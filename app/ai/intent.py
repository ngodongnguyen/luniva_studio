import json

from app.ai.llm import generate
from app.ai.history import format_history
from app.ai.prompt_template import INTENT_PROMPT
from app.utils.logging import get_logger

logger = get_logger(__name__)

VALID = {"tu_van", "bao_hanh", "dat_hang"}


async def detect_intent(message: str, history: list[dict]) -> str:
    history_block = f"Lịch sử hội thoại:\n{format_history(history)}\n\n" if history else ""
    raw = await generate(
        INTENT_PROMPT.format(message=message, history_block=history_block),
        temperature=0.1,
        max_tokens=64,
    )

    try:
        result = json.loads(raw).get("intent", "tu_van")
    except (json.JSONDecodeError, AttributeError):
        lower = raw.lower()
        if "bao_hanh" in lower:
            result = "bao_hanh"
        elif "dat_hang" in lower:
            result = "dat_hang"
        else:
            result = "tu_van"

    if result not in VALID:
        result = "tu_van"

    logger.info("Intent: %s | message=%r", result, message[:80])
    return result
