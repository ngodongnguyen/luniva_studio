# app/services — External Services

Các service giao tiếp với bên ngoài: Facebook Messenger API và Telegram Bot API.

## `facebook.py`

Gửi tin nhắn văn bản tới người dùng qua Facebook Send API.

```python
await send_message(recipient_id="<PSID>", text="Nội dung tin nhắn")
```

- Dùng `httpx.AsyncClient`
- Retry tự động tối đa 2 lần khi timeout/connect error
- Log lỗi nếu Facebook trả về status không thành công

**Cần cấu hình:**
```
FB_PAGE_ACCESS_TOKEN=...
FB_GRAPH_API_VERSION=v21.0   # mặc định
```

---

## `telegram.py`

Gửi thông báo nội bộ tới Telegram bot khi có yêu cầu bảo hành hoặc đặt hàng.

```python
await send_notification("🔧 <b>Yêu cầu bảo hành</b>\n...")
```

- Hỗ trợ HTML parse mode
- Tự bỏ qua nếu chưa cấu hình token/chat_id (không raise lỗi)

**Cần cấu hình:**
```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

Nếu không điền 2 biến này, Telegram sẽ bị skip hoàn toàn.
