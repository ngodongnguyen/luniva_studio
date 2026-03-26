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
