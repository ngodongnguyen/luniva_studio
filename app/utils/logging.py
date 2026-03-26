import logging
import sys
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


def setup_logging() -> None:
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format=log_format,
        datefmt=date_format,
        stream=sys.stdout,
    )

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Log method, path, status code, and elapsed time for every request."""

    def __init__(self, app, logger: logging.Logger | None = None) -> None:
        super().__init__(app)
        self._logger = logger or get_logger("request")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        self._logger.info(
            "%s %s → %s (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
