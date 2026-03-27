import json

from app.ai.gemini import generate
from app.ai.history import format_history
from app.ai.prompt_template import CLASSIFICATION_PROMPT
from app.utils.logging import get_logger

logger = get_logger(__name__)

VALID = {"general", "indomain"}


async def classify(message: str, history: list[dict]) -> str:
    history_block = f"Lịch sử hội thoại:\n{format_history(history)}\n\n" if history else ""
    raw = await generate(
        CLASSIFICATION_PROMPT.format(message=message, history_block=history_block),
        temperature=0.1,
        max_tokens=64,
    )

    try:
        result = json.loads(raw).get("classification", "general")
    except (json.JSONDecodeError, AttributeError):
        result = "indomain" if "indomain" in raw.lower() else "general"

    if result not in VALID:
        result = "general"

    logger.info("Classification: %s | message=%r", result, message[:80])
    return result
