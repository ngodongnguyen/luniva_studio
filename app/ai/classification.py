import json

from app.ai.gemini import generate
from app.ai.prompt_template import CLASSIFICATION_PROMPT
from app.utils.logging import get_logger

logger = get_logger(__name__)

VALID = {"general", "indomain"}


async def classify(message: str) -> str:
    raw = await generate(CLASSIFICATION_PROMPT.format(message=message), temperature=0.1, max_tokens=64)

    try:
        result = json.loads(raw).get("classification", "general")
    except (json.JSONDecodeError, AttributeError):
        result = "indomain" if "indomain" in raw.lower() else "general"

    if result not in VALID:
        result = "general"

    logger.info("Classification: %s | message=%r", result, message[:80])
    return result
