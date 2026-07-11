# ADR-0007: Async Worker / Queue — Celery (with Redis as broker)

**Status:** Accepted

## Decision

Use **Celery** as the async worker framework, with Redis (ADR-0006) as the
broker, for the document ingestion pipeline (Section 6.5).

## Context

Ingesting documents (parse, chunk, embed, write to Qdrant/`nova_kb`) must
run outside the live request path (Section 1.2 Performance Efficiency
goal), triggered per business unit whenever a document changes.

## Alternatives Considered

- **arq** — lighter-weight, async-native (fits FastAPI's async style more
  naturally than Celery's traditionally sync worker model), smaller
  dependency footprint.
- **Running ingestion synchronously in the Backend API** — rejected outright:
  would block live chat requests during ingestion, directly violating the
  Performance Efficiency and Reliability goals.

## Rationale

Celery was chosen over arq for its maturity and ecosystem — broader
documentation, more production track record, and built-in support for
retries, scheduling, and task routing, which matters once ingestion needs
to run per business unit with independent failure handling (so one
business unit's ingestion failure doesn't affect another's, consistent
with the Data Mesh isolation principle, ADR-0005). arq remains a reasonable
lighter-weight alternative if operational simplicity turns out to matter
more than Celery's feature set in practice.

## Consequences

- Positive: mature retry/failure-handling semantics; well-documented
  patterns for isolating per-business-unit ingestion jobs.
- Negative: Celery's sync worker model is a slight mismatch with the rest
  of the stack's async-first style (FastAPI, async Qdrant/Postgres
  clients) — manageable, but a small ongoing friction accepted for the
  maturity trade-off.
