"""Qdrant connection helper — a deliberate small duplicate of
mcp_servers/common/qdrant_client.py (see ADR-0022's Alternatives Considered)."""
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, VectorParams

# text-embedding-3-small (ADR-0015) output dimension
EMBEDDING_DIM = 1536


def get_client(url: str) -> QdrantClient:
    return QdrantClient(url=url)


def ensure_collection(client: QdrantClient, collection_name: str) -> None:
    """Called by every ingestion task for that unit (tasks.py), not just
    the first one - `collection_exists` then `create_collection` isn't
    atomic, so two tasks for the same not-yet-created collection racing
    (Celery's default prefork concurrency, e.g. a seed script enqueueing
    several documents for one unit at once) can both see "doesn't exist"
    and both try to create it. Qdrant correctly rejects the loser with a
    409, which is exactly the outcome ensure_collection wants (the
    collection exists) - not a real failure, so it's swallowed here
    instead of crashing that task."""
    if client.collection_exists(collection_name):
        return
    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
    except UnexpectedResponse as exc:
        if exc.status_code != 409:
            raise
