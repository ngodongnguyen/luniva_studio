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
        "stream": False,
    }

    start = time.perf_counter()
    response = await client.post(
        f"{settings.ollama_base_url}/api/chat",
        json=payload,
        timeout=settings.ai_timeout,
    )
    log_response("Ollama", response.status_code, (time.perf_counter() - start) * 1000)

    response.raise_for_status()
    data = response.json()
    return data.get("message", {}).get("content", "").strip()
