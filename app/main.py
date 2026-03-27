from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db.engine import init_db
from app.routes.test_chat import router as test_router
from app.routes.webhook import router as webhook_router
from app.utils.logging import RequestTimingMiddleware, get_logger, setup_logging
from app.vectordb.store import load_documents

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting | host=%s port=%s model=%s",
        settings.app_host, settings.app_port, settings.gemini_model,
    )
    await init_db()
    load_documents()
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Luniva Messenger Bot",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestTimingMiddleware)
app.include_router(webhook_router)
app.include_router(test_router)
