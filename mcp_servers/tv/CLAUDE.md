# mcp_servers/tv/ — MCN TV's Business Unit MCP Server

FastMCP server (`mcp-tv`) exposing MCN TV's KB Search and SQL Analytics
tools, per TDD §5.2. This is the template phase 2 replicates for MCN+ and
MCN News (`mcp_servers/plus/`, `mcp_servers/news/`) — keep changes here in
mind as "what the template looks like," not just "what MCN TV needs."

## Structure

```
server.py            FastMCP app: registers tools behind the auth check
auth.py              MCN TV's own check_tv_access(AuthContext) -> bool
db.py                Async read-only connection + hardcoded schema description
tools/kb_search.py     Embeds query, searches Qdrant collection "mcn_tv"
tools/sql_analytics.py  Text-to-SQL against postgres-tv, SELECT-only
alembic/              Schema migrations (ADR-0016) — this server owns them,
                      not infrastructure/, since it's the only service that
                      ever connects to postgres-tv
seed/
  seed_postgres.py     Dummy analytics data (idempotent — no-ops if already seeded)
  seed_qdrant.py        Dummy KB documents -> embeddings (idempotent — deterministic point IDs)
  documents/            The 3 dummy SOP markdown files actually seeded
```

## Phase-1 simplification: KB seeding bypasses the real ingestion pipeline

TDD §6.5 describes an async ingestion pipeline (MinIO + Celery) that
doesn't exist yet (phase 2). Phase 1 needs *something* in Qdrant for the
KB Search Tool to search, so `seed/seed_qdrant.py` reads the 3 markdown
files in `seed/documents/` directly and embeds them — bypassing MinIO
entirely. This is a one-off manual script (see root README's setup
steps), not something that runs automatically on container start (to
avoid needless re-embedding cost/races on every restart).

**When phase 2 builds the real ingestion pipeline, this script should be
retired**, not extended — it's explicitly a stand-in, not a permanent
lightweight alternative.

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
