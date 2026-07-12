# mcp_servers/news/ — MCN News's Business Unit MCP Server

FastMCP server (`mcp-news`) exposing MCN News's KB Search and SQL
Analytics tools, per TDD §5.2. A direct replication of `mcp_servers/tv/`'s
template (see that directory's `CLAUDE.md` for the original rationale).

## Structure

Same as `mcp_servers/tv/` — `server.py`, `auth.py`
(`check_news_access(AuthContext) -> bool`), `db.py`, `tools/`,
`alembic/`, `seed/`.

## MCN News-specific notes

- Schema covers `articles`, `article_engagement` (page views, unique
  visitors, time on page), and `ad_revenue` (by ad slot type) — reflecting
  MCN News's digital-first metrics rather than TV's daypart/rating model.
- 3 seeded SOPs cover the newsroom's editorial lifecycle: fact-checking
  before publication, expedited breaking-news publication, and
  correction/retraction handling.

## Phase-1 simplifications (inherited from the TV template)

Same as `mcp_servers/tv/CLAUDE.md`: KB seeding bypasses the real MinIO +
Celery ingestion pipeline (TDD §6.5) via a one-off `seed/seed_qdrant.py`
script; authorization is a minimal role/claim check
(`ALLOWED_ROLES = {"mcn_news_employee", "group_admin"}` or `"news"` in
the caller's business units), against an unverified dummy identity (see
`backend/CLAUDE.md`).

## Verifying changes here independent of the Backend API

Same recipe as `mcp_servers/tv/CLAUDE.md`, against port `9003`:

```bash
docker compose up -d mcp-news
curl -X POST http://localhost:9003/mcp -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" -H "Mcp-Session-Id: <id>" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"kb_search","arguments":{"query":"..."}}}'
```

Add `-H "X-Nova-Business-Units: news"` to pass authorization; omit it to
verify the auth check actually denies.
