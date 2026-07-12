"""MCN+'s own authorization rule (ADR-0008 — callable-based, per-unit).

Covers both MCN+ products (streaming and shorts) since they share one
MCP server (ADR-0014). Phase 1 simplification: a minimal role/claim check.
Richer per-unit rules are follow-up work (TDD §11), not a phase-1 blocker.
"""
from common.auth import AuthContext

ALLOWED_ROLES = {"mcn_plus_employee", "group_admin"}


def check_plus_access(auth_context: AuthContext) -> bool:
    if "plus" in auth_context.business_units:
        return True
    return bool(ALLOWED_ROLES & set(auth_context.roles))
