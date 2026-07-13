"""Chat Endpoint (TDD §5.2) — receives messages, streams the response back
via SSE (ADR-0017)."""
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.agent.graph import build_agent
from app.api.v1.deps import get_auth_headers
from app.schemas.chat import ChatRequest

router = APIRouter()


@router.post("/chat")
async def chat(payload: ChatRequest, request: Request, auth_headers: dict[str, str] = Depends(get_auth_headers)):
    checkpointer = request.app.state.checkpointer

    async def event_stream():
        agent = await build_agent(auth_headers, checkpointer)
        config = {"configurable": {"thread_id": payload.thread_id}}
        inputs = {"messages": [HumanMessage(content=payload.message)]}

        async for event in agent.astream_events(inputs, config=config, version="v2"):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield f"data: {json.dumps({'token': chunk.content})}\n\n"

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
