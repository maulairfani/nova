"""Shared Qdrant connection helper."""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# text-embedding-3-small (ADR-0015) output dimension
EMBEDDING_DIM = 1536


def get_client(url: str) -> QdrantClient:
    return QdrantClient(url=url)


def ensure_collection(client: QdrantClient, collection_name: str) -> None:
    """Idempotent collection creation — the seed script owns this (TDD §5.2),
    not the MCP server at query time."""
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
