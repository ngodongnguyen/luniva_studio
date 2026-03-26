import json
import os
from pathlib import Path

import chromadb

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None


def _get_collection() -> chromadb.Collection:
    global _client, _collection
    if _collection is None:
        os.makedirs(settings.vector_db_path, exist_ok=True)
        _client = chromadb.PersistentClient(path=settings.vector_db_path)
        _collection = _client.get_or_create_collection(name="tu_van_docs")
    return _collection


def load_documents() -> None:
    collection = _get_collection()
    if collection.count() > 0:
        logger.info("Vector DB already has %d documents, skipping load", collection.count())
        return

    path = Path("data/tu_van_docs.json")
    if not path.exists():
        logger.warning("data/tu_van_docs.json not found, vector DB is empty")
        return

    docs = json.loads(path.read_text(encoding="utf-8"))
    if not docs:
        return

    collection.add(
        documents=[d["content"] for d in docs],
        ids=[f"doc_{i}" for i in range(len(docs))],
        metadatas=[{"title": d.get("title", "")} for d in docs],
    )
    logger.info("Loaded %d documents into vector DB", len(docs))


def search_documents(query: str, n_results: int = 3) -> list[str]:
    collection = _get_collection()
    if collection.count() == 0:
        return []

    results = collection.query(query_texts=[query], n_results=min(n_results, collection.count()))
    return results["documents"][0] if results["documents"] else []
