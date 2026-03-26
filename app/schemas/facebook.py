from typing import Any

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Incoming webhook payload from Facebook
# ---------------------------------------------------------------------------

class MessagePayload(BaseModel):
    mid: str | None = None
    text: str | None = None


class SenderPayload(BaseModel):
    id: str


class RecipientPayload(BaseModel):
    id: str


class MessagingEvent(BaseModel):
    sender: SenderPayload
    recipient: RecipientPayload
    timestamp: int | None = None
    message: MessagePayload | None = None

    # Echo messages sent by the page itself include this field
    # We use it to detect and skip echoes
    @property
    def is_echo(self) -> bool:
        return self.message is not None and getattr(self.message, "is_echo", False)


class Entry(BaseModel):
    id: str
    time: int | None = None
    messaging: list[MessagingEvent] = []


class WebhookPayload(BaseModel):
    object: str
    entry: list[Entry] = []


# ---------------------------------------------------------------------------
# Health response
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "fb-webhook"
