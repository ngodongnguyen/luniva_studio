from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.pipeline import process

router = APIRouter(prefix="/test", tags=["test"])


class ChatRequest(BaseModel):
    sender_id: str = "test_user"
    message: str


class ChatResponse(BaseModel):
    sender_id: str
    message: str
    classification: str
    intent: str | None
    response: str


@router.post("/chat", response_model=ChatResponse)
async def test_chat(body: ChatRequest) -> ChatResponse:
    result = await process(sender_id=body.sender_id, message=body.message)
    return ChatResponse(
        sender_id=body.sender_id,
        message=body.message,
        classification=result.classification,
        intent=result.intent,
        response=result.response,
    )
