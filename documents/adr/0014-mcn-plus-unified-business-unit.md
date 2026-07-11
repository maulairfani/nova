# ADR-0014: MCN+ Streaming and Shorts as One Unified Business Unit

**Status:** Accepted (amends ADR-0005's business-unit list)

## Decision

MCN+ (OTT streaming) and MCN+ Shorts (micro-drama, vertical short-form
video) are **one business unit — "MCN+"** — offering two products, not two
separate business units. They share a single Data Mesh domain: one MCP
server (`mcp-plus`), one PostgreSQL database (`postgres-plus`), one Qdrant
collection (`mcn_plus`), one MinIO bucket. **Nova's total business-unit
count is 3** (MCN TV, MCN+, MCN News), not 4, everywhere this document set
previously said "×4."

## Context

The original company profile and TDD (Sections 1.3, 3.1, 4, 5, 7, 10, 11)
and ADR-0005 modeled MCN+ and MCN+ Shorts as two independent business units,
each getting its own MCP server and database under the Data Mesh
architecture. This surfaced as inaccurate during Q2 implementation
planning, before any code was written: MCN+ (streaming) and MCN+ Shorts sit
under one director/P&L, not two, and the two products share subscriber and
content-licensing operations closely enough that they are one data-owning
domain, not two.

## Alternatives Considered

- **Keep them as 2 separate MCP servers/databases, grouped only
  organizationally under one label.** Rejected: Data Mesh's domain boundary
  (ADR-0005) is meant to track *actual data ownership*, not organizational
  labeling. Since streaming and shorts data is genuinely owned by one team
  as one domain, splitting it into two MCP servers/databases would be an
  artifact of the original (incorrect) business-unit count, not a reflection
  of real ownership — the opposite of what ADR-0005 argues for.

## Rationale

Data Mesh's domain-oriented ownership principle means the mesh boundary
should match who owns and serves the data, not how many end-user apps or
products exist. MCN+ leadership owns both products' data as a single
domain, so one MCP server and one database is the accurate model. This
also reduces operational surface (3 MCP servers/databases instead of 4)
without weakening the Data Mesh rationale itself — the boundary is now
drawn correctly rather than removed.

## Consequences

- Positive: fewer moving parts — 3 MCP servers and 3 PostgreSQL instances
  instead of 4, for the same small Platform/Engineering team constraint
  (Section 2) ADR-0005 already worries about.
- Positive: the Data Mesh boundary now matches real organizational data
  ownership more accurately than the original ×4 model did.
- Negative: `postgres-plus` needs separate tables/schemas per product
  internally (e.g. `streaming_subscribers`, `shorts_coin_purchases`) since
  the two products' metrics differ substantially (subscription/churn vs.
  coin-purchase/episode-unlock) — the MCP server's SQL Analytics Tool must
  know which tables serve which product.
- Negative: the `mcn_plus` Qdrant collection holds KB documents from both
  products, distinguished by payload metadata (e.g. `product: "streaming" |
  "shorts"`) — the KB Search Tool should support filtering by product when
  a question is clearly scoped to one, to avoid cross-product noise in
  retrieval.
- This ADR amends ADR-0005's Decision text (business-unit list and ×4
  references) rather than silently editing it — ADR-0005's own Status line
  now points here.
