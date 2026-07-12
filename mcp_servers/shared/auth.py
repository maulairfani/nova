"""Shared MCP Server's own authorization rule (ADR-0008 — callable-based).

Unlike a business unit server, this server holds no business-unit-owned
data — web search results aren't scoped to any single unit. Any caller
with a recognized MCN Group identity (claims at least one business unit,
or an admin role) may use it; there's no finer-grained rule to enforce
here.
"""
from common.auth import AuthContext


def check_shared_access(auth_context: AuthContext) -> bool:
    if auth_context.business_units:
        return True
    return "group_admin" in auth_context.roles
