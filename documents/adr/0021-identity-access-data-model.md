# ADR-0021: Identity & Access Data Model (nova_core)

**Status:** Accepted

## Decision

`nova_core` gets a minimal identity/access schema, the foundation the
upcoming real authentication system (replacing the phase-1 unverified
header pass-through, `backend/CLAUDE.md`) will be built on:

- **`users`** - accounts (email, password hash, display name). No
  self-service signup - accounts are seeded/managed directly, matching how
  every other piece of dummy data in this project is provisioned.
- **`business_units`** - lookup table for `tv`/`plus`/`news`, plus one
  virtual entry, **`group`**, representing an MCN Group corporate-level
  claim (not a real per-unit MCP server) rather than a specific unit's
  data.
- **`business_unit_roles`** - lookup table for the permission tier a user
  has *within* a unit they belong to: `employee` (default), `finance`
  (additionally allowed sensitive/revenue data within that unit), `admin`
  (only meaningful under the virtual `group` unit - cross-unit data
  access without needing per-unit membership).
- **`user_business_units`** - the only membership/claim table: one row per
  (user, business unit) pair, carrying that pairing's `role_code`. A
  single mechanism covers every kind of claim this system needs - unit
  membership, unit-scoped permission tier, and MCN Group-level roles (as
  membership in the virtual `group` unit) - rather than a separate
  parallel table for cross-unit roles.

Conversation ownership/history is deliberately **not** modeled here - see
Alternatives Considered.

## Context

Phase 1's `AuthContext` (`mcp_servers/common/auth.py`) is populated from
unverified `X-Nova-*` headers forwarded as-is by the Backend API - "good
enough to give each unit's auth check something real to evaluate," not a
real identity system (`backend/CLAUDE.md`). Building real login/JWT auth
needs somewhere to actually look up who a user is and what they can
access - this ADR is that schema, decided before the auth mechanism itself
(a separate, not-yet-made decision) so the auth work has a stable
foundation to build against.

This is also the first schema `nova_core` (renamed from `nova_kb` once its
scope grew past "just conversation state," see git history) owns outside
of LangGraph's own checkpoint tables (ADR-0012) - `backend/` gained its
own Alembic setup for it (previously only the per-business-unit MCP
servers had migrations, ADR-0016), generated from a new SQLAlchemy
`app/models.py` rather than hand-written `op.create_table` calls (the
mcp_servers/*/alembic convention), since this schema is expected to grow
and evolve as auth is actually built, and autogenerate keeps migrations
from drifting out of sync with the ORM models by construction.

## Alternatives Considered

- **A separate `roles`/`user_roles` table for MCN Group-level roles
  (`group_employee`, `group_admin`), distinct from `business_unit_roles`**:
  rejected - "MCN Group" is really just another entity a user can have a
  claim against, exactly like a business unit. Giving it its own parallel
  table and role vocabulary would mean two different mechanisms
  expressing the same underlying idea (a scoped membership + tier), and
  two places that could drift out of sync in what "admin" or "employee"
  means. Modeling `group` as a `business_units` row lets it reuse
  `user_business_units` + `business_unit_roles` unchanged.
- **A `conversations` table for per-user chat history ownership/listing**:
  rejected for now - no feature today needs "list my past conversations";
  LangGraph's own checkpoint tables (keyed by `thread_id`) are sufficient
  until that feature is actually built, at which point `thread_id`-to-user
  ownership can be added (e.g. via the checkpoint's own JSONB `metadata`
  column, or a dedicated table then) without this schema needing to
  anticipate it now.
- **Business-unit-scoped role codes, e.g. `mcn_tv_employee`/`mcn_tv_finance`
  per unit** (the shape `mcn_servers/*/auth.py`'s `ALLOWED_ROLES` already
  uses today): rejected - `user_business_units` already answers "is this
  user in this unit," so a role name repeating the unit prefix would be
  redundant with the row's own `business_unit_code`. `business_unit_roles`
  is intentionally unit-agnostic (`employee`, `finance`, `admin` mean the
  same thing regardless of which unit's membership row they're attached
  to), avoiding a combinatorial explosion of unit×tier role codes.
- **Serial/UUID surrogate keys for `business_units`/`business_unit_roles`**:
  rejected - `code` (e.g. `"tv"`, `"employee"`) is a natural key already
  used verbatim throughout the codebase (`mcp_client.py`'s
  `_SERVER_TO_BUSINESS_UNIT`, the `X-Nova-Business-Units` header) - a
  surrogate key would need an extra join just to get back to the string
  every other component already speaks in.

## Rationale

One membership mechanism for every kind of claim (unit-specific or MCN
Group-level) means one place to query, one place to enforce constraints,
and no risk of the two "role" ideas drifting apart in meaning. Generating
migrations from `app/models.py` (vs. mcp_servers'/*'s hand-written
`op.create_table`) fits this schema's expected trajectory - it will keep
growing as real auth is implemented, unlike a per-unit analytics schema
that's fixed once seeded.

## Consequences

- Positive: the schema is ready for the login/JWT work to build directly
  against - `user_business_units` joined against `business_unit_roles`
  gives exactly the claims (`business_units`, per-unit tier) an issued
  token needs to carry.
- Positive: `alembic revision --autogenerate` + the `include_object`
  filter in `backend/alembic/env.py` (excluding LangGraph's
  checkpoint-owned tables from comparison) means future schema changes
  here are generated and verified against real drift, not hand-maintained
  in parallel with the ORM models.
- Negative: each business unit MCP server's `auth.py`
  (`ALLOWED_ROLES = {"mcn_tv_employee", "group_admin"}` and similar) still
  reflects the old phase-1 claim shape - follow-up work when auth is wired
  through is to derive `AuthContext` from real `user_business_units`
  rows and update each unit's check accordingly, not a blocker for this
  schema existing.
- Negative: `business_unit_roles`' tiers (`finance`, `admin`) are not yet
  enforced anywhere - today's SQL Analytics Tool (`run_select`) only
  guards against non-`SELECT` statements, not which tables/columns a
  caller's tier permits. Enforcing that is separate follow-up work in each
  unit's MCP server, tracked here so it isn't forgotten once auth ships.
