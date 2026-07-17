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
`alembic/`, `semantic/schema.yaml`. Dummy analytics data is seeded from
the root-level `SEED_DATA/` (ADR-0025), not a local `seed/` directory.

## MCN+-specific notes

- **Dimensional schema (ADR-0023), 15 tables.** `alembic/versions/0002_dimensional_schema.py`
  replaced the original 3-flat-table schema with `titles`/`seasons`/`episodes`
  (shared across both products), `subscription_plans`/`subscriptions`/
  `subscription_transactions` (streaming-only monetization),
  `coin_packages`/`coin_transactions` (shorts-only monetization),
  `subscribers`/`devices`/`regions`/`licensors`/`content_licensing_costs`,
  and a `revenue` daily rollup — see `semantic/schema.yaml` for the full
  business-meaning writeup the SQL Analytics Tool is grounded against.
- **Merged schema, `product` column, not two databases.** `titles`,
  `engagement`, and `revenue` all carry a `product` column
  (`'streaming'|'shorts'`) rather than separate tables per product — this
  matches ADR-0014's decision that MCN+ is one data domain with two
  products, not two domains grouped under one label. Monetization is
  still deliberately split into two separate fact tables
  (`subscription_transactions` vs. `coin_transactions`), since they're
  genuinely different business models, not two variants of one.
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
