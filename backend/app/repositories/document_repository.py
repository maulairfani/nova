"""Data access for the Document model (ingestion pipeline metadata,
ADR-0022). No MinIO/Qdrant/authorization logic here - that's
app/services/document_service.py."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document


async def list_by_unit(session: AsyncSession, business_unit: str) -> list[Document]:
    return (
        (
            await session.execute(
                select(Document).where(Document.business_unit_code == business_unit).order_by(Document.created_at.desc())
            )
        )
        .scalars()
        .all()
    )


async def get(session: AsyncSession, document_id: uuid.UUID) -> Document | None:
    return await session.get(Document, document_id)


async def get_by_unit_and_object_key(session: AsyncSession, business_unit_code: str, object_key: str) -> Document | None:
    """Resolves a kb_search citation's (unit, source_document) pair back to
    its Document row - exact match is correct and unambiguous regardless
    of which ingestion path produced the row (Manage Documents' upload
    UUID-prefixes object_key; worker/seed_documents.py's direct-MinIO path
    doesn't), since a Qdrant chunk's source_document payload field is
    always set to the exact object_key that triggered its ingestion
    (worker/tasks.py), and (business_unit_code, object_key) is unique."""
    return (
        await session.execute(
            select(Document).where(Document.business_unit_code == business_unit_code, Document.object_key == object_key)
        )
    ).scalar_one_or_none()


async def create(
    session: AsyncSession, *, business_unit_code: str, object_key: str, title: str, format: str
) -> Document:
    document = Document(
        business_unit_code=business_unit_code,
        object_key=object_key,
        title=title,
        format=format,
        status="pending",
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return document


async def delete(session: AsyncSession, document: Document) -> None:
    await session.delete(document)
    await session.commit()
