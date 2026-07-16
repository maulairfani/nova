"""Conversations Endpoint - sidebar list/rename/delete for chat threads
(Conversation model, app/models.py). Ownership is scoped by user_id from
the JWT (get_current_user_id) - a caller can only see/rename/delete their
own conversations."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import delete, select

from app.agent.tool_labels import map_tool_step
from app.api.v1.deps import get_current_user_id
from app.core.db import async_session
from app.models import Conversation
from app.schemas.conversations import ConversationOut, ConversationRenameRequest, MessageOut

router = APIRouter()


async def _get_owned_conversation(session, conversation_id: str, user_id: uuid.UUID) -> Conversation:
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user_id:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(user_id: uuid.UUID = Depends(get_current_user_id)):
    async with async_session() as session:
        rows = (
            await session.execute(
                select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc())
            )
        ).scalars().all()
        return rows


@router.patch("/conversations/{conversation_id}", response_model=ConversationOut)
async def rename_conversation(
    conversation_id: str,
    payload: ConversationRenameRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    title = payload.title.strip() or "Untitled conversation"
    async with async_session() as session:
        conversation = await _get_owned_conversation(session, conversation_id, user_id)
        conversation.title = title
        await session.commit()
        await session.refresh(conversation)
        return conversation


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: str, request: Request, user_id: uuid.UUID = Depends(get_current_user_id)):
    async with async_session() as session:
        await _get_owned_conversation(session, conversation_id, user_id)
        await session.execute(delete(Conversation).where(Conversation.id == conversation_id))
        await session.commit()

    # The row above is only sidebar metadata - the actual message history
    # lives in LangGraph's own checkpoint tables under the same id as
    # thread_id, so it must be purged separately via the checkpointer's
    # own API rather than left as an orphaned, unlistable thread.
    checkpointer = request.app.state.checkpointer
    await checkpointer.adelete_thread(conversation_id)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
async def get_conversation_messages(
    conversation_id: str, request: Request, user_id: uuid.UUID = Depends(get_current_user_id)
):
    async with async_session() as session:
        await _get_owned_conversation(session, conversation_id, user_id)

    # Reads the checkpointer's stored graph state directly rather than
    # building the full agent (build_agent, chat.py) - that would connect
    # to every MCP server just to read history back, which isn't needed
    # for a plain state read.
    checkpointer = request.app.state.checkpointer
    checkpoint_tuple = await checkpointer.aget_tuple({"configurable": {"thread_id": conversation_id}})
    if checkpoint_tuple is None:
        return []

    raw_messages = checkpoint_tuple.checkpoint["channel_values"].get("messages", [])
    messages = []
    pending_steps: list[dict[str, str]] = []
    for m in raw_messages:
        if isinstance(m, HumanMessage) and m.content:
            messages.append(MessageOut(role="user", content=m.content))
            pending_steps = []
        elif isinstance(m, AIMessage):
            if m.tool_calls:
                # An AIMessage with tool_calls and no content is the agent
                # deciding to call tools, not an answer - buffer the steps
                # until the turn's actual final (content-bearing) AIMessage.
                pending_steps.extend(map_tool_step(tc["name"]) for tc in m.tool_calls)
            elif m.content:
                messages.append(MessageOut(role="assistant", content=m.content, steps=pending_steps))
                pending_steps = []
    return messages
