import httpx

from app.config import settings
from app.services.ai import gemini, ollama, openai
from app.utils.logging import get_logger

logger = get_logger(__name__)

FALLBACK_MESSAGE = (
    "Xin lỗi, hiện tại hệ thống đang bận. "
    "Bạn vui lòng thử lại sau ít phút nhé."
)

_PROVIDERS = {
    "ollama": ollama.call,
    "openai": openai.call,
    "gemini": gemini.call,
}


async def get_reply(user_id: str, message: str) -> str:
    """Fetch reply from configured AI provider. Fallback on any error."""
    provider = settings.ai_provider.lower()
    call_fn = _PROVIDERS.get(provider)

    if call_fn is None:
        logger.error("Unknown AI_PROVIDER=%r, using fallback", provider)
        return FALLBACK_MESSAGE

    logger.info(
        "Calling %s | model=%s user_id=%s message=%r",
        provider, settings.ai_model, user_id, message,
    )

    try:
        async with httpx.AsyncClient() as client:
            answer = await call_fn(client, message)

        if not answer:
            logger.warning("Empty answer from %s, using fallback | user_id=%s", provider, user_id)
            return FALLBACK_MESSAGE

        return answer

    except Exception:
        logger.exception("%s error | user_id=%s", provider, user_id)
        return FALLBACK_MESSAGE
