from app.ai.gemini import generate
from app.config import settings


async def handle(message: str, sender_id: str) -> str:
    return await generate(message, system_prompt=settings.ai_system_prompt)
