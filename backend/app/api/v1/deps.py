"""Derives the X-Nova-* header shape every MCP server's AuthContext expects
(mcp_servers/common/auth.py) from a verified JWT (ADR-0021), replacing
phase 1's unverified header pass-through (backend/CLAUDE.md)."""
import jwt
from fastapi import Header, HTTPException

from app.core.security import decode_access_token


def get_auth_headers(authorization: str | None = Header(default=None)) -> dict[str, str]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
    token = authorization.split(" ", 1)[1]
    try:
        claims = decode_access_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

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
