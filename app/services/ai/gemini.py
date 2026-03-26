import time

import httpx

from app.config import settings
from app.services.ai.base import log_response, with_retry


@with_retry
async def call(client: httpx.AsyncClient, message: str) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{settings.ai_model}"
        f":generateContent?key={settings.gemini_api_key}"
    )
    user_message = f"[Hướng dẫn: {settings.ai_system_prompt}]\n\n{message}"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": user_message}]},
        ],
    }

    # Gemini-native models support system_instruction, Gemma does not
    if not settings.ai_model.startswith("gemma"):
        payload["system_instruction"] = {
            "parts": [{"text": settings.ai_system_prompt}],
        }
        payload["contents"][0]["parts"][0]["text"] = message

    start = time.perf_counter()
    response = await client.post(url, json=payload, timeout=settings.ai_timeout)
    log_response("Gemini", response.status_code, (time.perf_counter() - start) * 1000)

    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
