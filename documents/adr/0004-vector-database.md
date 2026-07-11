# ADR-0004: Vector Database — Qdrant

**Status:** Accepted

## Decision

Use **Qdrant** as the vector store for knowledge base embeddings, as a
single shared deployment logically partitioned into one collection per
business unit (Section 4).

## Context

The knowledge base needs a vector store for RAG retrieval. This isn't
mandated by the test brief — it's an open choice, so it was picked for
efficiency and fit rather than convenience or default. Since PostgreSQL is
already in the stack (ADR-0003), pgvector was the natural default to
evaluate first, alongside dedicated vector databases.

## Alternatives Considered

- **pgvector** — reuses the existing PostgreSQL investment (Maintainability
  goal, no new technology surface); handles RAG comfortably up to ~10M
  vectors. Research showed this comfortably covers Nova's actual scale
  (per-business-unit knowledge bases of internal SOPs/documentation — well
  under that ceiling).
- **Weaviate** — strong hybrid search and built-in vectorization modules,
  but adds more operational surface than needed here.
- **Milvus** — built for billion-scale search; community consensus flags it
  as overkill under ~50M vectors, which doesn't match Nova's scale at all.
- **Chroma** — good for prototyping, but trails Qdrant/Weaviate for
  production workloads.

## Rationale

At Nova's actual scale, pgvector would have been the more
Maintainability-aligned choice (per Section 1.2, avoiding new technology
surface for a small team). Qdrant was chosen instead — written in Rust,
offering the best self-hosted price-performance among dedicated vector
databases, with strong metadata filtering (useful for per-business-unit
collection scoping and future filtered retrieval) and native hybrid
search, which pgvector doesn't offer natively. This is a deliberate
trade-off: slightly more operational surface than pgvector, in exchange
for retrieval quality/filtering headroom as the knowledge base grows.

## Consequences

- Positive: best-in-class self-hosted vector search performance and
  filtering; clean separation between relational and vector concerns.
- Negative: introduces a technology beyond the already-adopted PostgreSQL,
  which pgvector would have avoided — accepted as a conscious trade-off
  rather than the Maintainability-optimal default.
