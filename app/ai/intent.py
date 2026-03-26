import json

from app.ai.gemini import generate
from app.utils.logging import get_logger

logger = get_logger(__name__)

PROMPT = """Xác định intent của tin nhắn sau:
- "tu_van": hỏi về sản phẩm, dịch vụ, giá cả, tính năng
- "bao_hanh": bảo hành, lỗi sản phẩm, đổi trả, khiếu nại
- "dat_hang": muốn mua, đặt hàng, thanh toán, mua ngay

Tin nhắn: "{message}"

Chỉ trả về JSON: {{"intent": "tu_van"}} hoặc {{"intent": "bao_hanh"}} hoặc {{"intent": "dat_hang"}}"""

VALID = {"tu_van", "bao_hanh", "dat_hang"}


async def detect_intent(message: str) -> str:
    raw = await generate(PROMPT.format(message=message), temperature=0.1, max_tokens=64)

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
