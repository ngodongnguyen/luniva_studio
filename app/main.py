from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.routes.webhook import router as webhook_router
from app.utils.logging import RequestTimingMiddleware, get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Service starting | host=%s port=%s log_level=%s",
        settings.app_host,
        settings.app_port,
        settings.log_level,
    )
    yield
    logger.info("Service shutting down")


app = FastAPI(
    title="Facebook Messenger Webhook",
    description="Tích hợp Facebook Messenger với chatbot backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestTimingMiddleware)
app.include_router(webhook_router)
