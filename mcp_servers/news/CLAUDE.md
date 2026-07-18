# mcp_servers/news/ — MCN News's Business Unit MCP Server

FastMCP server (`mcp-news`) exposing MCN News's KB Search and SQL
Analytics tools, per TDD §5.2. A direct replication of `mcp_servers/tv/`'s
template (see that directory's `CLAUDE.md` for the original rationale).

## Structure

Same as `mcp_servers/tv/` — `server.py`, `auth.py`
(`check_news_access(AuthContext) -> bool`), `db.py`, `tools/`,
`alembic/`, `semantic/schema.yaml`. Dummy analytics data is seeded from
the root-level `SEED_DATA/` (ADR-0025), not a local `seed/` directory.

## MCN News-specific notes

- **Dimensional schema (ADR-0023), 8 tables.** `alembic/versions/0002_dimensional_schema.py`
  replaced the original 3-flat-table schema with `desks`/`authors`/
  `platforms`/`ad_slot_types` dimensions and `articles`/
  `article_engagement`/`ad_revenue`/`corrections` facts — engagement and ad
  revenue are both measured per platform now, not just per article, and
  `corrections` tracks the correction/retraction lifecycle already
  described in the knowledge base's SOP. See `semantic/schema.yaml` for
  the full business-meaning writeup the SQL Analytics Tool is grounded
  against.
- Schema covers `articles`, `article_engagement` (page views, unique
  visitors, time on page, per platform), and `ad_revenue` (by ad slot type
  and platform) — reflecting MCN News's digital-first metrics rather than
  TV's daypart/rating model.
- 3 seeded SOPs (see `mcp_servers/tv/CLAUDE.md` for where seeding
  actually lives — [`documents/kb/news/`](../../documents/kb/news/))
  cover the newsroom's editorial lifecycle: fact-checking before
  publication, expedited breaking-news publication, and
  correction/retraction handling.

## Phase-1 simplifications (inherited from the TV template)

Authorization is a minimal role/claim check
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

## `db.py`'s SELECT-only guard also accepts `WITH` (CTE) queries

Same fix as `mcp_servers/tv/CLAUDE.md`'s "Real bug fixed" section - the
guard used to reject any `WITH ... SELECT ...` CTE outright, which the
SQL Analytics Tool's own text-to-SQL step reaches for on any
comparison-style question (WoW/MoM, etc.), failing those **every time**,
not occasionally. See that file for the full writeup; the fix and its
regression test (`tests/test_db.py`) are identical here.
