# ADR-0022: Document Ingestion Pipeline — MinIO Webhook + Celery Worker

**Status:** Accepted

## Decision

Implement TDD §6.5's ingestion pipeline as designed (ADR-0007 Celery,
ADR-0011 MinIO), triggered by **real MinIO bucket-notification webhooks**
(not a manual/polling trigger):

- **MinIO**: one shared deployment, one bucket per business unit
  (`mcn-tv`, `mcn-plus`, `mcn-news`), each configured to POST an
  `s3:ObjectCreated:*` event to an HTTP endpoint on upload.
- **`worker/`** (new top-level directory, sibling to `backend/`/`frontend/`):
  two processes built from the same codebase/image, split by Docker Compose
  `command:` override:
  - **`ingestion-webhook`** — a small FastAPI app receiving MinIO's webhook
    POST, extracting `(business_unit, object_key)` from the event payload,
    and enqueuing a Celery task (`ingest_document.delay(...)`) — a
    lightweight Celery *producer*, not a consumer.
  - **`worker`** — the Celery *consumer*: downloads the document from
    MinIO, parses it (Markdown or PDF), chunks it, embeds each chunk
    (OpenRouter, same model as query-time KB Search — ADR-0015), upserts
    into that business unit's Qdrant collection, and writes a metadata row
    to a new `documents` table in `nova_core`.
- **`documents` table** (`nova_core`, owned by `backend/`'s existing
  Alembic setup — ADR-0021 — written to by `worker/` using the same
  trusted internal credentials, not a scoped read-only role): `id`,
  `business_unit_code`, `object_key`, `title`, `format`
  (`markdown`/`pdf`), `status` (`pending`/`ingested`/`failed`),
  `chunk_count`, `error_message`, `created_at`, `ingested_at`.

## Context

Every business unit currently bypasses the designed ingestion pipeline
entirely: `mcp_servers/<unit>/seed/seed_qdrant.py` reads 3 committed dummy
Markdown files directly off disk and embeds them straight into Qdrant,
explicitly documented as a stand-in "to be retired, not extended" once the
real pipeline exists (`mcp_servers/tv/CLAUDE.md`). This ADR builds that
real pipeline; the seed scripts are left in place for now as a fast local
bootstrap path (unaffected — this is an additive, parallel path), not
retired in this pass.

## Alternatives Considered

- **Polling** (worker periodically lists each bucket, diffs against
  `documents`, ingests anything new): rejected — adds latency
  (document isn't searchable until the next poll), and reinvents diffing
  logic MinIO's own event system already provides for free.
- **A manual trigger endpoint** (e.g. `POST /api/v1/ingest` that a human
  or script calls after uploading): rejected in favor of the real MinIO
  webhook — a manual trigger is an extra step a real content-management
  workflow would have to remember to call, whereas a webhook fires
  automatically the moment a document actually lands in the bucket,
  which is what TDD §6.5's "New/changed document triggers an ingestion
  job" already specifies.
- **MinIO's Redis notification target directly** (publish the raw S3
  event straight to Redis, no separate webhook receiver): rejected — the
  raw event isn't in Celery's task-envelope format, so a bridging
  consumer would still be needed to translate it into a real
  `ingest_document.delay(...)` call; a small FastAPI webhook receiver
  that does exactly that is simpler to reason about than a bespoke
  Redis-message-format bridge.
- **Worker imports `mcp_servers/common/`'s embeddings/Qdrant helpers**:
  rejected — `common/` is scoped specifically to Business Unit MCP
  Servers (its own `CLAUDE.md`), and importing across that boundary would
  couple `worker/`'s Docker build context to `mcp_servers/` unnecessarily.
  `worker/` gets its own small embeddings client instead — a few lines,
  not worth a cross-service dependency to avoid duplicating.
- **A scoped read-only-style role for `worker/`'s Postgres access**
  (mirroring each business unit's `mcn_<unit>_readonly` role): rejected —
  that pattern exists specifically because the SQL Analytics Tool executes
  arbitrary LLM-generated `SELECT` queries against untrusted input
  (a real threat model). `worker/` only ever runs one fixed,
  developer-written `INSERT`/`UPDATE` against `documents` — a genuinely
  different, much lower-risk threat model that doesn't warrant the same
  role-scoping ceremony.

## Rationale

A real webhook keeps the pipeline actually async and event-driven, matching
TDD §6.5's design intent (and the Performance Efficiency goal — ingestion
must never block a live chat request) rather than a synchronous or
polling stand-in. Splitting the webhook receiver (producer) from the
Celery worker (consumer) into two processes/services from one codebase is
a standard Celery pattern: the producer only needs to be reachable enough
to enqueue a task quickly (so MinIO's webhook doesn't time out), while the
actual parse/chunk/embed work — the slow part — happens in the consumer,
independently scalable and retryable per Celery's built-in semantics
(ADR-0007's stated rationale for choosing Celery over arq).

## Consequences

- Positive: documents become searchable automatically on upload, no manual
  step to remember — the real behavior TDD §6.5 was designed for, not a
  demo simplification.
- Positive: `documents` gives an operator visibility into ingestion
  failures (`status`/`error_message`) per business unit, without needing
  to check worker logs.
- Negative: MinIO's webhook configuration (`mc admin config set` or
  `MINIO_NOTIFY_WEBHOOK_*` env vars) is one more piece of one-time,
  manual infrastructure setup per environment (local dev and the VM),
  documented in `worker/CLAUDE.md` and the root README rather than
  automated — consistent with this project's existing treatment of other
  one-time setup steps (migrations, seeding).
- Negative: two new long-running services (`worker`, `ingestion-webhook`)
  plus MinIO itself add real operational surface — accepted, since this is
  the actual bonus-checklist component (Async Worker/Message Queue) and
  was always going to cost this regardless of trigger mechanism chosen.
- Negative: `worker/`'s own embeddings client duplicates
  `mcp_servers/common/embeddings.py` almost verbatim — accepted per this
  project's existing precedent (`mcp_servers/plus`/`news` deliberately
  replicate `tv`'s template rather than share code prematurely across
  different kinds of services).
