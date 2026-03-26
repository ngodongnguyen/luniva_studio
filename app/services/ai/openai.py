import time

import httpx

from app.config import settings
from app.services.ai.base import log_response, with_retry


@with_retry
async def call(client: httpx.AsyncClient, message: str) -> str:
    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": settings.ai_system_prompt},
            {"role": "user", "content": message},
        ],
    }

    start = time.perf_counter()
    response = await client.post(
        f"{settings.openai_base_url}/chat/completions",
        json=payload,
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        timeout=settings.ai_timeout,
    )
    log_response("OpenAI", response.status_code, (time.perf_counter() - start) * 1000)

    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()
