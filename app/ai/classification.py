import json

from app.ai.gemini import generate
from app.utils.logging import get_logger

logger = get_logger(__name__)

PROMPT = """Phân loại tin nhắn sau vào MỘT trong hai nhóm:
- "general": chào hỏi, tán gẫu, câu hỏi chung chung, không liên quan sản phẩm/dịch vụ
- "indomain": liên quan sản phẩm, dịch vụ, tư vấn, bảo hành, đặt hàng, giá cả

Tin nhắn: "{message}"

Chỉ trả về JSON: {{"classification": "general"}} hoặc {{"classification": "indomain"}}"""

VALID = {"general", "indomain"}


async def classify(message: str) -> str:
    raw = await generate(PROMPT.format(message=message), temperature=0.1, max_tokens=64)

    try:
        result = json.loads(raw).get("classification", "general")
    except (json.JSONDecodeError, AttributeError):
        result = "indomain" if "indomain" in raw.lower() else "general"

    if result not in VALID:
        result = "general"

    logger.info("Classification: %s | message=%r", result, message[:80])
    return result
