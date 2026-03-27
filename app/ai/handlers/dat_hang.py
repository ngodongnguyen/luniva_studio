import json

from app.ai.llm import generate
from app.ai.history import format_history
from app.ai.prompt_template import DAT_HANG_EXTRACT_PROMPT
from app.db.engine import get_or_create_customer, save_order
from app.services.telegram import send_notification
from app.utils.logging import get_logger

logger = get_logger(__name__)

REQUIRED_CUSTOMER = {"ten": "tên người nhận", "sdt": "số điện thoại", "dia_chi": "địa chỉ giao hàng"}
REQUIRED_ORDER = {"ten_sp": "tên sản phẩm", "phuong_thuc": "phương thức thanh toán (COD hay chuyển khoản)"}

PAYMENT_LABELS = {"cod": "COD (thanh toán khi nhận hàng)", "chuyen_khoan": "Chuyển khoản"}


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
    all_required = {**REQUIRED_CUSTOMER, **REQUIRED_ORDER}
    missing = [label for field, label in all_required.items() if not info.get(field)]

    if missing:
        missing_text = ", ".join(missing)
        return (
            f"Cảm ơn bạn đã quan tâm đến sản phẩm bên em! 🥰 "
            f"Để xử lý đơn hàng nhanh nhất, bạn cho em xin thêm: "
            f"**{missing_text}** nhé!"
        )

    # Đủ thông tin → lưu DB và notify Telegram
    customer_id = await get_or_create_customer(
        ten=info["ten"],
        sdt=info["sdt"],
        dia_chi=info["dia_chi"],
    )
    await save_order(
        customer_id=customer_id,
        ten_sp=info["ten_sp"],
        mau=info.get("mau"),
        size=info.get("size"),
        gia=0,  # staff cập nhật giá sau
        so_luong=info.get("so_luong") or 1,
        phuong_thuc=info["phuong_thuc"],
        luu_y=info.get("luu_y"),
    )

    payment_label = PAYMENT_LABELS.get(info["phuong_thuc"], info["phuong_thuc"])
    luu_y = info.get("luu_y") or "Không có"

    await send_notification(
        f"🛒 <b>Đơn hàng mới</b>\n"
        f"👤 Sender: <code>{sender_id}</code>\n"
        f"🙍 Tên: {info['ten']}\n"
        f"📞 SĐT: {info['sdt']}\n"
        f"📍 Địa chỉ: {info['dia_chi']}\n"
        f"👟 Sản phẩm: {info['ten_sp']}"
        + (f" | Màu: {info['mau']}" if info.get("mau") else "")
        + (f" | Size: {info['size']}" if info.get("size") else "")
        + f"\n📦 Số lượng: {info.get('so_luong') or 1}\n"
        f"💳 Thanh toán: {payment_label}\n"
        f"📝 Lưu ý: {luu_y}"
    )

    return (
        f"Tuyệt vời! Em đã ghi nhận đơn hàng của bạn rồi ạ 🎉\n"
        f"📋 Thông tin đơn hàng:\n"
        f"• Tên: {info['ten']}\n"
        f"• SĐT: {info['sdt']}\n"
        f"• Địa chỉ: {info['dia_chi']}\n"
        f"• Sản phẩm: {info['ten_sp']}"
        + (f" | Màu: {info['mau']}" if info.get("mau") else "")
        + (f" | Size: {info['size']}" if info.get("size") else "")
        + f"\n• Số lượng: {info.get('so_luong') or 1}\n"
        f"• Thanh toán: {payment_label}\n"
        f"• Lưu ý: {luu_y}\n\n"
        f"Nhân viên sẽ liên hệ xác nhận lại với bạn sớm nhất nhé! 💕"
    )
