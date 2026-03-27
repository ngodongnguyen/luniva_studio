from app.ai.gemini import generate
from app.ai.prompt_template import GENERAL_SYSTEM_PROMPT


async def handle(message: str, sender_id: str, _history: list[dict]) -> str:
    return await generate(message, system_prompt=GENERAL_SYSTEM_PROMPT)
