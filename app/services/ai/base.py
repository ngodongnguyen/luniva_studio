import time

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


def with_retry(fn):
    """Shared retry decorator for all AI providers."""
    return retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        stop=stop_after_attempt(2),
        wait=wait_fixed(1),
        reraise=True,
    )(fn)


def log_response(provider: str, status_code: int, elapsed_ms: float) -> None:
    logger.info("%s responded | status=%s elapsed=%.1f ms", provider, status_code, elapsed_ms)


def timed_post():
    """Return (start_time) helper — call time.perf_counter()."""
    return time.perf_counter()
