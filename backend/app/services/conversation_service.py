"""Conversations business logic - ownership enforcement, the sidebar
title-derivation rule, and reconstructing a thread's message history from
the checkpointer's stored state. app/api/v1/endpoints/conversations.py and
chat.py stay thin HTTP/SSE adapters around this."""
import uuid

from fastapi import HTTPException
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agent.tool_labels import map_tool_step, merge_citations, parse_chart_result, parse_citations
from app.core.db import async_session
from app.models import Conversation
from app.repositories import conversation_repository
from app.schemas.conversations import MessageOut


def derive_title(first_message: str) -> str:
    text = first_message.strip()
    return text[:42] + "…" if len(text) > 42 else text


async def _get_owned(session, conversation_id: str, user_id: uuid.UUID) -> Conversation:
    conversation = await conversation_repository.get(session, conversation_id)
    if conversation is None or conversation.user_id != user_id:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation


async def list_conversations(user_id: uuid.UUID) -> list[Conversation]:
    async with async_session() as session:
        return await conversation_repository.list_by_user(session, user_id)


async def touch_conversation(thread_id: str, user_id: uuid.UUID, first_message: str) -> None:
    """Upserts the sidebar's Conversation row for this thread - called by
    chat.py on every message (created with a derived title on the first
    one, bumped on every later one)."""
    async with async_session() as session:
        await conversation_repository.touch(session, thread_id, user_id, derive_title(first_message))


async def rename_conversation(conversation_id: str, user_id: uuid.UUID, title: str) -> Conversation:
    title = title.strip() or "Untitled conversation"
    async with async_session() as session:
        conversation = await _get_owned(session, conversation_id, user_id)
        return await conversation_repository.rename(session, conversation, title)


async def delete_conversation(conversation_id: str, user_id: uuid.UUID, checkpointer) -> None:
    async with async_session() as session:
        await _get_owned(session, conversation_id, user_id)
        await conversation_repository.delete(session, conversation_id)

    # The row above is only sidebar metadata - the actual message history
    # lives in LangGraph's own checkpoint tables under the same id as
    # thread_id, so it must be purged separately via the checkpointer's
    # own API rather than left as an orphaned, unlistable thread.
    await checkpointer.adelete_thread(conversation_id)


async def get_conversation_messages(conversation_id: str, user_id: uuid.UUID, checkpointer) -> list[MessageOut]:
    async with async_session() as session:
        await _get_owned(session, conversation_id, user_id)

    # Reads the checkpointer's stored graph state directly rather than
    # building the full agent (build_agent) - that would connect to every
    # MCP server just to read history back, which isn't needed for a plain
    # state read.
    checkpoint_tuple = await checkpointer.aget_tuple({"configurable": {"thread_id": conversation_id}})
    if checkpoint_tuple is None:
        return []

    raw_messages = checkpoint_tuple.checkpoint["channel_values"].get("messages", [])
    messages: list[MessageOut] = []
    pending_steps: list[dict[str, str]] = []
    pending_charts: list[dict[str, str]] = []
    pending_citations: list[dict] = []
    for m in raw_messages:
        if isinstance(m, HumanMessage) and m.content:
            messages.append(MessageOut(role="user", content=m.content))
            pending_steps = []
            pending_charts = []
            pending_citations = []
        elif isinstance(m, ToolMessage):
            # The tool CALL (AIMessage.tool_calls, below) only has the
            # request, not the result - a chart's id (or a kb/web result's
            # citation fields) only exists in the matching ToolMessage's
            # own content.
            chart = parse_chart_result(m.name, m.content)
            if chart is not None:
                pending_charts.append(chart)
            pending_citations = merge_citations(pending_citations, parse_citations(m.name, m.content))
        elif isinstance(m, AIMessage):
            if m.tool_calls:
                # An AIMessage with tool_calls and no content is the agent
                # deciding to call tools, not an answer - buffer the steps
                # until the turn's actual final (content-bearing) AIMessage.
                pending_steps.extend(map_tool_step(tc["name"]) for tc in m.tool_calls)
            elif m.content:
                messages.append(
                    MessageOut(
                        role="assistant",
                        content=m.content,
                        steps=pending_steps,
                        charts=pending_charts,
                        citations=pending_citations,
                    )
                )
                pending_steps = []
                pending_charts = []
                pending_citations = []
    return messages
