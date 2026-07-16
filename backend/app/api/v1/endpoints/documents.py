"""Manage Documents Endpoint - list/upload/delete the knowledge base
source files each business unit's MCP server retrieves from (kb_search).

Real product decision, not a UI-only feature: uploading here writes
straight to the same MinIO bucket the real ingestion pipeline already
watches (ADR-0022) - a webhook fires, worker/ downloads, parses, embeds,
and upserts into Qdrant exactly as it would for a file uploaded any other
way. This endpoint never talks to Qdrant to *add* anything; it only
deletes from it, since removing a document must also stop Nova from
citing it."""
import io
import re
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sqlalchemy import select

from app.api.v1.deps import get_current_claims
from app.core.db import async_session
from app.core.storage import BUCKETS, get_minio_client
from app.core.vectorstore import COLLECTIONS, get_qdrant_client
from app.models import Document
from app.schemas.documents import DocumentOut

router = APIRouter()

_REAL_UNITS = ["tv", "plus", "news"]
_FORMAT_BY_EXTENSION = {".md": "markdown", ".markdown": "markdown", ".pdf": "pdf"}


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


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(business_unit: str, claims: dict = Depends(get_current_claims)):
    _require_view(business_unit, claims)
    async with async_session() as session:
        rows = (
            await session.execute(
                select(Document).where(Document.business_unit_code == business_unit).order_by(Document.created_at.desc())
            )
        ).scalars().all()
        return rows


@router.post("/documents", response_model=DocumentOut, status_code=201)
async def upload_document(
    business_unit: str = Form(...),
    title: str = Form(""),
    file: UploadFile = File(...),
    claims: dict = Depends(get_current_claims),
):
    _require_manage(business_unit, claims)

    extension = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    format_ = _FORMAT_BY_EXTENSION.get(extension)
    if format_ is None:
        raise HTTPException(status_code=400, detail="Only Markdown (.md) and PDF (.pdf) files are supported.")

    safe_filename = re.sub(r"[^A-Za-z0-9._-]", "_", file.filename)
    object_key = f"{uuid.uuid4()}-{safe_filename}"
    resolved_title = title.strip() or file.filename

    content = await file.read()

    async with async_session() as session:
        document = Document(
            business_unit_code=business_unit,
            object_key=object_key,
            title=resolved_title,
            format=format_,
            status="pending",
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)

    # Written after the row commits: if the upload fails partway, the row
    # is still visible as "pending" rather than lost, and worker's own
    # insert_pending get-or-create will just find this row once the
    # object does land (or an admin can delete the stuck pending row and
    # retry).
    minio = get_minio_client()
    minio.put_object(BUCKETS[business_unit], object_key, io.BytesIO(content), length=len(content))

    return document


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(document_id: uuid.UUID, claims: dict = Depends(get_current_claims)):
    async with async_session() as session:
        document = await session.get(Document, document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found.")
        _require_manage(document.business_unit_code, claims)

        object_key = document.object_key
        business_unit = document.business_unit_code
        await session.delete(document)
        await session.commit()

    qdrant = get_qdrant_client()
    collection = COLLECTIONS[business_unit]
    if qdrant.collection_exists(collection):
        qdrant.delete(
            collection_name=collection,
            points_selector=Filter(must=[FieldCondition(key="source_document", match=MatchValue(value=object_key))]),
        )

    minio = get_minio_client()
    minio.remove_object(BUCKETS[business_unit], object_key)
