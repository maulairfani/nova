"""One-off seed script: embeds the committed dummy MCN+ SOP markdown docs
directly into Qdrant, bypassing MinIO + Celery (phase 2 scope, TDD §6.5).

Idempotent — safe to re-run (deterministic point IDs, upsert not insert).

Usage: python -m seed.seed_qdrant
"""
import pathlib
import re
import uuid

from qdrant_client.models import PointStruct

from config import settings
from common.embeddings import EmbeddingClient
from common.qdrant_client import ensure_collection, get_client

DOCS_DIR = pathlib.Path(__file__).parent / "documents"
NAMESPACE = uuid.UUID("7a1d0c2b-7f7c-4f3f-ad3b-3a7b3a7b3a7b")  # fixed, for deterministic point IDs


def split_into_sections(text: str, source_document: str) -> list[dict]:
    """Split a markdown doc on '## ' headers. Each section becomes one chunk."""
    title_match = re.match(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else source_document

    sections = re.split(r"\n(?=##\s)", text)
    chunks = []
    for i, section in enumerate(sections):
        section = section.strip()
        if not section or section.startswith("# "):
            continue
        heading_match = re.match(r"^##\s+(.+)$", section)
        heading = heading_match.group(1).strip() if heading_match else title
        chunks.append(
            {
                "text": section,
                "title": title,
                "section_heading": heading,
                "chunk_index": i,
            }
        )
    return chunks


def seed() -> None:
    embedder = EmbeddingClient(api_key=settings.openrouter_api_key, model=settings.openrouter_embedding_model)
    client = get_client(settings.qdrant_url)
    ensure_collection(client, settings.qdrant_collection)

    points = []
    for doc_path in sorted(DOCS_DIR.glob("*.md")):
        text = doc_path.read_text(encoding="utf-8")
        chunks = split_into_sections(text, doc_path.name)
        vectors = embedder.embed([c["text"] for c in chunks])

        for chunk, vector in zip(chunks, vectors):
            point_id = str(uuid.uuid5(NAMESPACE, f"{doc_path.name}:{chunk['chunk_index']}"))
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "text": chunk["text"],
                        "source_document": doc_path.name,
                        "title": chunk["title"],
                        "section_heading": chunk["section_heading"],
                        "chunk_index": chunk["chunk_index"],
                    },
                )
            )
        print(f"{doc_path.name}: {len(chunks)} chunks")

    client.upsert(collection_name=settings.qdrant_collection, points=points)
    print(f"Upserted {len(points)} points into '{settings.qdrant_collection}'.")


if __name__ == "__main__":
    seed()
