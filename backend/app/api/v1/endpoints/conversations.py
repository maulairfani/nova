"""Conversations Endpoint - sidebar list/rename/delete for chat threads.
Ownership is scoped by user_id from the JWT (get_current_user_id). Thin
HTTP adapter - see app/services/conversation_service.py for the actual
logic."""
import uuid

from fastapi import APIRouter, Depends, Request

from app.api.v1.deps import get_current_user_id
from app.schemas.conversations import ConversationOut, ConversationRenameRequest, MessageOut
from app.services import conversation_service

router = APIRouter()


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(user_id: uuid.UUID = Depends(get_current_user_id)):
    return await conversation_service.list_conversations(user_id)


@router.patch("/conversations/{conversation_id}", response_model=ConversationOut)
async def rename_conversation(
    conversation_id: str,
    payload: ConversationRenameRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    return await conversation_service.rename_conversation(conversation_id, user_id, payload.title)


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: str, request: Request, user_id: uuid.UUID = Depends(get_current_user_id)):
    await conversation_service.delete_conversation(conversation_id, user_id, request.app.state.checkpointer)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
async def get_conversation_messages(
    conversation_id: str, request: Request, user_id: uuid.UUID = Depends(get_current_user_id)
):
    return await conversation_service.get_conversation_messages(conversation_id, user_id, request.app.state.checkpointer)
