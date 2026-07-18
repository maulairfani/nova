"""Chat Endpoint (TDD §5.2) — receives messages, streams the response back
via SSE (ADR-0017)."""
import json
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from sqlalchemy import func

from app.agent.graph import build_agent
from app.agent.tool_labels import map_tool_step, parse_chart_result
from app.api.v1.deps import check_rate_limit, get_auth_headers, get_current_user_id
from app.core.db import async_session
from app.models import Conversation
from app.schemas.chat import ChatRequest
from app.schemas.usage import UsageOut

router = APIRouter()


def _conversation_title(message: str) -> str:
    text = message.strip()
    return text[:42] + "…" if len(text) > 42 else text


async def _touch_conversation(thread_id: str, user_id: uuid.UUID, first_message: str) -> None:
    """Upserts the sidebar's Conversation row (app/models.py) for this
    thread - created with a title derived from the first message, bumped
    (updated_at only, title unchanged) on every later message so the
    sidebar can order by recency."""
    async with async_session() as session:
        conversation = await session.get(Conversation, thread_id)
        if conversation is None:
            session.add(Conversation(id=thread_id, user_id=user_id, title=_conversation_title(first_message)))
        else:
            conversation.updated_at = func.now()
        await session.commit()


@router.post("/chat")
async def chat(
    payload: ChatRequest,
    request: Request,
    auth_headers: dict[str, str] = Depends(get_auth_headers),
    user_id: uuid.UUID = Depends(get_current_user_id),
    rate_limit: UsageOut = Depends(check_rate_limit),
):
    checkpointer = request.app.state.checkpointer
    await _touch_conversation(payload.thread_id, user_id, payload.message)

    async def event_stream():
        agent = await build_agent(auth_headers, checkpointer, payload.force_tools)
        config = {"configurable": {"thread_id": payload.thread_id}}
        inputs = {"messages": [HumanMessage(content=payload.message)]}

        async for event in agent.astream_events(inputs, config=config, version="v2"):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield f"data: {json.dumps({'token': chunk.content})}\n\n"
            elif event["event"] == "on_tool_start":
                step = map_tool_step(event["name"])
                yield f"event: tool_start\ndata: {json.dumps({'id': str(event['run_id']), **step})}\n\n"
            elif event["event"] == "on_tool_end":
                yield f"event: tool_end\ndata: {json.dumps({'id': str(event['run_id'])})}\n\n"
                chart = parse_chart_result(event["name"], event["data"]["output"].content)
                if chart is not None:
                    yield f"event: chart\ndata: {json.dumps(chart)}\n\n"

        yield "event: done\ndata: {}\n\n"

    response_headers = {
        "X-RateLimit-Limit": str(rate_limit.limit),
        "X-RateLimit-Remaining": str(rate_limit.remaining),
        "X-RateLimit-Reset": str(rate_limit.reset_seconds),
    }
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=response_headers)
