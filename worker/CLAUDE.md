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
```

## How a document actually gets ingested

1. Something (a human via the MinIO console at `localhost:9011`, or a
   script) uploads a file to one of the 3 buckets (`mcn-tv`, `mcn-plus`,
   `mcn-news`).
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

## One-off setup (first run only)

MinIO's env vars configure the webhook *target*, but each *bucket* still
needs an explicit subscription — not something env vars alone can do:

```bash
docker compose run --rm worker python bootstrap_buckets.py
```

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
