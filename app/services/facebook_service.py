import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


@retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    stop=stop_after_attempt(2),
    wait=wait_fixed(1),
    reraise=True,
)
async def _post_message(client: httpx.AsyncClient, recipient_id: str, text: str) -> None:
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
    }
    params = {"access_token": settings.fb_page_access_token}

    response = await client.post(
        settings.fb_messages_url,
        json=payload,
        params=params,
        timeout=10,
    )

    if not response.is_success:
        logger.error(
            "Facebook Send API error | recipient_id=%s status=%s body=%s",
            recipient_id,
            response.status_code,
            response.text,
        )
        response.raise_for_status()


async def send_message(recipient_id: str, text: str) -> None:
    """
    Send a text message to a Facebook Messenger user.
    Logs success or failure without propagating exceptions to the caller.
    """
    logger.info("Sending message to Facebook | recipient_id=%s", recipient_id)

    try:
        async with httpx.AsyncClient() as client:
            await _post_message(client, recipient_id, text)
        logger.info("Message sent successfully | recipient_id=%s", recipient_id)

    except Exception:
        logger.exception(
            "Failed to send message via Facebook Send API | recipient_id=%s", recipient_id
        )
