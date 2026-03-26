import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.ai.pipeline import process
from app.config import settings
from app.schemas.facebook import HealthResponse, WebhookPayload
from app.services.facebook import send_message
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def extract_text(event_message: Any) -> str | None:
    if event_message is None:
        return None
    if getattr(event_message, "is_echo", False):
        return None
    text = getattr(event_message, "text", None)
    if not text or not text.strip():
        return None
    return text.strip()


@router.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
) -> str:
    logger.info(
        "Webhook verification | mode=%s token_match=%s",
        hub_mode, hub_verify_token == settings.fb_verify_token,
    )

    if hub_mode != "subscribe":
        raise HTTPException(status_code=400, detail="hub.mode phải là 'subscribe'")

    if hub_verify_token != settings.fb_verify_token:
        logger.warning("Webhook verification failed: token mismatch")
        raise HTTPException(status_code=403, detail="Verify token không hợp lệ")

    logger.info("Webhook verified successfully")
    return hub_challenge


@router.post("/webhook", status_code=200)
async def receive_webhook(request: Request) -> dict:
    try:
        raw_body = await request.json()
    except Exception:
        logger.exception("Failed to parse webhook JSON body")
        return {"status": "invalid_payload"}

    logger.info("Webhook received | object=%s", raw_body.get("object"))

    try:
        payload = WebhookPayload.model_validate(raw_body)
    except Exception:
        logger.exception("Failed to validate webhook payload")
        return {"status": "invalid_payload"}

    if payload.object != "page":
        return {"status": "ignored"}

    for entry in payload.entry:
        for event in entry.messaging:
            asyncio.create_task(_handle_messaging_event(event))

    return {"status": "ok"}


async def _handle_messaging_event(event: Any) -> None:
    sender_id: str = event.sender.id

    try:
        text = extract_text(event.message)
        if text is None:
            logger.debug("Skipping non-text event | sender_id=%s", sender_id)
            return

        logger.info("Received message | sender_id=%s text=%r", sender_id, text)

        result = await process(sender_id=sender_id, message=text)
        await send_message(recipient_id=sender_id, text=result.response)

    except Exception:
        logger.exception("Error processing event | sender_id=%s", sender_id)


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse()
