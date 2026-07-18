# mcp_servers/shared/ — Nova's Shared MCP Server

FastMCP server (`mcp-shared`) exposing the Web Search Tool (TDD §5.2/§6.4),
via Tavily (ADR-0010), and the Chart Generation Tool (TDD §6.6, ADR-0026),
via matplotlib. Unlike `mcp_servers/tv|plus|news/`, this server owns no
database or Qdrant collection — neither tool is scoped to a single
business unit's data. It's no longer just "a thin wrapper around an
external search API" now that chart rendering lives here too (ADR-0026's
Consequences notes this cost explicitly).

## Structure

```
server.py         FastMCP app: registers web_search and generate_chart, both
                behind the same auth check
auth.py           check_shared_access(AuthContext) -> bool
minio_client.py    get_client()/ensure_bucket() - a small per-service MinIO
                client duplicate (ADR-0022's "no shared code across
                independently-deployable services" rationale), used only
                by generate_chart to write the rendered PNG
tools/
  web_search.py      Calls Tavily, normalizes the response shape
  generate_chart.py  Renders a matplotlib chart (bar/line/pie) from data
                    the agent already has, uploads the PNG to the
                    nova-charts MinIO bucket (ADR-0026)
```

## Why this server has no per-unit ownership

Web search results and chart rendering aren't scoped to any business
unit's data, so there's nothing here to partition the way
`mcp_servers/<unit>/` partitions Postgres/Qdrant per unit.
`check_shared_access` is intentionally permissive — any caller with a
recognized MCN Group identity (claims at least one business unit, or an
admin role) may use either tool. This mirrors the *shape* of ADR-0008's
callable-based authorization (every MCP server has one), even though the
rule itself has nothing meaningful to restrict.

## Chart Generation Tool (ADR-0026)

`generate_chart(title, chart_type, labels, series, x_label, y_label)` —
the agent calls this explicitly (typically right after a `*_sql_analytics`
result in the same turn) with data it already has; it never reads from
any business unit's database itself. Renders via matplotlib
(`matplotlib.use("Agg")` - headless, no display server) using a fixed,
validated-for-colorblind-safety categorical color order (never reordered
or cycled per series), uploads the PNG to the `nova-charts` bucket keyed
by a random UUID, and returns just `{chart_id, title, chart_type}` - the
image bytes themselves never pass through the LLM's context. The Backend
API's Chart Endpoint (`GET /api/v1/charts/{chart_id}`, `backend/app/api/v1/endpoints/charts.py`)
streams the image back to the frontend on request; any authenticated
caller may fetch any chart_id, since charts carry no more sensitivity than
the analytics answer they were generated from (see ADR-0026's
Consequences for the reasoning).

`nova-charts` is created by `worker/bootstrap_buckets.py` alongside the
three KB buckets, but deliberately **not** subscribed to the ingestion
webhook - charts aren't documents to parse/embed.

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

For `generate_chart` specifically, `tests/test_generate_chart.py` mocks
`minio_client.get_client`/`ensure_bucket` (no live MinIO in CI's
`test-mcp-servers` job) and covers valid bar/line/pie inputs plus each
validation error path (empty series, mismatched labels/values length, a
pie chart with more than one series, an unsupported chart_type). For a
real end-to-end check against live MinIO, call the function directly
inside the running container (`docker compose exec mcp-shared python -c
"..."`) and fetch the resulting object back through the Backend API's
Chart Endpoint to confirm the full path, not just the render step.
