import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.schemas.facebook import HealthResponse, WebhookPayload
from app.services.ai import get_reply
from app.services.facebook_service import send_message
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def extract_text(event_message: Any) -> str | None:
    """Safely extract text from a messaging event's message field."""
    if event_message is None:
        return None
    # Guard against echo messages (messages sent by the page itself)
    if getattr(event_message, "is_echo", False):
        return None
    text = getattr(event_message, "text", None)
    if not text or not text.strip():
        return None
    return text.strip()


# ---------------------------------------------------------------------------
# GET /webhook  –  Facebook verification handshake
# ---------------------------------------------------------------------------

@router.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
) -> str:
    logger.info(
        "Webhook verification request | mode=%s token_match=%s",
        hub_mode,
        hub_verify_token == settings.fb_verify_token,
    )

    if hub_mode != "subscribe":
        raise HTTPException(status_code=400, detail="hub.mode phải là 'subscribe'")

    if hub_verify_token != settings.fb_verify_token:
        logger.warning("Webhook verification failed: token mismatch")
        raise HTTPException(status_code=403, detail="Verify token không hợp lệ")

    logger.info("Webhook verified successfully")
    return hub_challenge


# ---------------------------------------------------------------------------
# POST /webhook  –  Receive messages from Facebook
# ---------------------------------------------------------------------------

@router.post("/webhook", status_code=200)
async def receive_webhook(request: Request) -> dict:
    try:
        raw_body = await request.json()
    except Exception:
        logger.exception("Failed to parse webhook JSON body")
        # Always return 200 to Facebook so it doesn't retry with the same bad payload
        return {"status": "invalid_payload"}

    logger.info("Webhook received | object=%s", raw_body.get("object"))

    try:
        payload = WebhookPayload.model_validate(raw_body)
    except Exception:
        logger.exception("Failed to validate webhook payload")
        return {"status": "invalid_payload"}

    if payload.object != "page":
        logger.debug("Ignoring non-page webhook object: %s", payload.object)
        return {"status": "ignored"}

    # Return 200 immediately, process events in background
    # Facebook requires response within 5 seconds
    for entry in payload.entry:
        for event in entry.messaging:
            asyncio.create_task(_handle_messaging_event(event))

    return {"status": "ok"}


async def _handle_messaging_event(event: Any) -> None:
    sender_id: str = event.sender.id

    try:
        text = extract_text(event.message)

        if text is None:
            logger.debug("Skipping non-text or echo event | sender_id=%s", sender_id)
            return

        logger.info("Received message | sender_id=%s text=%r", sender_id, text)

        reply = await get_reply(user_id=sender_id, message=text)
        await send_message(recipient_id=sender_id, text=reply)

    except Exception:
        logger.exception("Unhandled error processing event | sender_id=%s", sender_id)


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse()
