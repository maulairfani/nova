# worker/ — Nova's Document Ingestion Pipeline

Implements TDD §6.5 (ADR-0007 Celery, ADR-0011 MinIO, ADR-0022 the overall
architecture). Read `documents/adr/0022-document-ingestion-pipeline.md`
before making non-trivial changes here.

## Structure

One codebase/image, two processes (split by Docker Compose `command:`):

```
celery_app.py        Celery app instance (broker=Redis, ADR-0007)
webhook.py            FastAPI producer — MinIO's webhook POSTs here, enqueues a task
tasks.py              Celery consumer — the actual ingest_document task
parser.py             Markdown (header-split) + PDF (paragraph-grouped) chunking
embeddings.py          OpenRouter client — deliberate duplicate of
                      mcp_servers/common/embeddings.py, not a shared import (ADR-0022)
qdrant_helper.py        Same duplication reasoning, mirrors mcp_servers/common/qdrant_client.py
minio_client.py         MinIO connection + object download/bucket helpers
db.py                  Writes to nova_core's `documents` table (schema owned by backend/, ADR-0021)
bootstrap_buckets.py    One-off setup: creates buckets, subscribes them to the webhook target
seed_documents.py        One-off dev seed: uploads documents/kb/<unit>/* (repo root) into each
                        unit's bucket - the real ingestion path, not a Qdrant shortcut (below)
```

## How a document actually gets ingested

1. Something uploads a file to one of the 3 buckets (`mcn-tv`,
   `mcn-plus`, `mcn-news`) - a human via the MinIO console
   (`localhost:9011`), a script, or (the real product path now)
   `backend/`'s Manage Documents endpoint (`backend/app/api/v1/endpoints/documents.py`),
   which also pre-creates the `documents` row itself with a caller-chosen
   title before writing the object, unlike the other two.
2. MinIO's `INGEST` webhook notification target (configured via
   `MINIO_NOTIFY_WEBHOOK_*` env vars on the `minio` service,
   `docker-compose.yaml`) POSTs an `s3:ObjectCreated:*` event to
   `ingestion-webhook`.
3. `webhook.py` extracts `(business_unit, object_key)` from the event and
   calls `ingest_document.delay(...)` — a Celery producer call, not the
   actual work.
4. The `worker` service (a separate container, same image, running
   `celery -A celery_app worker`) picks up the task: downloads the object
   from MinIO, parses it (`parser.py`), embeds each chunk, upserts into
   that business unit's Qdrant collection, and writes/updates a row in
   `documents` (`pending` → `ingested`/`failed`).

`db.py`'s `insert_pending` is a **get-or-create** by
`(business_unit_code, object_key)` (unique constraint, backend/'s
migration `0004`), not a blind insert — if the Manage Documents endpoint
already created the row (with a human-provided title) before the object
landed in MinIO, this just returns that row's id instead of inserting a
duplicate. `mark_ingested` only overwrites `title` with the parser's
extracted title when the row's title still equals its `object_key`
placeholder — a human-provided title from the upload endpoint is never
clobbered by the parsed one. Uploads that don't go through the backend
endpoint (MinIO console, `seed_documents.py`) are unaffected: no row
exists yet, so `insert_pending` creates one exactly as before, and its
placeholder title still gets replaced by the parsed title on success.
`mark_ingested` also clears any `error_message` left over from a prior
failed attempt — found missing when seeding surfaced a real retry (a
document that failed once and later succeeded still showed a stale error
in Manage Documents despite `status: ingested`).

`qdrant_helper.py`'s `ensure_collection` catches a `409 Conflict` from
`create_collection` rather than letting it crash the task —
`collection_exists` → `create_collection` isn't atomic, so two Celery
tasks for the same unit's not-yet-created collection (Celery's default
prefork concurrency; `seed_documents.py` enqueues 3 documents per unit at
once) can race, and the loser hitting Qdrant's "already exists" error is
exactly the outcome `ensure_collection` wants, not a real failure.

## One-off setup (first run only)

MinIO's env vars configure the webhook *target*, but each *bucket* still
needs an explicit subscription — not something env vars alone can do:

```bash
docker compose run --rm worker python bootstrap_buckets.py
```

## Seeding dummy KB documents (first run only, or after wiping volumes)

There's no direct-to-Qdrant shortcut anymore — `mcp_servers/tv/`'s old
`seed/seed_qdrant.py` (and its `plus`/`news` equivalents) were retired
once this real pipeline existed, per that decision's own note that it
should be retired, not kept alongside it. The project's dummy SOP docs
now live at `documents/kb/<unit>/` (repo root, shared across units, not
duplicated per-server) — `seed_documents.py` uploads them into each
unit's bucket, the same real path any other upload takes:

```bash
docker compose run --rm -v "$PWD/documents/kb:/kb:ro" worker python seed_documents.py
```

Requires `bootstrap_buckets.py` (above) and backend/'s `alembic upgrade
head` (creates the `documents` table) to have already run. Re-running is
safe (`fput_object` overwrites by key, `insert_pending`'s get-or-create
avoids duplicate rows) — most of the seeded docs are PDF, one Markdown
file per unit, to exercise both parser paths (`parser.py`) with real
content rather than only ever testing the Markdown path.

## Verifying changes here independent of the full webhook flow

Skip MinIO's webhook entirely and enqueue a task directly — this isolates
whether the *task* itself works from whether the *webhook wiring* works:

```bash
docker compose run --rm worker python -c "
from tasks import ingest_document
ingest_document.delay('tv', 'some-object-key.md')
"
docker compose logs -f worker
```

To test the webhook path end-to-end, upload a file via the MinIO console
(`http://localhost:9011`, credentials `MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY`)
to one of the 3 buckets, then check `docker compose logs ingestion-webhook
worker` and query `documents` in `nova_core` for the resulting row.

## Why this duplicates mcp_servers/common/ instead of importing it

`mcp_servers/common/` is explicitly scoped to Business Unit MCP Servers
(its own `CLAUDE.md`). `worker/` is a different kind of service entirely —
importing across that boundary would couple this service's Docker build
context to `mcp_servers/` for no real benefit; the duplicated files
(`embeddings.py`, `qdrant_helper.py`) are a handful of lines each. Same
precedent as `mcp_servers/plus`/`news` deliberately replicating `tv`'s
template rather than sharing code prematurely.

## Why worker/ uses the same trusted credentials as backend's Alembic connection

`worker/` only ever runs one fixed, developer-written `INSERT`/`UPDATE`
against `documents` (`db.py`) — never an untrusted or LLM-generated query.
That's a fundamentally different threat model from the SQL Analytics
Tool's scoped `mcn_<unit>_readonly` role (which exists specifically to
contain arbitrary LLM-generated `SELECT`s), so the same role-scoping
ceremony isn't warranted here (see ADR-0022's Alternatives Considered).
