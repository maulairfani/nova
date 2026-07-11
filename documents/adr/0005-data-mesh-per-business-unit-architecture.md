# ADR-0005: Data Mesh — Per-Business-Unit MCP Servers and Databases

**Status:** Accepted (supersedes an earlier single-consolidated-warehouse
design used in early drafts of Sections 3-5)

## Decision

Reject a single, consolidated analytics warehouse and a single shared MCP
server. Instead, adopt a
[Data Mesh](https://martinfowler.com/articles/data-monolith-to-mesh.html)
architecture: each business unit (MCN TV, MCN+, MCN+ Shorts, MCN News) owns
and serves its own analytics data and knowledge base documents, exposed
through its own dedicated MCP server. Cross-business-unit questions are
answered by the agent calling multiple business units' MCP servers and
synthesizing the results at query time (Section 6.3), rather than a
pre-joined query against one warehouse.

## Context

The initial design (Sections 3-5, early drafts) assumed MCN Group already
had one consolidated analytics warehouse — a plausible simplification, and
a common real-world pattern (a Data Engineering function ETLs per-unit data
into one SSOT). During design review, this was reconsidered: realistically,
each business unit's data is genuinely distinct in ownership, schema, and
sensitivity (e.g. MCN News has embargo/editorial constraints, MCN+ has
subscriber PII, MCN TV has ad revenue figures relevant mainly to Finance)
— and centralizing it all behind one MCP server also centralizes
authorization logic that should differ per unit (Section 8).

## Alternatives Considered

- **Single consolidated warehouse + single MCP server** (the original
  design). Simpler: one database, one MCP server, trivial cross-unit
  queries (a single SQL join). Rejected because: (1) it assumes an ETL/
  consolidation process that doesn't actually exist in this scope — we'd
  be modeling infrastructure MCN Group doesn't have, rather than what each
  business unit realistically owns; (2) it creates a single point of
  failure across all business units simultaneously (directly conflicts
  with the Reliability quality goal, Section 1.2); (3) it forces one-size-
  fits-all authorization logic, when business units realistically need
  different rules.
- **Per-business-unit databases, but still one shared MCP server** (a
  middle ground). Rejected because the MCP server would still need to
  implement per-unit authorization logic internally via conditionals,
  rather than each unit owning its own authorization implementation — this
  keeps the "federated governance" principle only half-applied, and the
  shared MCP server becomes a growing pile of per-unit special cases as
  more units are added (contradicts Maintainability, Section 1.2).

## Rationale

Data Mesh's four principles map directly onto this decision:
domain-oriented decentralized ownership (each business unit owns its data),
data as a product (each unit's MCP server is that product's serving
interface), a self-serve data platform (Qdrant, MinIO, Redis, the async
worker remain shared infrastructure — Section 4 — rather than each unit
reinventing its own), and federated computational governance (a shared
layer decides which units an employee can reach; each unit decides its own
detailed access rules, Section 8). This is a more accurate model of how a
multi-business-unit media conglomerate the size of MCN Group actually
assigns data ownership, and it directly serves the Reliability goal: one
business unit's outage no longer takes down every other unit's Nova
capability.

## Consequences

- Positive: better failure isolation (Reliability); authorization rules can
  genuinely differ per business unit without special-casing a shared
  server; adding a 5th business unit later means replicating an existing
  template, not modifying shared code (Maintainability).
- Negative: significantly more operational surface — 4 MCP servers and 4
  PostgreSQL instances instead of 1 of each — for a small Platform/
  Engineering team (Section 2 constraint) to run and monitor. Recorded as
  an accepted risk in Section 11.
- Negative: cross-business-unit questions (Section 6.3) are now answered
  by the agent synthesizing multiple tool results at runtime instead of
  one pre-joined SQL query. This shifts risk onto the agent's reasoning
  correctness — a wrong synthesis threatens the Groundedness/Accuracy goal
  more directly than a warehouse-level JOIN would. Recorded as an accepted
  risk in Section 11, to be mitigated by careful prompt design and
  evaluation (future work).
