"""Manage Documents business logic - business-unit access control plus
orchestrating the Document row (nova_core) alongside MinIO/Qdrant, the
same infrastructure worker/'s real ingestion pipeline uses (ADR-0022).
app/api/v1/endpoints/documents.py stays a thin HTTP adapter around this."""
import io
import re
import uuid

from fastapi import HTTPException
from minio.error import S3Error
from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.core.db import async_session
from app.core.storage import BUCKETS, get_minio_client
from app.core.vectorstore import COLLECTIONS, get_qdrant_client
from app.models import Document
from app.repositories import document_repository

_REAL_UNITS = ["tv", "plus", "news"]
_FORMAT_BY_EXTENSION = {".md": "markdown", ".markdown": "markdown", ".pdf": "pdf"}
_CONTENT_TYPE_BY_FORMAT = {"markdown": "text/markdown; charset=utf-8", "pdf": "application/pdf"}


def _business_unit_roles(claims: dict) -> dict[str, str]:
    return {m["code"]: m["role"] for m in claims.get("business_units", [])}


def _is_group_admin(claims: dict) -> bool:
    return _business_unit_roles(claims).get("group") == "admin"


def _accessible_units(claims: dict) -> list[str]:
    """Which units' documents the caller may *view* - mirrors
    mcp_client.py's get_tools_for_identity scoping: group_admin sees
    every unit, everyone else only their own claimed unit(s). A "group"
    membership alone (no admin tier) grants no unit's documents, same as
    it grants no unit's MCP tools today."""
    if _is_group_admin(claims):
        return list(_REAL_UNITS)
    roles = _business_unit_roles(claims)
    return [u for u in _REAL_UNITS if u in roles]


def _can_manage(unit_code: str, claims: dict) -> bool:
    """Which units' documents the caller may upload/delete - unit admins
    manage only their own unit, group_admin manages every unit."""
    if _is_group_admin(claims):
        return True
    return _business_unit_roles(claims).get(unit_code) == "admin"


def _require_view(unit_code: str, claims: dict) -> None:
    if unit_code not in _REAL_UNITS or unit_code not in _accessible_units(claims):
        raise HTTPException(status_code=403, detail="You don't have access to this business unit's documents.")


def _require_manage(unit_code: str, claims: dict) -> None:
    if unit_code not in _REAL_UNITS or not _can_manage(unit_code, claims):
        raise HTTPException(status_code=403, detail="You don't have permission to manage this business unit's documents.")


async def list_documents(business_unit: str, claims: dict) -> list[Document]:
    _require_view(business_unit, claims)
    async with async_session() as session:
        return await document_repository.list_by_unit(session, business_unit)


async def find_by_source(business_unit: str, object_key: str, claims: dict) -> Document:
    """Resolves a kb_search citation (Sources panel, frontend) back to the
    real Document row so it can be opened via the same preview flow
    Manage Documents already uses - a document that's since been deleted
    (or was never real, e.g. seed content ingested outside this table)
    just 404s, same as get_document_content does today."""
    _require_view(business_unit, claims)
    async with async_session() as session:
        document = await document_repository.get_by_unit_and_object_key(session, business_unit, object_key)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found.")
        return document


async def get_document_content(document_id: uuid.UUID, claims: dict):
    """Returns (byte_stream, content_type) for the document's raw content,
    read straight from MinIO. Raises HTTPException on not-found/forbidden."""
    async with async_session() as session:
        document = await document_repository.get(session, document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found.")
        _require_view(document.business_unit_code, claims)
        object_key = document.object_key
        business_unit = document.business_unit_code
        content_type = _CONTENT_TYPE_BY_FORMAT[document.format]

    minio = get_minio_client()
    try:
        response = minio.get_object(BUCKETS[business_unit], object_key)
    except S3Error:
        raise HTTPException(status_code=404, detail="Document content not found in storage.")

    def stream():
        try:
            yield from response.stream(32 * 1024)
        finally:
            response.close()
            response.release_conn()

    return stream(), content_type


async def upload_document(business_unit: str, title: str, filename: str, content: bytes, claims: dict) -> Document:
    _require_manage(business_unit, claims)

    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    format_ = _FORMAT_BY_EXTENSION.get(extension)
    if format_ is None:
        raise HTTPException(status_code=400, detail="Only Markdown (.md) and PDF (.pdf) files are supported.")

    safe_filename = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    object_key = f"{uuid.uuid4()}-{safe_filename}"
    resolved_title = title.strip() or filename

    async with async_session() as session:
        document = await document_repository.create(
            session, business_unit_code=business_unit, object_key=object_key, title=resolved_title, format=format_
        )

    # Written after the row commits: if the upload fails partway, the row
    # is still visible as "pending" rather than lost, and worker's own
    # insert_pending get-or-create will just find this row once the
    # object does land (or an admin can delete the stuck pending row and
    # retry).
    minio = get_minio_client()
    minio.put_object(BUCKETS[business_unit], object_key, io.BytesIO(content), length=len(content))

    return document


async def delete_document(document_id: uuid.UUID, claims: dict) -> None:
    async with async_session() as session:
        document = await document_repository.get(session, document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found.")
        _require_manage(document.business_unit_code, claims)

        object_key = document.object_key
        business_unit = document.business_unit_code
        await document_repository.delete(session, document)

    qdrant = get_qdrant_client()
    collection = COLLECTIONS[business_unit]
    if qdrant.collection_exists(collection):
        qdrant.delete(
            collection_name=collection,
            points_selector=Filter(must=[FieldCondition(key="source_document", match=MatchValue(value=object_key))]),
        )

    minio = get_minio_client()
    minio.remove_object(BUCKETS[business_unit], object_key)
