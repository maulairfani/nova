"""Manage Documents Endpoint - list/upload/delete the knowledge base
source files each business unit's MCP server retrieves from (kb_search).
Thin HTTP adapter - see app/services/document_service.py for the actual
logic (access control, MinIO/Qdrant orchestration)."""
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse

from app.api.v1.deps import get_current_claims
from app.schemas.documents import DocumentOut
from app.services import document_service

router = APIRouter()


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(business_unit: str, claims: dict = Depends(get_current_claims)):
    return await document_service.list_documents(business_unit, claims)


@router.get("/documents/lookup", response_model=DocumentOut)
async def find_document_by_source(business_unit: str, object_key: str, claims: dict = Depends(get_current_claims)):
    """Resolves a kb_search citation (Sources panel) back to its real
    Document row, so the frontend can open the same preview flow Manage
    Documents already uses instead of a raw (unauthenticated) MinIO URL."""
    return await document_service.find_by_source(business_unit, object_key, claims)


@router.get("/documents/{document_id}/content")
async def get_document_content(document_id: uuid.UUID, claims: dict = Depends(get_current_claims)):
    stream, content_type = await document_service.get_document_content(document_id, claims)
    return StreamingResponse(stream, media_type=content_type)


@router.post("/documents", response_model=DocumentOut, status_code=201)
async def upload_document(
    business_unit: str = Form(...),
    title: str = Form(""),
    file: UploadFile = File(...),
    claims: dict = Depends(get_current_claims),
):
    content = await file.read()
    return await document_service.upload_document(business_unit, title, file.filename, content, claims)


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(document_id: uuid.UUID, claims: dict = Depends(get_current_claims)):
    await document_service.delete_document(document_id, claims)
