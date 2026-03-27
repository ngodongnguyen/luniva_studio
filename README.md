# Luniva Studio — Facebook Messenger Chatbot

Chatbot tự động cho shop giày nữ **Luniva Studio**, tích hợp Facebook Messenger. Tự động phân loại tin nhắn, tư vấn sản phẩm, xử lý đơn hàng, hỗ trợ bảo hành và gửi thông báo qua Telegram.

---

## Cấu trúc project

```
├── app/
│   ├── main.py                        # FastAPI entry point, khởi tạo DB + VectorDB
│   ├── config.py                      # Cấu hình từ .env (pydantic-settings)
│   ├── routes/
│   │   ├── webhook.py                 # GET/POST /webhook, GET /health
│   │   └── test_chat.py               # POST /test/chat (test pipeline qua API)
│   ├── ai/
│   │   ├── pipeline.py                # Điều phối toàn bộ luồng xử lý tin nhắn
│   │   ├── classification.py          # Phân loại: general / indomain
│   │   ├── intent.py                  # Xác định intent: tu_van / bao_hanh / dat_hang
│   │   ├── llm.py                     # Unified generate(), route sang Gemini hoặc OpenAI
│   │   ├── gemini.py                  # Gemini API client (httpx + retry)
│   │   ├── openai_client.py           # OpenAI API client (httpx + retry)
│   │   ├── history.py                 # In-memory conversation history (5 turns/user)
│   │   ├── prompt_template.py         # Tất cả prompt tập trung tại đây
│   │   └── handlers/
│   │       ├── general.py             # Trả lời chào hỏi, hội thoại thông thường
│   │       ├── tu_van.py              # Tư vấn sản phẩm qua Vector DB + AI
│   │       ├── bao_hanh.py            # Hỗ trợ bảo hành/đổi trả + notify Telegram
│   │       └── dat_hang.py            # Xử lý đặt hàng: thu thập info → confirm → lưu DB
│   ├── db/
│   │   └── engine.py                  # SQLite: customers, products, orders, conversations
│   ├── vectordb/
│   │   └── store.py                   # ChromaDB local: load + search tài liệu tư vấn
│   ├── services/
│   │   ├── facebook.py                # Gửi tin nhắn qua Facebook Send API
│   │   └── telegram.py                # Gửi thông báo nội bộ qua Telegram Bot
│   ├── schemas/
│   │   └── facebook.py                # Pydantic models cho Facebook webhook payload
│   └── utils/
│       └── logging.py                 # Setup logging, RequestTimingMiddleware
├── data/
│   ├── tu_van_docs.json               # Tài liệu tư vấn sản phẩm (load vào ChromaDB)
│   └── bao_hanh_qa.json               # Q&A bảo hành/đổi trả
├── test.py                            # Script test chatbot qua terminal
├── .env.example
└── requirements.txt
```

---

## Luồng xử lý tin nhắn

```
Facebook Messenger
      │ POST /webhook
      ▼
  webhook.py  ──── trả 200 ngay, xử lý async
      │
      ▼
  pipeline.py
      │
      ├── get_history(sender_id)         ← lấy 5 tin nhắn gần nhất từ RAM
      │
      ├── classify(message, history)
      │       ├── "general"  → general.handle()    ← chào hỏi, hội thoại thông thường
      │       └── "indomain" → detect_intent()
      │                           ├── "tu_van"    → tu_van.handle()
      │                           ├── "bao_hanh"  → bao_hanh.handle()
      │                           └── "dat_hang"  → dat_hang.handle()
      │
      ├── add_turn(sender_id, message, response)   ← cập nhật history
      ├── save_conversation(...)                   ← lưu vào SQLite
      │
      ▼
  facebook.py  ──── gửi response về Messenger
```

---

## Luồng đặt hàng (dat_hang handler)

```
Khách nhắn muốn mua
      │
      ├── Extract thông tin từ message + history
      │       Fields: tên, SĐT, địa chỉ, tên SP, màu, size, số lượng, phương thức TT
      │
      ├── Nếu thiếu field → hỏi lại
      │
      ├── Nếu đủ → lookup giá từ bảng products
      │
      ├── Hiển thị order summary → hỏi confirm
      │
      └── Khách xác nhận
              ├── OK  → get_or_create_customer() → save_order() → notify Telegram
              └── Hủy → xóa pending, không lưu
```

---

## Database schema

```sql
-- Khách hàng (upsert theo SĐT)
customers (customer_id PK, ten, sdt UNIQUE, dia_chi)

-- Danh mục sản phẩm (staff tự thêm)
products (product_id PK, ten_sp, mau, size, gia)

-- Đơn hàng
orders (
    order_id PK, ngay, customer_id FK,
    ten_sp, mau, size, gia, so_luong,
    total GENERATED AS (so_luong * gia),
    phuong_thuc CHECK('cod' | 'chuyen_khoan'),
    luu_y
)

-- Doanh thu theo tháng (VIEW tự tính từ orders)
monthly_revenue (nam, thang, so_don, tong_doanh_thu)

-- Lịch sử hội thoại
conversations (id PK, sender_id, raw_message, classification, intent, response_text, created_at)
```

Xem dữ liệu:
```bash
sqlite3 data/conversations.db "SELECT * FROM monthly_revenue;"
```
Hoặc dùng **DBeaver** / **TablePlus** → connect SQLite → chọn file `data/conversations.db`.

---

## Cài đặt

```bash
conda create -n luniva python=3.11 -y
conda activate luniva
pip install -r requirements.txt
```

---

## Cấu hình .env

```bash
cp .env.example .env
```

| Biến | Mô tả | Bắt buộc |
|------|-------|----------|
| `FB_VERIFY_TOKEN` | Token tự đặt để verify webhook | Có |
| `FB_PAGE_ACCESS_TOKEN` | Page Access Token từ Meta Developer Portal | Có |
| `AI_PROVIDER` | `gemini` hoặc `openai` | Có |
| `GEMINI_API_KEY` | Google Gemini API key | Nếu dùng Gemini |
| `GEMINI_MODEL` | Model Gemini, ví dụ `gemini-2.0-flash`, `gemma-3-27b-it` | Nếu dùng Gemini |
| `OPENAI_API_KEY` | OpenAI API key | Nếu dùng OpenAI |
| `OPENAI_MODEL` | Model OpenAI, ví dụ `gpt-4o-mini` | Nếu dùng OpenAI |
| `TELEGRAM_BOT_TOKEN` | Token Telegram bot để nhận thông báo đơn hàng | Không (optional) |
| `TELEGRAM_CHAT_ID` | Chat ID nhận thông báo Telegram | Không (optional) |
| `DATABASE_PATH` | Đường dẫn SQLite, mặc định `data/conversations.db` | Không |
| `VECTOR_DB_PATH` | Đường dẫn ChromaDB, mặc định `data/vectordb` | Không |
| `AI_TIMEOUT` | Timeout gọi AI API (giây), mặc định `30` | Không |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING`, mặc định `INFO` | Không |

**Switch AI provider** chỉ cần đổi trong `.env`:
```env
AI_PROVIDER=openai   # hoặc gemini
```

---

## Chạy app

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8383 --reload
```

Khi khởi động app sẽ tự động:
- Tạo các bảng SQLite nếu chưa có
- Load tài liệu từ `data/tu_van_docs.json` vào ChromaDB (chỉ lần đầu)

---

## Test chatbot

**Terminal interactive:**
```bash
python test.py
```

```
Luniva Studio Chatbot Test — gõ 'exit' để thoát

Bạn: giày cao gót size 37 có không?
[indomain] intent=tu_van
Bot: ...
```

**Swagger UI:**
```
http://localhost:8383/docs
```
Vào `POST /test/chat` → nhập `sender_id` và `message`.

**curl:**
```bash
curl -X POST http://localhost:8383/test/chat \
  -H "Content-Type: application/json" \
  -d '{"sender_id": "user_001", "message": "giày boots đen size 37 giá bao nhiêu?"}'
```

---

## Cập nhật dữ liệu tư vấn

Sửa file `data/tu_van_docs.json`:
```json
[
  {
    "title": "Tên tài liệu",
    "content": "Nội dung..."
  }
]
```

Sau đó xóa vectordb để load lại:
```bash
rm -rf data/vectordb
# restart app
```

---

## Expose webhook bằng ngrok

```bash
ngrok http 8383
# → https://abc123.ngrok-free.app
```

Webhook URL: `https://abc123.ngrok-free.app/webhook`

> URL thay đổi mỗi lần restart ngrok (free tier) → cần cập nhật lại trên Meta Developer Portal.

---

## Cấu hình webhook trên Meta Developer Portal

1. Vào [developers.facebook.com](https://developers.facebook.com) → **My Apps** → **Create App** → chọn **Business**
2. Add product **Messenger** → **Set Up**
3. **Access Tokens** → kết nối Facebook Page → **Generate Token** → copy vào `FB_PAGE_ACCESS_TOKEN`
4. **Webhooks** → **Setup Webhooks**:
   - Callback URL: `https://xxx.ngrok-free.app/webhook`
   - Verify Token: giá trị `FB_VERIFY_TOKEN` trong `.env`
5. Subscribe fields: tick `messages` và `messaging_postbacks`
6. **App Roles** → **Add Tester** → thêm tài khoản test

> Bot chỉ hoạt động với Tester trong Standard Access. Submit App Review để go live toàn bộ người dùng.

---

## Quyền Facebook cần có

| Quyền | Mục đích |
|-------|---------|
| `pages_messaging` | Gửi/nhận tin nhắn Messenger |
| `pages_manage_metadata` | Subscribe webhook |
| `pages_read_engagement` | Đọc PSID người dùng |

---

## Lưu ý

- App luôn trả HTTP 200 cho Facebook ngay lập tức, xử lý tin nhắn async để tránh timeout 5 giây.
- Echo messages (Page tự gửi) bị bỏ qua tự động.
- Conversation history lưu trên RAM, mất khi restart app — đây là thiết kế cố ý cho stateless deployment.
- Telegram notification là optional — nếu không điền token/chat_id thì tự động skip.
