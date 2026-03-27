import os
from datetime import datetime, timezone

import aiosqlite

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def init_db() -> None:
    os.makedirs(os.path.dirname(settings.database_path), exist_ok=True)
    async with aiosqlite.connect(settings.database_path) as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ten         TEXT NOT NULL,
                sdt         TEXT NOT NULL UNIQUE,
                dia_chi     TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                product_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                ten_sp      TEXT NOT NULL,
                mau         TEXT,
                size        TEXT,
                gia         REAL NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS orders (
                order_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ngay            TEXT NOT NULL,
                customer_id     INTEGER NOT NULL REFERENCES customers(customer_id),
                ten_sp          TEXT NOT NULL,
                mau             TEXT,
                size            TEXT,
                gia             REAL NOT NULL DEFAULT 0,
                so_luong        INTEGER NOT NULL DEFAULT 1,
                total           REAL GENERATED ALWAYS AS (so_luong * gia) STORED,
                phuong_thuc     TEXT NOT NULL DEFAULT 'cod' CHECK(phuong_thuc IN ('cod', 'chuyen_khoan')),
                luu_y           TEXT
            );

            CREATE VIEW IF NOT EXISTS monthly_revenue AS
            SELECT
                strftime('%Y', ngay) AS nam,
                strftime('%m', ngay) AS thang,
                COUNT(order_id)      AS so_don,
                SUM(total)           AS tong_doanh_thu
            FROM orders
            GROUP BY nam, thang
            ORDER BY nam DESC, thang DESC;

            CREATE TABLE IF NOT EXISTS conversations (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id       TEXT NOT NULL,
                raw_message     TEXT NOT NULL,
                classification  TEXT NOT NULL,
                intent          TEXT,
                response_text   TEXT NOT NULL,
                created_at      TEXT NOT NULL
            );
            """
        )
        await db.commit()
    logger.info("Database initialized | path=%s", settings.database_path)


async def lookup_product_price(ten_sp: str, mau: str | None, size: str | None) -> float | None:
    """Tìm giá sản phẩm trong bảng products. Trả về None nếu không tìm thấy."""
    async with aiosqlite.connect(settings.database_path) as db:
        # Tìm chính xác tên + màu + size
        async with db.execute(
            "SELECT gia FROM products WHERE LOWER(ten_sp) LIKE LOWER(?) AND LOWER(mau) = LOWER(?) AND LOWER(size) = LOWER(?) LIMIT 1",
            (f"%{ten_sp}%", mau or "", size or ""),
        ) as cursor:
            row = await cursor.fetchone()
        if row:
            return row[0]

        # Fallback: tìm theo tên + size
        async with db.execute(
            "SELECT gia FROM products WHERE LOWER(ten_sp) LIKE LOWER(?) AND LOWER(size) = LOWER(?) LIMIT 1",
            (f"%{ten_sp}%", size or ""),
        ) as cursor:
            row = await cursor.fetchone()
        if row:
            return row[0]

        # Fallback: tìm theo tên sản phẩm
        async with db.execute(
            "SELECT gia FROM products WHERE LOWER(ten_sp) LIKE LOWER(?) LIMIT 1",
            (f"%{ten_sp}%",),
        ) as cursor:
            row = await cursor.fetchone()
        if row:
            return row[0]

    return None


async def get_or_create_customer(ten: str, sdt: str, dia_chi: str) -> int:
    async with aiosqlite.connect(settings.database_path) as db:
        async with db.execute(
            "SELECT customer_id FROM customers WHERE sdt = ?", (sdt,)
        ) as cursor:
            row = await cursor.fetchone()

        if row:
            customer_id = row[0]
            await db.execute(
                "UPDATE customers SET ten = ?, dia_chi = ? WHERE customer_id = ?",
                (ten, dia_chi, customer_id),
            )
        else:
            async with db.execute(
                "INSERT INTO customers (ten, sdt, dia_chi) VALUES (?, ?, ?)",
                (ten, sdt, dia_chi),
            ) as cursor:
                customer_id = cursor.lastrowid

        await db.commit()
    logger.info("Customer upserted | customer_id=%s sdt=%s", customer_id, sdt)
    return customer_id


async def save_order(
    customer_id: int,
    ten_sp: str,
    mau: str | None,
    size: str | None,
    gia: float,
    so_luong: int,
    phuong_thuc: str,
    luu_y: str | None,
) -> int:
    ngay = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(settings.database_path) as db:
        async with db.execute(
            "INSERT INTO orders (ngay, customer_id, ten_sp, mau, size, gia, so_luong, phuong_thuc, luu_y) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ngay, customer_id, ten_sp, mau, size, gia, so_luong, phuong_thuc, luu_y),
        ) as cursor:
            order_id = cursor.lastrowid
        await db.commit()
    logger.info("Order saved | order_id=%s customer_id=%s ten_sp=%s", order_id, customer_id, ten_sp)
    return order_id


async def save_conversation(
    sender_id: str,
    raw_message: str,
    classification: str,
    intent: str | None,
    response_text: str,
) -> None:
    async with aiosqlite.connect(settings.database_path) as db:
        await db.execute(
            "INSERT INTO conversations (sender_id, raw_message, classification, intent, response_text, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                sender_id,
                raw_message,
                classification,
                intent,
                response_text,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        await db.commit()
    logger.info("Conversation saved | sender_id=%s classification=%s intent=%s", sender_id, classification, intent)
