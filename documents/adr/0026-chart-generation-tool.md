# ADR-0026: Chart Generation Tool — matplotlib, server-side, on `mcp-shared`

**Status:** Accepted

## Decision

Add a **Chart Generation Tool** (`generate_chart`) that the ReAct agent
calls explicitly, alongside the existing KB Search and SQL Analytics
Tools. It renders a chart with **matplotlib** (headless, `Agg` backend)
from data the agent already has in its own turn context — typically a
prior SQL Analytics Tool result — and stores the PNG in a new MinIO
bucket, `nova-charts`. The tool lives on **`mcp-shared`**, the same
server that already exposes the Web Search Tool, not on any per-business-
unit server. The chat UI shows the image inline when this tool is called,
served through a new authenticated Backend API endpoint
(`GET /api/v1/charts/{chart_id}`), with a download affordance.

## Context

Analytics answers (SQL Analytics Tool results) were text/markdown-table
only — harder to read at a glance than a chart, especially for trends
over time or comparisons across categories/segments. This tool makes
that data easier to read without requiring the frontend to guess at
chart-worthy shapes from raw rows.

## Alternatives Considered

- **A frontend charting library, auto-detecting chart-worthy shapes from
  SQL Analytics Tool rows** (e.g. recharts, rendering client-side): rejected
  — would require heuristics to guess chart type/axes from arbitrary query
  results, is fragile against the many shapes a text-to-SQL result can
  take, and duplicates reasoning the LLM already does when it decides how
  to summarize a query's rows. Keeping the rows→chart transform in the
  agent's own reasoning (it already read the rows to write its answer) is
  more robust than re-deriving chart intent from raw data client-side.
- **One `generate_chart` tool per business unit** (mirroring `kb_search`/
  `sql_analytics`'s per-unit duplication): rejected — chart rendering
  never touches a business unit's Postgres or Qdrant, so there is nothing
  to partition per unit. Tripling identical matplotlib/MinIO code for zero
  data-ownership benefit doesn't fit the reasoning that justified
  per-unit duplication for the other tools in the first place.
- **A `charts` table in `nova_core`** tracking chart metadata (owner,
  business unit, thread) for ACL/listing: deferred, not requested. Unlike
  `Document` (ADR-0022), there's no async ingestion lifecycle to track and
  nothing needs listing per business unit — generation is synchronous
  within the tool call itself (success → a chart_id; failure → an error
  the agent sees directly). Revisit if a "chart history" feature is ever
  wanted.

## Rationale

Placing `generate_chart` on `mcp-shared` follows the exact reasoning that
already placed `web_search` there (ADR-0008's callable-based authorization
still applies unchanged, `check_shared_access`): the capability isn't
owned by any single business unit's data, so it needs the same permissive
"any recognized identity" gate, not a new one.

matplotlib was chosen over a JS charting library specifically because the
agent — not the frontend — is the one deciding what to visualize and how;
a static server-rendered image is the simplest thing that can carry that
decision to the browser. MinIO (already the object store for KB documents,
ADR-0011) is the natural place to put the resulting PNG rather than
inventing a second storage mechanism.

`<img src>` can't carry a JWT and there's no public MinIO exposure in this
app (mirroring how KB documents are served, not linked directly) — so the
frontend fetches the chart as a Blob through a new authenticated endpoint
and renders it via `URL.createObjectURL`, the same technique used for the
Manage Documents PDF preview.

## Consequences

- Positive: reuses the agent's own existing tool-calling reasoning rather
  than adding new frontend inference logic; reuses existing MinIO
  infrastructure rather than a new storage mechanism.
- Positive: matches this project's dual-path discipline for tool-call
  results — a chart shows identically whether the answer just streamed in
  live or was reloaded from a past conversation's history.
- Negative: `mcp-shared` is no longer a "thin wrapper around an external
  search API" (its own `CLAUDE.md`'s prior description) — `matplotlib`
  (+`numpy`) is a materially heavier dependency than anything this server
  has carried before, meaning a larger image and longer build than the
  other three MCP servers.
- Negative: no chart lifecycle or cleanup — `nova-charts` grows unbounded,
  since there's no delete path (no DB row, no "Manage Charts" UI). A MinIO
  bucket lifecycle policy (auto-expire after N days) is a cheap follow-up
  if storage growth becomes a real concern; out of scope for now.
- Negative: chart access is any-authenticated-user, not business-unit-
  scoped, since `chart_id` is just an unguessable MinIO object key with no
  owning-unit record — a deliberate simplification matching `mcp-shared`'s
  existing permissive philosophy, not a business-unit data leak (charts
  carry no more sensitivity than the SQL Analytics Tool answer they were
  generated from, which the caller already had to be authorized to see in
  order to generate).
