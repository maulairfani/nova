# ADR-0003: Relational Database — PostgreSQL

**Status:** Accepted

## Decision

Use **PostgreSQL** for all relational data: each business unit's analytics
data, and the shared `nova_kb` instance (conversation state).

## Context

Nova needs a relational store for structured analytics data (per business
unit, per the Data Mesh decision, ADR-0005) and for its own operational
state (conversation history via LangGraph's checkpointer, ADR-0012).
Section 2 prefers open-source/self-hosted tooling.

## Alternatives Considered

- **MySQL/MariaDB** — viable, but PostgreSQL has stronger support for
  advanced querying (window functions, CTEs) that a text-to-SQL analytics
  tool is likely to generate, and better native JSON support for
  semi-structured metadata.
- **Managed cloud databases (RDS, Cloud SQL, etc.)** — reduces ops burden,
  but conflicts with the "prefer self-hosted, avoid recurring managed-
  service cost" organizational constraint (Section 2) at this stage.

## Rationale

PostgreSQL is mature, open-source, well-understood by the team, has a
first-class LangGraph Postgres checkpointer integration (avoiding a
separate store for conversation history), and its SQL dialect is
well-represented in LLM training data — helping the text-to-SQL tool
generate correct queries (Groundedness/Accuracy goal, Section 1.2).

## Consequences

- Positive: one well-understood technology for all relational needs across
  every business unit and shared services; strong LangGraph integration.
- Negative: running one PostgreSQL instance per business unit (ADR-0005)
  multiplies operational surface compared to a single consolidated
  database — accepted trade-off, discussed in ADR-0005 and Section 11.
