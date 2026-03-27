import json

from app.ai.llm import generate
from app.ai.history import format_history
from app.ai.prompt_template import CONFIRM_ORDER_PROMPT, DAT_HANG_EXTRACT_PROMPT
from app.db.engine import get_or_create_customer, lookup_product_price, save_order
from app.services.telegram import send_notification
from app.utils.logging import get_logger

logger = get_logger(__name__)

# State: lưu đơn hàng đang chờ confirm { sender_id: order_info }
_pending_orders: dict[str, dict] = {}

REQUIRED_FIELDS = {
    "ten": "tên người nhận",
    "sdt": "số điện thoại",
    "dia_chi": "địa chỉ giao hàng",
    "ten_sp": "tên sản phẩm",
    "so_luong": "số lượng",
    "phuong_thuc": "phương thức thanh toán (COD hay chuyển khoản)",
}

PAYMENT_LABELS = {
    "cod": "COD (thanh toán khi nhận hàng)",
    "chuyen_khoan": "Chuyển khoản",
}


async def _extract(message: str, history: list[dict]) -> dict:
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


async def _is_confirmed(message: str) -> bool:
    raw = await generate(
        CONFIRM_ORDER_PROMPT.format(message=message),
        temperature=0.1,
        max_tokens=32,
    )
    try:
        return json.loads(raw).get("confirmed", False)
    except (json.JSONDecodeError, AttributeError):
        return False


def _order_summary(info: dict, gia: float) -> str:
    total = (info.get("so_luong") or 1) * gia
    payment_label = PAYMENT_LABELS.get(info.get("phuong_thuc", ""), info.get("phuong_thuc", ""))
    luu_y = info.get("luu_y") or "Không có"

    lines = [
        f"📋 Xác nhận đơn hàng:",
        f"• Tên: {info['ten']}",
        f"• SĐT: {info['sdt']}",
        f"• Địa chỉ: {info['dia_chi']}",
        f"• Sản phẩm: {info['ten_sp']}"
        + (f" | Màu: {info['mau']}" if info.get("mau") else "")
        + (f" | Size: {info['size']}" if info.get("size") else ""),
        f"• Số lượng: {info.get('so_luong') or 1}",
        f"• Đơn giá: {gia:,.0f}đ",
        f"• Tổng tiền: {total:,.0f}đ",
        f"• Thanh toán: {payment_label}",
        f"• Lưu ý: {luu_y}",
    ]
    return "\n".join(lines)


async def handle(message: str, sender_id: str, history: list[dict]) -> str:
    # Khách đang có đơn chờ confirm
    if sender_id in _pending_orders:
        confirmed = await _is_confirmed(message)
        if confirmed:
            info = _pending_orders.pop(sender_id)
            gia = info.pop("_gia", 0)

            customer_id = await get_or_create_customer(
                ten=info["ten"], sdt=info["sdt"], dia_chi=info["dia_chi"],
            )
            await save_order(
                customer_id=customer_id,
                ten_sp=info["ten_sp"],
                mau=info.get("mau"),
                size=info.get("size"),
                gia=gia,
                so_luong=info.get("so_luong") or 1,
                phuong_thuc=info["phuong_thuc"],
                luu_y=info.get("luu_y"),
            )

            total = (info.get("so_luong") or 1) * gia
            payment_label = PAYMENT_LABELS.get(info["phuong_thuc"], info["phuong_thuc"])
            luu_y = info.get("luu_y") or "Không có"

            await send_notification(
                f"🛒 <b>Đơn hàng mới</b>\n"
                f"👤 Sender: <code>{sender_id}</code>\n"
                f"🙍 Tên: {info['ten']} | 📞 {info['sdt']}\n"
                f"📍 Địa chỉ: {info['dia_chi']}\n"
                f"👟 SP: {info['ten_sp']}"
                + (f" | Màu: {info['mau']}" if info.get("mau") else "")
                + (f" | Size: {info['size']}" if info.get("size") else "")
                + f"\n📦 SL: {info.get('so_luong') or 1} | Tổng: {total:,.0f}đ\n"
                f"💳 {payment_label} | 📝 {luu_y}"
            )

            return (
                f"Đơn hàng của bạn đã được xác nhận rồi ạ 🎉 "
                f"Nhân viên sẽ liên hệ lại sớm nhất nhé! 💕"
            )
        else:
            _pending_orders.pop(sender_id)
            return "Dạ, em đã hủy đơn hàng rồi ạ. Bạn cần em hỗ trợ gì thêm không? 😊"

    # Khách muốn gặp tư vấn viên
    info = await _extract(message, history)

    if info.get("muon_gap_tu_van"):
        await send_notification(
            f"🙋 <b>Khách muốn gặp tư vấn viên</b>\n"
            f"👤 Sender: <code>{sender_id}</code>\n"
            f"💬 Tin nhắn: {message}"
        )
        return "Xin vui lòng đợi trong ít phút, tư vấn viên sẽ liên hệ lại với bạn ngay nhé! 🥰"

    # Kiểm tra thông tin còn thiếu
    missing = [label for field, label in REQUIRED_FIELDS.items() if not info.get(field)]
    if missing:
        missing_text = ", ".join(missing)
        return (
            f"Cảm ơn bạn đã quan tâm đến sản phẩm bên em! 🥰 "
            f"Để xử lý đơn hàng, bạn cho em xin thêm: **{missing_text}** nhé!"
        )

    # Lookup giá từ bảng products
    gia = await lookup_product_price(info["ten_sp"], info.get("mau"), info.get("size")) or 0

    # Lưu pending và hỏi confirm
    info["_gia"] = gia
    _pending_orders[sender_id] = info

    gia_text = f"{gia:,.0f}đ" if gia > 0 else "chưa có giá (nhân viên sẽ xác nhận)"
    summary = _order_summary({**info, "so_luong": info.get("so_luong") or 1}, gia)

    return (
        f"{summary}\n"
        f"{'• Đơn giá: ' + gia_text if gia == 0 else ''}\n\n"
        f"Bạn xác nhận đặt hàng không ạ? 😊"
    ).strip()
