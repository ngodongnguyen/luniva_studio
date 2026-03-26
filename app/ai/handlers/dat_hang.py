from app.services.telegram import send_notification

RESPONSE = (
    "Cảm ơn bạn đã quan tâm! "
    "Chúng tôi đã ghi nhận yêu cầu đặt hàng của bạn. "
    "Nhân viên sẽ liên hệ lại trong thời gian sớm nhất nhé."
)


async def handle(message: str, sender_id: str) -> str:
    await send_notification(
        f"🛒 <b>Yêu cầu đặt hàng</b>\n"
        f"👤 Sender: <code>{sender_id}</code>\n"
        f"💬 Message: {message}"
    )
    return RESPONSE
