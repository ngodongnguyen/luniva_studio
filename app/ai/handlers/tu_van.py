from app.ai.gemini import generate
from app.ai.history import format_history
from app.ai.prompt_template import TU_VAN_SYSTEM_PROMPT
from app.utils.logging import get_logger
from app.vectordb.store import search_documents

logger = get_logger(__name__)


async def handle(message: str, sender_id: str, history: list[dict]) -> str:
    docs = search_documents(message, n_results=3)
    context = "\n---\n".join(docs) if docs else "Không có thông tin tham khảo."
    history_block = f"Lịch sử hội thoại:\n{format_history(history)}\n\n" if history else ""
    system = TU_VAN_SYSTEM_PROMPT.format(context=context, history_block=history_block)
    logger.info("tu_van handler | docs_found=%d sender_id=%s", len(docs), sender_id)
    return await generate(message, system_prompt=system)
