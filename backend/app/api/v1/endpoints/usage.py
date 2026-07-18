"""Usage Endpoint (ADR-0027) — read-only status for the chat rate limit,
polled by the frontend's Settings view. Deliberately does not depend on
check_rate_limit: checking your usage must never itself consume quota."""
import uuid

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_current_user_id
from app.core.rate_limit import get_usage_status
from app.schemas.usage import UsageOut

router = APIRouter()


@router.get("/usage", response_model=UsageOut)
async def get_usage(user_id: uuid.UUID = Depends(get_current_user_id)) -> UsageOut:
    return await get_usage_status(user_id)
