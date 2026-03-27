import json
from pathlib import Path

from app.ai.gemini import generate
from app.ai.prompt_template import BAO_HANH_SYSTEM_PROMPT
from app.services.telegram import send_notification
from app.utils.logging import get_logger

logger = get_logger(__name__)

_qa_data: list[dict] = []


def _load_qa() -> None:
    global _qa_data
    path = Path("data/bao_hanh_qa.json")
    if path.exists():
        _qa_data = json.loads(path.read_text(encoding="utf-8"))
        logger.info("Loaded %d bao_hanh Q&A pairs", len(_qa_data))


async def handle(message: str, sender_id: str) -> str:
    if not _qa_data:
        _load_qa()

    qa_text = "\n".join(
        f"Q: {item['question']}\nA: {item['answer']}" for item in _qa_data
    )
    system = BAO_HANH_SYSTEM_PROMPT.format(qa_text=qa_text or "Chưa có dữ liệu Q&A.")
    response = await generate(message, system_prompt=system)

    await send_notification(
        f"🔧 <b>Yêu cầu bảo hành</b>\n"
        f"👤 Sender: <code>{sender_id}</code>\n"
        f"💬 Message: {message}"
    )

    return response
