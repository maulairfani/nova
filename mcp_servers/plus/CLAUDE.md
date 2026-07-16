# mcp_servers/plus/ — MCN+'s Business Unit MCP Server

FastMCP server (`mcp-plus`) exposing MCN+'s KB Search and SQL Analytics
tools, per TDD §5.2. Covers **both** MCN+ products — OTT streaming and
Shorts (micro-drama) — as one business unit, one MCP server, one database,
one Qdrant collection (ADR-0014). A direct replication of
`mcp_servers/tv/`'s template (see that directory's `CLAUDE.md` for the
original rationale); differences from the template are called out below.

## Structure

Same as `mcp_servers/tv/` — `server.py`, `auth.py`
(`check_plus_access(AuthContext) -> bool`), `db.py`, `tools/`,
`alembic/`, `seed/`.

## MCN+-specific notes

- **Merged schema, `product` column, not two databases.** `titles`,
  `engagement`, and `revenue` all carry a `product` column
  (`'streaming'|'shorts'`) rather than separate tables per product — this
  matches ADR-0014's decision that MCN+ is one data domain with two
  products, not two domains grouped under one label.
- **KB docs cover both products.** The 3 seeded SOPs (see
  `mcp_servers/tv/CLAUDE.md` for where seeding actually lives —
  [`documents/kb/plus/`](../../documents/kb/plus/)) span content
  licensing (both products), streaming subscription billing, and Shorts
  coin purchases — reflecting that one KB Search call can surface either
  product's documentation depending on the question.

## Phase-1 simplifications (inherited from the TV template)

Authorization is a minimal role/claim check
(`ALLOWED_ROLES = {"mcn_plus_employee", "group_admin"}` or `"plus"` in the
caller's business units), against an unverified dummy identity (see
`backend/CLAUDE.md`).

## Verifying changes here independent of the Backend API

Same recipe as `mcp_servers/tv/CLAUDE.md`, against port `9002`:

```bash
docker compose up -d mcp-plus
curl -X POST http://localhost:9002/mcp -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" -H "Mcp-Session-Id: <id>" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"kb_search","arguments":{"query":"..."}}}'
```

Add `-H "X-Nova-Business-Units: plus"` to pass authorization; omit it to
verify the auth check actually denies.
