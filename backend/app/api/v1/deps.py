"""Derives the X-Nova-* header shape every MCP server's AuthContext expects
(mcp_servers/common/auth.py) from a verified JWT (ADR-0021), replacing
phase 1's unverified header pass-through (backend/CLAUDE.md)."""
import uuid

import jwt
from fastapi import Header, HTTPException

from app.core.security import decode_access_token


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
