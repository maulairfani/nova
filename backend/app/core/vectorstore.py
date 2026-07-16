"""Qdrant connection for the Manage Documents delete endpoint - deleting a
document must also remove its points from the vector store, or Nova would
keep citing "deleted" content (worker/qdrant_helper.py duplicated the same
way, see ADR-0022's Alternatives Considered)."""
from qdrant_client import QdrantClient

from app.core.config import settings

COLLECTIONS = {"tv": "mcn_tv", "plus": "mcn_plus", "news": "mcn_news"}


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)
