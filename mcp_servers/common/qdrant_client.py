"""Shared Qdrant connection helper - query-time only. Collection creation
is worker/'s job now (tasks.py's ensure_collection, on first real
ingestion) since the old seed_qdrant.py scripts that used to own it here
were retired (see mcp_servers/tv/CLAUDE.md)."""
from qdrant_client import QdrantClient


def get_client(url: str) -> QdrantClient:
    return QdrantClient(url=url)
