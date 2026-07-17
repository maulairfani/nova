# ADR-0025: Consolidated Dummy Seed Data Under `SEED_DATA/`

**Status:** Accepted

## Decision

Retire the three independent `mcp_servers/<unit>/seed/seed_postgres.py`
scripts and replace them with one consolidated location at the repo
root, `SEED_DATA/`, containing:

- `tv_data.py`, `plus_data.py`, `news_data.py` — per-unit dimension value
  lists and fact-row generators for the new dimensional schema (ADR-0023).
- `seed_all.py` — orchestrator that connects to all three business-unit
  databases (admin URLs, same credentials Alembic already uses) and seeds
  each, idempotently (a no-op if already seeded, same guarantee the old
  per-unit scripts made).
- Its own `Dockerfile`/`requirements.txt`, run as a one-off Docker Compose
  service (`seed-data`) rather than piggy-backing on any business unit
  MCP server's own image.

Schema migrations stay exactly where ADR-0016 put them (each unit's own
Alembic environment) — this ADR only relocates *dummy analytics data*,
not schema ownership.

## Context

Each Business Unit MCP Server previously generated its own dummy data in
its own `seed/seed_postgres.py`, replicated by copying `mcp_servers/tv/`'s
template (same pattern the servers themselves follow, per that
directory's `CLAUDE.md`). That worked while every unit had the same 3
flat tables and ~4 dimension rows apiece. ADR-0023's dimensional schema
makes that no longer true: seeding now requires inserting dimension rows
*before* the fact rows that reference them, in a specific order, with
meaningfully more volume per unit (Nielsen-style ratings alone are a
cross-product of airings × DMAs × demographic segments) — three
independently-maintained copies of that ordering logic is real drift risk
for no benefit, since (unlike the MCP servers themselves) the seed
scripts were never behind an authorization boundary that needed them kept
separate.

## Alternatives Considered

- **Keep three per-unit seed scripts, just make each more complex**:
  rejected — this was the status quo and is exactly what motivated this
  ADR; three copies of dimension-then-fact ordering logic is the kind of
  duplication `mcp_servers/common/` already exists to avoid for other
  shared concerns (embeddings, Qdrant helpers).
- **One seed script per unit, but still colocated inside that unit's
  `seed/` directory**: rejected — doesn't solve the actual problem (three
  independently-run, independently-drifting scripts); consolidating
  location without consolidating orchestration would be reorganization
  without the benefit.
- **Fold seeding into each unit's own Alembic migration (data migration,
  not just schema)**: rejected — conflates two different concerns
  (`ALTER TABLE`s that must run once, in order, forever vs. dummy content
  that a developer might want to regenerate or resize) and was already
  rejected once for this reason in ADR-0016 ("dummy-data seeding stays a
  separate concern from schema migrations").
- **A single seed script that also seeds `nova_core` and the knowledge
  base**: rejected — `nova_core`'s seed (`seed_users.py`) and the KB seed
  (`worker/seed_documents.py`) are already correctly scoped to the
  services that own that data (`backend/`, `worker/` respectively, per
  ADR-0021/0022); pulling them into `SEED_DATA/` would blur ownership
  boundaries this project has otherwise kept clean. `SEED_DATA/` is
  scoped specifically to the three business-unit analytics databases,
  which have no other natural single owner now that their seed data no
  longer belongs to any one unit's own image.

## Rationale

A single location with per-unit generator modules keeps the *content*
scoped per business unit (so `tv_data.py` still only knows about Nielsen
ratings, `plus_data.py` only about subscriptions/coins) while sharing the
*mechanics* — idempotency check, dimension-before-fact insert ordering,
bulk-insert helpers — once. This is the same shared-mechanics-not-shared-
content shape as `mcp_servers/common/semantic_layer.py` (ADR-0024) and
`common/embeddings.py`: one seam per concern, not one seam per business
unit copy-pasted three times.

Running it as its own Compose service (rather than, say,
`docker compose run --rm mcp-tv python /seed_data/tv_data.py`) keeps it
from needing network/filesystem access into three other services' build
contexts — `seed-data` gets its own small image with only what seeding
needs (`sqlalchemy` + `psycopg2`, no FastMCP/Qdrant/OpenRouter
dependencies at all), and is invoked once, the same one-off-command
pattern already used for every other bootstrap step (migrations,
`bootstrap_buckets.py`, `seed_users.py`).

## Consequences

- Positive: one place to look for how any business unit's dummy analytics
  data is generated, instead of three.
- Positive: seed volume was substantially increased as part of this move
  (multi-year daily fact data instead of a few weeks) to actually reflect
  the "big data" framing this project answers — a change that would have
  had to be made three times over under the old layout.
- Positive: `seed-data`'s image has no MCP/Qdrant/OpenRouter dependencies
  at all — smaller, faster to build, and clearly scoped to exactly one
  job.
- Negative: one more Compose service and one more root-level directory
  outside the mandated `backend/`/`frontend/`/`infrastructure/` structure
  — accepted, same as `worker/`'s existing precedent of a new top-level
  directory when a concern doesn't naturally belong inside any existing
  one.
- Negative: `mcp_servers/<unit>/CLAUDE.md`'s "Structure" section no longer
  lists a `seed/` subdirectory — updated in this pass, not left stale.
