"""Chat Endpoint (TDD §5.2) — receives messages, streams the response back
via SSE (ADR-0017). Thin HTTP adapter - see app/services/chat_service.py
and app/services/conversation_service.py for the actual logic."""
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.v1.deps import check_rate_limit, get_auth_headers, get_current_user_id
from app.schemas.chat import ChatRequest
from app.schemas.usage import UsageOut
from app.services import chat_service

router = APIRouter()


@router.post("/chat")
async def chat(
    payload: ChatRequest,
    request: Request,
    auth_headers: dict[str, str] = Depends(get_auth_headers),
    user_id: uuid.UUID = Depends(get_current_user_id),
    rate_limit: UsageOut = Depends(check_rate_limit),
):
    checkpointer = request.app.state.checkpointer
    await chat_service.touch_conversation(payload.thread_id, user_id, payload.message)

    response_headers = {
        "X-RateLimit-Limit": str(rate_limit.limit),
        "X-RateLimit-Remaining": str(rate_limit.remaining),
        "X-RateLimit-Reset": str(rate_limit.reset_seconds),
    }
    return StreamingResponse(
        chat_service.stream_chat_events(auth_headers, checkpointer, payload.thread_id, payload.message, payload.force_tools),
        media_type="text/event-stream",
        headers=response_headers,
    )
