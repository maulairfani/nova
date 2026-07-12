# mcp_servers/shared/ — Nova's Shared MCP Server

FastMCP server (`mcp-shared`) exposing the Web Search Tool (TDD §5.2/§6.4),
via Tavily (ADR-0010). Unlike `mcp_servers/tv|plus|news/`, this server owns
no database or Qdrant collection — it's a thin wrapper around an external
search API, used as a fallback when internal sources (KB, business unit
data) don't have the answer.

## Structure

```
server.py       FastMCP app: registers the web_search tool behind the auth check
auth.py         check_shared_access(AuthContext) -> bool
tools/
  web_search.py   Calls Tavily, normalizes the response shape
```

## Why this server has no per-unit ownership

Web search results aren't scoped to any business unit's data, so there's
nothing here to partition the way `mcp_servers/<unit>/` partitions
Postgres/Qdrant per unit. `check_shared_access` is intentionally permissive
— any caller with a recognized MCN Group identity (claims at least one
business unit, or an admin role) may use it. This mirrors the *shape* of
ADR-0008's callable-based authorization (every MCP server has one), even
though the rule itself has nothing meaningful to restrict.

## Phase-1 simplification: dummy authorization

Same as the business unit servers — identity comes from a forwarded,
unverified header (see `backend/CLAUDE.md`), not a real auth system.

## Verifying changes here independent of the Backend API

```bash
docker compose up -d mcp-shared
curl -X POST http://localhost:9004/mcp -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" -H "Mcp-Session-Id: <id>" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"web_search","arguments":{"query":"..."}}}'
```

Add `-H "X-Nova-Business-Units: tv"` (or any real unit) to pass
authorization; omit both that header and any role header to verify the
auth check actually denies.
