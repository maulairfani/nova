"""KB Search Tool — embeds the query, searches mcp-tv's Qdrant collection."""
from common.embeddings import EmbeddingClient
from common.qdrant_client import get_client

from config import settings

_embedder = EmbeddingClient(api_key=settings.openrouter_api_key, model=settings.openrouter_embedding_model)
_qdrant = get_client(settings.qdrant_url)


async def kb_search(query: str, top_k: int = 5) -> list[dict]:
    """Search MCN TV's knowledge base (SOPs, internal documentation) for chunks
    relevant to `query`. Returns matching chunks with source metadata."""
    vector = _embedder.embed_one(query)
    hits = _qdrant.query_points(
        collection_name=settings.qdrant_collection,
        query=vector,
        limit=top_k,
    ).points

    return [
        {
            "text": hit.payload["text"],
            "source_document": hit.payload["source_document"],
            "title": hit.payload["title"],
            "section_heading": hit.payload["section_heading"],
            "score": hit.score,
        }
        for hit in hits
    ]
