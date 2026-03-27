# app/vectordb — Vector Database

Lưu trữ và tìm kiếm tài liệu tư vấn bằng ChromaDB (local persistent).

## `store.py`

### Khởi tạo

Được gọi tự động khi app start (`load_documents()`). Đọc file `data/tu_van_docs.json` và nạp vào ChromaDB nếu collection còn trống.

```json
// Cấu trúc data/tu_van_docs.json
[
  {
    "title": "Tên tài liệu",
    "content": "Nội dung tài liệu..."
  }
]
```

### Tìm kiếm

```python
docs = search_documents(query="câu hỏi của khách", n_results=3)
# Trả về list[str] — nội dung các tài liệu liên quan nhất
```

Handler `tu_van` gọi hàm này để lấy context trước khi gửi cho Gemini.

## Cấu hình

```
VECTOR_DB_PATH=data/vectordb   # mặc định
```

ChromaDB lưu dữ liệu tại thư mục này, persist qua các lần restart.

## Thêm tài liệu mới

Chỉnh sửa file `data/tu_van_docs.json`, sau đó **xóa thư mục `data/vectordb`** để ChromaDB load lại từ đầu khi restart app.
