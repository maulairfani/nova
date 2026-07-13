"""Celery task: download a document from MinIO, parse/chunk/embed it, write
the vectors to that business unit's Qdrant collection, and record the
result in nova_core's `documents` table (ADR-0022)."""
import logging
import uuid

from qdrant_client.models import PointStruct

from celery_app import celery_app
from config import settings
from db import insert_pending, mark_failed, mark_ingested
from embeddings import EmbeddingClient
from minio_client import download_object, get_client as get_minio_client
from parser import parse_document
from qdrant_helper import ensure_collection, get_client as get_qdrant_client

logger = logging.getLogger(__name__)

# Bucket/collection names, matching the business unit codes used
# throughout the codebase (mcp_client.py's _SERVER_TO_BUSINESS_UNIT, the
# X-Nova-Business-Units header, ADR-0021).
_BUCKETS = {"tv": "mcn-tv", "plus": "mcn-plus", "news": "mcn-news"}
_QDRANT_COLLECTIONS = {"tv": "mcn_tv", "plus": "mcn_plus", "news": "mcn_news"}

# Fixed per business unit (not random) so re-ingesting the same object key
# upserts the same points instead of creating duplicates.
_NAMESPACE = uuid.UUID("2f6a2f6a-9c2a-4e2e-6e6b-6f9c9b1a0001")


@celery_app.task(name="ingest_document", bind=True, max_retries=3, default_retry_delay=30)
def ingest_document(self, business_unit: str, object_key: str) -> None:
    if business_unit not in _BUCKETS:
        logger.error("Unknown business unit %r for object %r - skipping", business_unit, object_key)
        return

    guessed_format = "pdf" if object_key.lower().endswith(".pdf") else "markdown"
    # Inserted before any risky work (download/parse/embed) so a failure at
    # any stage still shows up in `documents` — not just failures after
    # parsing succeeded.
    document_id = insert_pending(business_unit, object_key, title=object_key, format_=guessed_format)
    try:
        minio = get_minio_client()
        content = download_object(minio, _BUCKETS[business_unit], object_key)
        title, chunks, format_ = parse_document(content, object_key)
        if not chunks:
            raise ValueError("No chunks extracted from document")

        embedder = EmbeddingClient(api_key=settings.openrouter_api_key, model=settings.openrouter_embedding_model)
        vectors = embedder.embed([c["text"] for c in chunks])

        qdrant = get_qdrant_client(settings.qdrant_url)
        collection = _QDRANT_COLLECTIONS[business_unit]
        ensure_collection(qdrant, collection)

        points = [
            PointStruct(
                id=str(uuid.uuid5(_NAMESPACE, f"{business_unit}:{object_key}:{chunk['chunk_index']}")),
                vector=vector,
                payload={
                    "text": chunk["text"],
                    "source_document": object_key,
                    "title": title,
                    "section_heading": chunk.get("section_heading"),
                    "chunk_index": chunk["chunk_index"],
                },
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        qdrant.upsert(collection_name=collection, points=points)

        mark_ingested(document_id, title, len(points))
        logger.info("Ingested %s/%s into %s: %d chunks", business_unit, object_key, collection, len(points))
    except Exception as exc:
        mark_failed(document_id, str(exc))
        logger.exception("Ingestion failed for %s/%s", business_unit, object_key)
        raise
