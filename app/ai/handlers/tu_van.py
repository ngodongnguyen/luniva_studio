from app.ai.gemini import generate
from app.vectordb.store import search_documents
from app.utils.logging import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "Bạn là tư vấn viên của Luniva Studio. "
    "Dựa vào thông tin tham khảo bên dưới để trả lời khách hàng. "
    "Trả lời ngắn gọn, chính xác, bằng tiếng Việt. "
    "Nếu không có thông tin phù hợp, hãy nói rằng bạn sẽ chuyển cho bộ phận tư vấn.\n\n"
    "Thông tin tham khảo:\n{context}"
)


async def handle(message: str, sender_id: str) -> str:
    docs = search_documents(message, n_results=3)
    context = "\n---\n".join(docs) if docs else "Không có thông tin tham khảo."
    system = SYSTEM_PROMPT.format(context=context)
    logger.info("tu_van handler | docs_found=%d sender_id=%s", len(docs), sender_id)
    return await generate(message, system_prompt=system)
