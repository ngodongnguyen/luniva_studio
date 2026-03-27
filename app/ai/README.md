# app/ai — AI Pipeline

Module xử lý toàn bộ logic AI: phân loại tin nhắn, xác định intent, và điều phối handler phù hợp.

## Luồng xử lý

```
Tin nhắn đến
    │
    ▼
classify()          ← classification.py
    │
    ├── "general"   → general.handle()
    │
    └── "indomain"  → detect_intent()     ← intent.py
                            │
                            ├── "tu_van"   → tu_van.handle()
                            ├── "bao_hanh" → bao_hanh.handle()
                            └── "dat_hang" → dat_hang.handle()
```

## Các file

### `pipeline.py`
Điều phối trung tâm. Gọi `classify()` → `detect_intent()` → handler tương ứng → lưu conversation vào DB.

Trả về `PipelineResult(classification, intent, response)`.

### `classification.py`
Phân loại tin nhắn vào 2 nhóm:
- `general`: chào hỏi, tán gẫu, câu hỏi chung
- `indomain`: liên quan sản phẩm/dịch vụ của Luniva Studio

Dùng Gemini với `temperature=0.1`, parse JSON response.

### `intent.py`
Xác định intent cho tin nhắn `indomain`:
- `tu_van`: hỏi về sản phẩm, giá cả, tính năng
- `bao_hanh`: bảo hành, lỗi, đổi trả
- `dat_hang`: muốn mua, đặt hàng

Dùng Gemini với `temperature=0.1`, parse JSON response.

### `gemini.py`
Wrapper gọi Gemini API (Google Generative Language). Hỗ trợ:
- System prompt (tự động embed vào user message nếu dùng model Gemma)
- Retry tự động khi timeout/connect error (tối đa 2 lần)
- Cấu hình `temperature` và `max_tokens`

## handlers/

| File | Mô tả |
|------|-------|
| `general.py` | Trả lời tự do bằng Gemini với system prompt mặc định |
| `tu_van.py` | Tìm tài liệu liên quan trong Vector DB → đưa vào context cho Gemini |
| `bao_hanh.py` | Trả lời dựa trên Q&A file JSON + gửi thông báo Telegram |
| `dat_hang.py` | Gửi thông báo Telegram + trả lời cố định cho khách |
