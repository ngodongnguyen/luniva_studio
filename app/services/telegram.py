import httpx

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def send_notification(text: str) -> None:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.debug("Telegram not configured, skipping notification")
        return

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10)
            if response.is_success:
                logger.info("Telegram notification sent")
            else:
                logger.error("Telegram error | status=%s body=%s", response.status_code, response.text)
    except Exception:
        logger.exception("Failed to send Telegram notification")
