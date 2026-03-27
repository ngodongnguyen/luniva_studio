import json

from app.ai.llm import generate
from app.ai.history import format_history
from app.ai.prompt_template import DAT_HANG_EXTRACT_PROMPT
from app.db.engine import save_order
from app.services.telegram import send_notification
from app.utils.logging import get_logger

logger = get_logger(__name__)

MISSING_MESSAGES = {
    "ten": "tên người nhận",
    "sdt": "số điện thoại",
    "dia_chi": "địa chỉ giao hàng",
}


async def _extract_order_info(message: str, history: list[dict]) -> dict:
    history_block = f"Lịch sử hội thoại:\n{format_history(history)}\n\n" if history else ""
    raw = await generate(
        DAT_HANG_EXTRACT_PROMPT.format(message=message, history_block=history_block),
        temperature=0.1,
        max_tokens=256,
    )
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, AttributeError):
        return {}


async def handle(message: str, sender_id: str, history: list[dict]) -> str:
    info = await _extract_order_info(message, history)

    # Khách muốn gặp tư vấn viên
    if info.get("muon_gap_tu_van"):
        await send_notification(
            f"🙋 <b>Khách muốn gặp tư vấn viên</b>\n"
            f"👤 Sender: <code>{sender_id}</code>\n"
            f"💬 Tin nhắn: {message}"
        )
        return "Xin vui lòng đợi trong ít phút, tư vấn viên sẽ liên hệ lại với bạn ngay nhé! 🥰"

    # Kiểm tra thông tin còn thiếu
    missing = [label for field, label in MISSING_MESSAGES.items() if not info.get(field)]

    if missing:
        missing_text = ", ".join(missing)
        return (
            f"Cảm ơn bạn đã quan tâm đến sản phẩm bên em! 🥰 "
            f"Để xử lý đơn hàng nhanh nhất, bạn cho em xin thêm: "
            f"**{missing_text}** nhé!"
        )

    # Đủ thông tin → lưu DB, notify Telegram và xác nhận
    luu_y = info.get("luu_y") or "Không có"
    await save_order(
        sender_id=sender_id,
        ten=info["ten"],
        sdt=info["sdt"],
        dia_chi=info["dia_chi"],
        luu_y=info.get("luu_y"),
    )
    await send_notification(
        f"🛒 <b>Đơn hàng mới</b>\n"
        f"👤 Sender: <code>{sender_id}</code>\n"
        f"🙍 Tên: {info['ten']}\n"
        f"📞 SĐT: {info['sdt']}\n"
        f"📍 Địa chỉ: {info['dia_chi']}\n"
        f"📝 Lưu ý: {luu_y}"
    )

    return (
        f"Tuyệt vời! Em đã ghi nhận đơn hàng của bạn rồi ạ 🎉\n"
        f"📋 Thông tin đơn hàng:\n"
        f"• Tên: {info['ten']}\n"
        f"• SĐT: {info['sdt']}\n"
        f"• Địa chỉ: {info['dia_chi']}\n"
        f"• Lưu ý: {luu_y}\n\n"
        f"Nhân viên sẽ liên hệ xác nhận lại với bạn trong thời gian sớm nhất nhé! 💕"
    )
