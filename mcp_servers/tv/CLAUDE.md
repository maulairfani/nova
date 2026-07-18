# mcp_servers/tv/ — MCN TV's Business Unit MCP Server

FastMCP server (`mcp-tv`) exposing MCN TV's KB Search and SQL Analytics
tools, per TDD §5.2. This is the template phase 2 replicates for MCN+ and
MCN News (`mcp_servers/plus/`, `mcp_servers/news/`) — keep changes here in
mind as "what the template looks like," not just "what MCN TV needs."

## Structure

```
server.py            FastMCP app: registers tools behind the auth check
auth.py              MCN TV's own check_tv_access(AuthContext) -> bool
db.py                Async read-only connection; SCHEMA_DESCRIPTION loaded from semantic/schema.yaml
tools/kb_search.py     Embeds query, searches Qdrant collection "mcn_tv"
tools/sql_analytics.py  Text-to-SQL against postgres-tv, SELECT-only
alembic/              Schema migrations (ADR-0016) — this server owns them,
                      not infrastructure/, since it's the only service that
                      ever connects to postgres-tv. 0002_dimensional_schema.py
                      (ADR-0023) replaced the original flat schema with a
                      Nielsen-style dimensional model.
semantic/schema.yaml   Semantic layer (ADR-0024) — table/column business
                      meaning, glossary, derived metrics, example queries;
                      rendered by mcp_servers/common/semantic_layer.py
```

Dummy analytics data is no longer seeded from a `seed/` directory here —
it moved to the root-level `SEED_DATA/` (ADR-0025), which seeds all 3
business units' databases together.

## KB seeding goes through the real ingestion pipeline

Phase 1 had a `seed/seed_qdrant.py` script that embedded MCN TV's 3 dummy
SOP docs directly into Qdrant, bypassing MinIO entirely — a stand-in for
when the real async ingestion pipeline (MinIO + Celery, ADR-0022) didn't
exist yet. That pipeline now exists (`worker/`), so the bypass was
retired rather than kept alongside it: MCN TV's dummy KB documents live
at [`documents/kb/tv/`](../../documents/kb/tv/) (repo root, shared across
all 3 business units, not colocated here) and are seeded by uploading
them into MinIO via `worker/seed_documents.py` (see root README's setup
steps) — the exact same path a real upload through Manage Documents or
the MinIO console takes. There is no direct-to-Qdrant shortcut left
anywhere in the codebase.

## Phase-1 simplification: dummy authorization

`auth.py`'s `check_tv_access` is intentionally simple (checks for `"tv"`
in the caller's business units, or an allowlisted role) — TDD §11 already
flags richer per-unit authorization rules as follow-up work, not a
phase-1 blocker. The identity itself is unverified (see `backend/CLAUDE.md`).

## Verifying changes here independent of the Backend API

Test `mcp-tv` standalone before assuming a bug is in the agent/backend —
send raw MCP protocol requests directly:

```bash
docker compose up -d mcp-tv
# initialize, capture Mcp-Session-Id from the response headers, then:
curl -X POST http://localhost:9001/mcp -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" -H "Mcp-Session-Id: <id>" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"kb_search","arguments":{"query":"..."}}}'
```

Add `-H "X-Nova-Business-Units: tv"` to pass authorization; omit it to
verify the auth check actually denies (it should return `isError: true`
with "Not authorized for MCN TV's data.").

## Real bug fixed: the SQL Analytics Tool rejected its own valid queries

`db.py`'s `run_select` guard originally only accepted a query starting
with a literal `select`. `tools/sql_analytics.py`'s own text-to-SQL step
(a nested LLM call, not the main agent) correctly reaches for a `WITH ...
SELECT ...` CTE for any question involving a comparison (week-over-week,
month-over-month, "latest vs. last 7/30 days", etc.) - a completely
safe, read-only query, but one the guard rejected outright with "Only
SELECT statements are allowed.", **deterministically, every time**, not
as an occasional model slip. Reproduced directly against the live
service (bypassing the agent) to confirm it wasn't a backend/agent bug:
the same question phrased simply ("last 7 days total") produced a plain
`SELECT` and worked; the same question asking for a WoW/MoM comparison
produced a `WITH` CTE and failed 100% of the time. Fixed by also
accepting a `with`-prefixed query - the existing forbidden-keyword check
(`insert`/`update`/`delete`/...) still runs afterward and would catch a
data-modifying CTE (Postgres allows `WITH x AS (DELETE FROM ... RETURNING
*) SELECT * FROM x`), so this doesn't weaken the actual safety guarantee,
only stops rejecting a legitimate query shape. Same guard, same fix,
duplicated identically in `mcp_servers/plus/db.py` and
`mcp_servers/news/db.py`. Added a regression test
(`tests/test_db.py::test_accepts_a_cte_query_and_reaches_the_database`,
same pattern in all 3 units) that stubs the DB connection to assert the
guard lets a CTE through instead of raising `NonSelectQueryError` first.
Verified against the live stack: the exact previously-failing question
now returns real revenue rows with WoW/MoM deltas, both calling the tool
directly and through a full chat request via the backend agent.
