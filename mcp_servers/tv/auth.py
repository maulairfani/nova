"""MCN TV's own authorization rule (ADR-0008 — callable-based, per-unit).

Phase 1 simplification: a minimal role/claim check. Richer per-unit rules
are follow-up work (TDD §11), not a phase-1 blocker.
"""
from common.auth import AuthContext

ALLOWED_ROLES = {"mcn_tv_employee", "group_admin"}


def check_tv_access(auth_context: AuthContext) -> bool:
    if "tv" in auth_context.business_units:
        return True
    return bool(ALLOWED_ROLES & set(auth_context.roles))
