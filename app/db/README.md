# app/db — Database (SQLite)

Lưu lịch sử hội thoại vào SQLite để theo dõi và phân tích.

## `engine.py`

### Schema

```sql
CREATE TABLE conversations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id       TEXT NOT NULL,      -- Facebook PSID của người dùng
    raw_message     TEXT NOT NULL,      -- Tin nhắn gốc
    classification  TEXT NOT NULL,      -- "general" | "indomain"
    intent          TEXT,               -- "tu_van" | "bao_hanh" | "dat_hang" | NULL
    response_text   TEXT NOT NULL,      -- Câu trả lời đã gửi
    created_at      TEXT NOT NULL       -- ISO 8601 UTC timestamp
)
```

### Hàm

**`init_db()`** — Tạo bảng nếu chưa tồn tại. Được gọi khi app khởi động.

**`save_conversation(...)`** — Lưu một lượt hội thoại sau khi pipeline xử lý xong.

## Cấu hình

```
DATABASE_PATH=data/conversations.db   # mặc định
```

## Xem dữ liệu

```bash
sqlite3 data/conversations.db "SELECT * FROM conversations ORDER BY id DESC LIMIT 20;"
```
