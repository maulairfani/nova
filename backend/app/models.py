"""SQLAlchemy declarative models for nova_core - the ORM source of truth
Alembic migrations are generated from (see alembic/env.py's target_metadata).

Message content and agent state are NOT modeled here - those live in
LangGraph's own checkpoint tables (checkpointer.py, ADR-0012), created by
setup_checkpointer.py, not by this file or Alembic.
"""
import uuid

from sqlalchemy import Boolean, ForeignKey, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    email: Mapped[str] = mapped_column(Text, unique=True)
    # Nullable: the real auth mechanism (session/JWT/SSO) is a separate,
    # not-yet-made decision - this model stays agnostic to it.
    password_hash: Mapped[str | None] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())


class BusinessUnit(Base):
    __tablename__ = "business_units"

    # Natural key (not a serial id): "tv"/"plus"/"news" are the exact
    # strings already used throughout the codebase (mcp_client.py's
    # _SERVER_TO_BUSINESS_UNIT, the X-Nova-Business-Units header) - no join
    # needed to get back to the value everything else already speaks in.
    # "group" is a virtual entry (MCN Group corporate-level, not a real
    # per-unit MCP server) - membership in it represents an MCN
    # Group-level claim rather than a specific unit's data access, letting
    # cross-cutting permissions (e.g. an "admin" tier) reuse the exact same
    # membership+role mechanism as real business units instead of a
    # separate roles table.
    code: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)


class BusinessUnitRole(Base):
    __tablename__ = "business_unit_roles"

    # The permission tier a member has *within* a business unit (or the
    # virtual "group" unit) they belong to - e.g. "employee" gets KB search
    # + non-sensitive analytics, "finance" additionally gets revenue data,
    # "admin" (only meaningful under the "group" unit) gets cross-unit data
    # access. Shared across units rather than one role per unit, to avoid a
    # combinatorial explosion of unit-prefixed role codes - not every code
    # is meaningful under every unit; that's interpreted by each unit's own
    # auth check, not enforced here.
    code: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)


class UserBusinessUnit(Base):
    __tablename__ = "user_business_units"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    business_unit_code: Mapped[str] = mapped_column(Text, ForeignKey("business_units.code"), primary_key=True)
    # One tier per membership (not a many-to-many join) - a member's
    # standing within a given unit is a single value, not a set.
    role_code: Mapped[str] = mapped_column(Text, ForeignKey("business_unit_roles.code"), server_default="employee")
