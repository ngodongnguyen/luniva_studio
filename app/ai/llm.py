from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def generate(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    provider = settings.ai_provider.lower()

    if provider == "openai":
        from app.ai.openai_client import generate as _generate
    else:
        from app.ai.gemini import generate as _generate

    logger.debug("LLM provider: %s", provider)
    return await _generate(prompt, system_prompt=system_prompt, temperature=temperature, max_tokens=max_tokens)
