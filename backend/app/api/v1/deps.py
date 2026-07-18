"""Derives the X-Nova-* header shape every MCP server's AuthContext expects
(mcp_servers/common/auth.py) from a verified JWT (ADR-0021), replacing
phase 1's unverified header pass-through (backend/CLAUDE.md)."""
import uuid

import jwt
from fastapi import Depends, Header, HTTPException

from app.core.rate_limit import increment_and_check
from app.core.security import decode_access_token
from app.schemas.usage import UsageOut


def _decode_bearer(authorization: str | None) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
    token = authorization.split(" ", 1)[1]
    try:
        return decode_access_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")


def get_current_user_id(authorization: str | None = Header(default=None)) -> uuid.UUID:
    """Verifies the JWT and returns the caller's user id - used by
    endpoints (conversations.py) that scope rows to `user_id` rather than
    needing the full X-Nova-* header shape get_auth_headers builds for the
    MCP servers."""
    claims = _decode_bearer(authorization)
    return uuid.UUID(claims["sub"])


def get_current_claims(authorization: str | None = Header(default=None)) -> dict:
    """Verifies the JWT and returns its full claims dict - used by
    endpoints (documents.py) that need the caller's per-business-unit
    role_code, not just a flattened header shape or the bare user id."""
    return _decode_bearer(authorization)


def get_auth_headers(authorization: str | None = Header(default=None)) -> dict[str, str]:
    claims = _decode_bearer(authorization)

    memberships = claims.get("business_units", [])
    business_units = [m["code"] for m in memberships]
    # Bridges ADR-0021's "group" + "admin" tier to the "group_admin" role
    # string every unit's auth.py (and mcp_servers/shared/auth.py) already
    # checks for - keeps those checks unchanged for now (updating them to
    # read business_unit_roles tiers directly is separate follow-up work,
    # noted in ADR-0021).
    roles = ["group_admin" for m in memberships if m["code"] == "group" and m["role"] == "admin"]

    return {
        "x-nova-user": claims["sub"],
        "x-nova-business-units": ",".join(business_units),
        "x-nova-roles": ",".join(roles),
    }


def _format_retry_duration(seconds: int) -> str:
    hours, remainder = divmod(max(seconds, 0), 3600)
    minutes = remainder // 60
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    if minutes:
        return f"{minutes}m"
    return "a moment"


async def check_rate_limit(user_id: uuid.UUID = Depends(get_current_user_id)) -> UsageOut:
    """Chat-only per-user rate limit (ADR-0027): 50 requests / rolling 5h
    window, Redis-backed, no exemptions. Raises 429 when exceeded; returns
    the status otherwise so chat.py can stamp the same headers on success."""
    status = await increment_and_check(user_id)
    if status.used > status.limit:
        retry_after = str(status.reset_seconds)
        raise HTTPException(
            status_code=429,
            detail=(
                f"You've reached the limit of {status.limit} messages per 5-hour window. "
                f"Try again in {_format_retry_duration(status.reset_seconds)}."
            ),
            headers={
                "Retry-After": retry_after,
                "X-RateLimit-Limit": str(status.limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": retry_after,
            },
        )
    return status
