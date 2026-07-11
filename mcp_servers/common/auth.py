"""Shared callable-based authorization shape (ADR-0008/FastMCP).

Each business unit implements its own check function with this signature;
this module only defines the shared shape, not any unit's actual rules.
"""
from dataclasses import dataclass


@dataclass
class AuthContext:
    """Minimal phase-1 stand-in for FastMCP's AuthContext.

    Phase 1 simplification (documented in mcp_servers/tv/CLAUDE.md and the
    root README): there is no real auth system yet. The Backend API forwards
    a dummy identity via an `X-Nova-User` header; claims here are derived
    from that header rather than a verified token.
    """

    user_id: str
    business_units: list[str]
    roles: list[str]
