from app.ai.gemini import generate
from app.ai.prompt_template import TU_VAN_SYSTEM_PROMPT
from app.utils.logging import get_logger
from app.vectordb.store import search_documents

logger = get_logger(__name__)


async def handle(message: str, sender_id: str) -> str:
    docs = search_documents(message, n_results=3)
    context = "\n---\n".join(docs) if docs else "Không có thông tin tham khảo."
    system = TU_VAN_SYSTEM_PROMPT.format(context=context)
    logger.info("tu_van handler | docs_found=%d sender_id=%s", len(docs), sender_id)
    return await generate(message, system_prompt=system)
