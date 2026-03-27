import os
from datetime import datetime, timezone

import aiosqlite

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def init_db() -> None:
    os.makedirs(os.path.dirname(settings.database_path), exist_ok=True)
    async with aiosqlite.connect(settings.database_path) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT NOT NULL,
                raw_message TEXT NOT NULL,
                classification TEXT NOT NULL,
                intent TEXT,
                response_text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT NOT NULL,
                ten TEXT NOT NULL,
                sdt TEXT NOT NULL,
                dia_chi TEXT NOT NULL,
                luu_y TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        await db.commit()
    logger.info("Database initialized | path=%s", settings.database_path)


async def save_conversation(
    sender_id: str,
    raw_message: str,
    classification: str,
    intent: str | None,
    response_text: str,
) -> None:
    async with aiosqlite.connect(settings.database_path) as db:
        await db.execute(
            "INSERT INTO conversations "
            "(sender_id, raw_message, classification, intent, response_text, created_at) "
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


async def save_order(
    sender_id: str,
    ten: str,
    sdt: str,
    dia_chi: str,
    luu_y: str | None,
) -> None:
    async with aiosqlite.connect(settings.database_path) as db:
        await db.execute(
            "INSERT INTO orders (sender_id, ten, sdt, dia_chi, luu_y, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (sender_id, ten, sdt, dia_chi, luu_y, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()
    logger.info("Order saved | sender_id=%s ten=%s sdt=%s", sender_id, ten, sdt)
