import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


@retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    stop=stop_after_attempt(2),
    wait=wait_fixed(1),
    reraise=True,
)
async def generate(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    model = settings.gemini_model
    url = f"{BASE_URL}/{model}:generateContent?key={settings.gemini_api_key}"

    user_text = prompt
    if system_prompt and model.startswith("gemma"):
        user_text = f"[Hướng dẫn: {system_prompt}]\n\n{prompt}"
        system_prompt = ""

    payload: dict = {
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }

    if system_prompt:
        payload["system_instruction"] = {"parts": [{"text": system_prompt}]}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=settings.ai_timeout)
        response.raise_for_status()

    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        block_reason = data.get("promptFeedback", {}).get("blockReason", "unknown")
        logger.warning("Gemini blocked response | reason=%s", block_reason)
        return ""

    return candidates[0]["content"]["parts"][0]["text"].strip()
