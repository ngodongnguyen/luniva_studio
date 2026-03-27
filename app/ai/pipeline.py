from dataclasses import dataclass

from app.ai.classification import classify
from app.ai.handlers import bao_hanh, dat_hang, general, tu_van
from app.ai.history import add_turn, get_history
from app.ai.intent import detect_intent
from app.db.engine import save_conversation
from app.utils.logging import get_logger

logger = get_logger(__name__)

FALLBACK = (
    "Xin lỗi, hiện tại hệ thống đang bận. "
    "Bạn vui lòng thử lại sau ít phút nhé."
)

_INTENT_HANDLERS = {
    "tu_van": tu_van.handle,
    "bao_hanh": bao_hanh.handle,
    "dat_hang": dat_hang.handle,
}


@dataclass
class PipelineResult:
    classification: str
    intent: str | None
    response: str


async def process(sender_id: str, message: str) -> PipelineResult:
    classification = "general"
    intent = None
    response = FALLBACK
    history = get_history(sender_id)

    try:
        classification = await classify(message, history)

        if classification == "general":
            response = await general.handle(message, sender_id, history)
        else:
            intent = await detect_intent(message, history)
            handler = _INTENT_HANDLERS.get(intent, tu_van.handle)
            response = await handler(message, sender_id, history)

        if not response:
            response = FALLBACK

    except Exception:
        logger.exception("Pipeline error | sender_id=%s", sender_id)
        response = FALLBACK

    add_turn(sender_id, message, response)
    await save_conversation(sender_id, message, classification, intent, response)

    logger.info(
        "Pipeline done | sender=%s classification=%s intent=%s response_len=%d",
        sender_id, classification, intent, len(response),
    )

    return PipelineResult(classification=classification, intent=intent, response=response)
