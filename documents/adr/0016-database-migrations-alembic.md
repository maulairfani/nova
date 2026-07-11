# ADR-0016: Database Schema Migrations — Alembic

**Status:** Accepted

## Decision

Use **Alembic** to manage schema migrations for every business-unit
PostgreSQL database (starting with `postgres-tv`, replicated for
`postgres-plus` and `postgres-news` in phase 2). Each Business Unit MCP
Server owns its own Alembic environment and migration history, since it's
the only service that connects to its unit's database (Section 5.2) — this
is not shared tooling in the Backend API.

## Context

TDD Section 5.2 fixes each Business Unit MCP Server as the sole owner of
its unit's PostgreSQL schema. The initial implementation used a plain SQL
file mounted into Postgres's `/docker-entrypoint-initdb.d` (auto-run once,
on first container start) for both schema creation and dummy-data seeding.
This has no forward migration path — any schema change after the first run
requires manually dropping the volume, which doesn't scale past a first
demo pass and isn't a pattern that would be defensible for a real business
unit's production data.

## Alternatives Considered

- **Plain SQL init scripts only** (the original approach): simplest to
  write, but no versioned migration history, no repeatable "add a column"
  path, and no separation between schema definition and dummy-data seeding
  — rejected once schema evolution became a realistic near-term need
  (e.g. adding `ad_revenue` after `programs`/`viewership_ratings` already
  existed).
- **A different migration tool per business unit** (e.g. raw
  hand-rolled SQL migration scripts): rejected — inconsistent with the
  goal of all Business Unit MCP Servers following an identical template
  (Section 5.2); Alembic is the standard, well-known SQLAlchemy-ecosystem
  tool and needs no bespoke tooling to maintain.

## Rationale

Alembic is the de facto migration tool for SQLAlchemy-based Python
services, has first-class support for both sync and async engines (the
migration runner itself uses a sync `psycopg2` connection even though
runtime queries use an async driver — a standard, documented Alembic
pattern, not a special case), and keeps schema changes versioned and
reviewable like any other code change. Since every Business Unit MCP
Server follows the same internal shape (Section 5.2), the same Alembic
setup replicates cleanly to `mcp-plus` and `mcp-news` in phase 2.

Dummy-data seeding stays a **separate** concern from schema migrations
(a plain Python seed script run after `alembic upgrade head`), matching
the same separation already used for Qdrant (schema/collection creation
vs. content seeding) — one consistent pattern across both data stores.

## Consequences

- Positive: schema changes are versioned, reviewable, and repeatable
  across environments — no more "wipe the volume to change a column."
- Positive: consistent with the async-runtime/sync-migration pattern
  common in the FastAPI + SQLAlchemy ecosystem; no bespoke process.
- Negative: one more moving part per Business Unit MCP Server (an
  `alembic upgrade head` step must run before the server can serve
  queries) — documented as an explicit setup step in each unit's
  `CLAUDE.md` and the root README, same treatment as the Qdrant seed step.
- Negative: adds `alembic`, `sqlalchemy`, and a sync Postgres driver
  (`psycopg2-binary`) to each Business Unit MCP Server's dependencies,
  alongside the async driver (`asyncpg`) used at runtime.
