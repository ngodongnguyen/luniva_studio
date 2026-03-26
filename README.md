# Facebook Messenger Webhook Service

Service Python/FastAPI nhận webhook từ Facebook Messenger, gọi chatbot backend, và gửi câu trả lời về cho người dùng.

---

## Cấu trúc project

```
fb-webhook-test/
├── app/
│   ├── main.py                    # FastAPI app entry point, middleware
│   ├── config.py                  # Cấu hình từ biến môi trường (pydantic-settings)
│   ├── routes/
│   │   └── webhook.py             # GET /webhook, POST /webhook, GET /health
│   ├── services/
│   │   ├── facebook_service.py    # Gửi tin nhắn qua Facebook Send API
│   │   └── chatbot_service.py     # Gọi chatbot backend, xử lý fallback
│   ├── schemas/
│   │   └── facebook.py            # Pydantic models cho webhook payload
│   └── utils/
│       └── logging.py             # Setup logging, RequestTimingMiddleware
├── .env.example
├── requirements.txt
└── README.md
```

---

## Cài dependencies

```bash
# Tạo conda environment với Python 3.11
conda create -n fb-webhook python=3.11 -y
conda activate fb-webhook

pip install -r requirements.txt
```

---

## Tạo file .env

```bash
cp .env.example .env
```

Điền các giá trị thực vào `.env`:

| Biến | Mô tả |
|------|-------|
| `APP_HOST` | Host chạy server, mặc định `0.0.0.0` |
| `APP_PORT` | Port chạy server, mặc định `8383` |
| `FB_VERIFY_TOKEN` | Token tự đặt để verify webhook với Facebook |
| `FB_PAGE_ACCESS_TOKEN` | Page Access Token lấy từ Meta Developer Portal |
| `FB_GRAPH_API_VERSION` | Phiên bản Graph API, ví dụ `v21.0` |
| `CHATBOT_API_URL` | URL endpoint chatbot backend nhận tin nhắn |
| `CHATBOT_API_TIMEOUT` | Timeout (giây) khi gọi chatbot, mặc định `10` |
| `LOG_LEVEL` | Mức log: `DEBUG`, `INFO`, `WARNING`, mặc định `INFO` |

---

## Chạy local

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8383 --reload
```

Server sẽ khởi động tại `http://localhost:8383`.

---

## Test GET /health

```bash
curl http://localhost:8383/health
```

Kết quả mong đợi:

```json
{"status": "ok", "service": "fb-webhook"}
```

---

## Expose webhook bằng ngrok

Facebook yêu cầu webhook URL phải là HTTPS public. Dùng ngrok để public local server:

**1. Cài ngrok:** https://ngrok.com/download

**2. Chạy ngrok:**

```bash
ngrok http 8383
```

Bạn sẽ thấy output dạng:

```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8383
```

**3. Webhook URL của bạn là:**

```
https://abc123.ngrok-free.app/webhook
```

> **Lưu ý:** URL ngrok thay đổi mỗi lần restart (trừ khi dùng gói trả phí). Mỗi lần restart ngrok cần cập nhật lại webhook URL trên Meta Developer Portal.

---

## Cấu hình webhook trên Meta Developer Portal

### Bước 1 — Tạo Meta Developer App

1. Vào [developers.facebook.com](https://developers.facebook.com) → đăng nhập bằng tài khoản Facebook
2. Click **My Apps** → **Create App**
3. Chọn use case → chọn **Other** → chọn loại app là **Business**
   > **Lưu ý:** Phải chọn **Business**, không chọn Consumer. Business app dùng hệ thống Access Level (Standard vs Advanced) thay vì Development/Live toggle.
4. Điền **App Display Name**, **Contact Email**, gắn Business Portfolio nếu có
5. Click **Create App**

---

### Bước 2 — Thêm Messenger Product

1. Trong App Dashboard, tìm mục **Add Products** ở sidebar
2. Tìm **Messenger** → click **Set Up**
3. Messenger Platform settings console sẽ xuất hiện ở sidebar trái

---

### Bước 3 — Kết nối Facebook Page với App

> Bạn phải là **Admin** của Facebook Page.

1. Trong Messenger settings, tìm mục **Access Tokens**
2. Click **Add or Remove Pages** → cấp quyền cho Page của bạn
3. Page sẽ xuất hiện trong danh sách

---

### Bước 4 — Lấy Page Access Token (Never-expiring)

1. Trong mục **Access Tokens**, click **Generate Token** bên cạnh Page của bạn
2. **Copy ngay lập tức** — UI sẽ không lưu lại, mỗi lần mở lại sẽ generate token mới
3. Paste vào file `.env`: `FB_PAGE_ACCESS_TOKEN=EAAxxxxxx...`
4. Xác nhận token không hết hạn tại [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/) — cột **Expires** phải hiện **Never**

> **Token bị invalidate khi:** admin thu hồi quyền app, đổi mật khẩu Facebook, hoặc app bị vô hiệu hóa.

---

### Bước 5 — Expose local server bằng ngrok (làm trước khi cấu hình webhook)

```bash
# Cài ngrok (macOS)
brew install ngrok

# Đăng ký tài khoản miễn phí tại ngrok.com, lấy authtoken
ngrok config add-authtoken <YOUR_AUTHTOKEN>

# Chạy server local
conda activate fb-webhook
uvicorn app.main:app --host 0.0.0.0 --port 8383 --reload

# Trong terminal khác, mở tunnel
ngrok http 8383
```

ngrok sẽ hiện:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8383
```

Dùng URL `https://` đó làm Callback URL. Inspect request realtime tại `http://localhost:4040`.

> **Lưu ý:** Free tier đổi URL mỗi lần restart ngrok → phải cập nhật lại Callback URL trên Meta mỗi lần.

---

### Bước 6 — Cấu hình Webhook Callback URL

1. Trong Messenger settings, tìm mục **Webhooks** → click **Setup Webhooks** (hoặc **Edit Callback URL**)
2. Điền:
   - **Callback URL:** `https://abc123.ngrok-free.app/webhook`
   - **Verify Token:** giá trị `FB_VERIFY_TOKEN` trong file `.env`
3. Click **Verify and Save**

**Điều gì xảy ra khi click Verify:** Facebook gọi:
```
GET /webhook?hub.mode=subscribe&hub.verify_token=...&hub.challenge=1234567890
```
Server trả về đúng chuỗi `hub.challenge` → verify thành công.

---

### Bước 7 — Subscribe Webhook Fields cho Page

1. Trong mục **Webhooks**, tìm phần **"Add subscriptions to your page"**
2. Chọn Page → click **Add Subscriptions**
3. Tick các field sau:

| Field | Bắt buộc | Mục đích |
|-------|----------|----------|
| `messages` | **Có** | Nhận tin nhắn text/media từ user |
| `messaging_postbacks` | **Có** | Nhận click button/quick reply |
| `messaging_optins` | Tùy chọn | Opt-in notification |
| `messaging_referrals` | Tùy chọn | m.me link, ads |
| `message_reads` | Tùy chọn | Xác nhận user đã đọc |

**Tối thiểu cần tick:** `messages` và `messaging_postbacks`.

---

### Bước 8 — Thêm Tester để test trước khi có Advanced Access

Trong Standard Access, bot **chỉ hoạt động** với tài khoản có role trong app:

1. App Dashboard → **App Roles** → **Roles**
2. Click **Add Tester** → nhập tên Facebook của người test
3. Người đó vào [developers.facebook.com](https://developers.facebook.com) → chấp nhận lời mời
4. Tài khoản đó nhắn tin vào Page → bot reply bình thường

---

### Bước 9 — Submit App Review để go live (Production)

Khi muốn tất cả người dùng đều dùng được bot:

1. App Dashboard → **App Review** → **Permissions and Features**
2. Request **Advanced Access** cho các quyền:

| Quyền | Mục đích |
|-------|---------|
| `pages_messaging` | Gửi/nhận tin nhắn Messenger |
| `pages_manage_metadata` | Subscribe webhook, quản lý page settings |
| `pages_read_engagement` | Đọc PSID, ảnh đại diện user |
| `pages_show_list` | Xem danh sách pages do user quản lý |

3. Chuẩn bị cho review:
   - Screencast demo luồng đăng nhập + chức năng bot end-to-end
   - Mô tả use case rõ ràng (customer support, e-commerce,...)
   - Page phải ở trạng thái **Published** (không phải draft)
   - Tuân thủ [Messenger Platform Policy](https://developers.facebook.com/docs/messenger-platform/policy) (quy tắc 24 giờ, opt-in,...)

---

### Các lỗi phổ biến cần tránh

| Vấn đề | Cách xử lý |
|--------|-----------|
| **Echo message loop** | Check `event.message.is_echo == True` và bỏ qua — code đã handle sẵn |
| **Timeout 5 giây** | Facebook cần nhận `200 OK` trong vòng 5 giây. Code trả `200` ngay, xử lý async sau |
| **Token bị mất** | Copy token ngay khi generate, UI không lưu lại |
| **Self-signed cert** | Phải dùng TLS hợp lệ — ngrok đã xử lý sẵn cho local |
| **PSID không phải global ID** | `sender.id` là Page-Scoped ID, chỉ dùng được với Page đó |
| **Webhook bị disable** | Nếu server down >1 tiếng Meta tắt webhook — phải vào re-enable thủ công |
| **URL ngrok thay đổi** | Mỗi lần restart ngrok phải cập nhật lại Callback URL trên Meta |

---

### Checklist tổng hợp

```
[ ] Tạo Business app trên Meta Developer Portal
[ ] Add Messenger product
[ ] Kết nối Facebook Page (phải là Admin)
[ ] Generate Page Access Token → copy ngay → lưu vào .env
[ ] Kiểm tra token tại Access Token Debugger → Expires = Never
[ ] Chạy server local + ngrok
[ ] Cấu hình Callback URL + Verify Token → Verify and Save
[ ] Subscribe webhook fields: messages, messaging_postbacks
[ ] Thêm Tester roles cho tài khoản test
[ ] Test end-to-end: nhắn tin vào Page → bot reply
[ ] Submit Advanced Access cho 4 permissions để go live
```

---

## Ví dụ verify webhook (manual)

Facebook sẽ gọi:

```
GET /webhook?hub.mode=subscribe&hub.verify_token=my_secret_verify_token&hub.challenge=1234567890
```

Service sẽ trả về chuỗi `1234567890` (giá trị challenge).

Bạn có thể test thủ công:

```bash
curl "http://localhost:8383/webhook?hub.mode=subscribe&hub.verify_token=my_secret_verify_token&hub.challenge=test_challenge_123"
```

---

## Ví dụ payload Facebook gửi vào POST /webhook

```json
{
  "object": "page",
  "entry": [
    {
      "id": "PAGE_ID",
      "time": 1705000000000,
      "messaging": [
        {
          "sender": {"id": "USER_PSID"},
          "recipient": {"id": "PAGE_ID"},
          "timestamp": 1705000000000,
          "message": {
            "mid": "m_abc123",
            "text": "Xin chào!"
          }
        }
      ]
    }
  ]
}
```

---

## Luồng xử lý

```
Facebook Messenger
      │
      ▼ POST /webhook
  Webhook Route
      │ parse payload
      ▼
  _handle_messaging_event
      │ lấy sender_id + text
      ▼
  chatbot_service.get_reply()
      │ POST {CHATBOT_API_URL}
      ▼
  facebook_service.send_message()
      │ POST graph.facebook.com/.../messages
      ▼
  Người dùng nhận tin nhắn
```

---

## Chuẩn API chatbot backend

Service này kỳ vọng chatbot backend của bạn nhận:

```
POST {CHATBOT_API_URL}
Content-Type: application/json

{
  "message": "nội dung tin nhắn",
  "user_id": "facebook_psid",
  "channel": "facebook_messenger"
}
```

Và trả về:

```json
{
  "answer": "Câu trả lời từ chatbot"
}
```

Nếu backend lỗi hoặc timeout, service sẽ tự động trả fallback:
> *"Xin lỗi, hiện tại hệ thống đang bận. Bạn vui lòng thử lại sau ít phút nhé."*

---

## Quyền Facebook cần có

Trong Meta Developer Portal, App cần các quyền sau:

| Quyền | Mục đích |
|-------|---------|
| `pages_messaging` | Gửi và nhận tin nhắn qua Messenger |
| `pages_read_engagement` | Đọc thông tin tương tác trên Page |

Để dùng app với người dùng ngoài nhóm test, cần submit app để Facebook review các quyền trên.

---

## Ghi chú

- Service luôn trả HTTP 200 cho Facebook dù có lỗi nội bộ, để tránh Facebook retry liên tục.
- Echo messages (tin nhắn do chính Page gửi đi) sẽ bị bỏ qua tự động.
- Retry tự động 1 lần cho lỗi timeout/connection khi gọi chatbot backend và Facebook Send API.
- Log được in ra stdout theo format: `YYYY-MM-DD HH:MM:SS | LEVEL | module | message`
