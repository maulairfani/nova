"""Receives MinIO's bucket-notification webhook (ADR-0022) and enqueues a
Celery task per uploaded object. A lightweight Celery *producer* only —
the actual parse/chunk/embed work happens in tasks.py's consumer
(a separate `worker` process/service, same image)."""
import logging

from fastapi import FastAPI, Request

from tasks import ingest_document

logger = logging.getLogger(__name__)
app = FastAPI(title="Nova Ingestion Webhook")

_BUCKET_TO_BUSINESS_UNIT = {"mcn-tv": "tv", "mcn-plus": "plus", "mcn-news": "news"}


@app.post("/webhook")
async def minio_webhook(request: Request):
    payload = await request.json()
    for record in payload.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        object_key = record["s3"]["object"]["key"]
        business_unit = _BUCKET_TO_BUSINESS_UNIT.get(bucket)
        if business_unit is None:
            logger.warning("Ignoring event for unrecognized bucket %r", bucket)
            continue
        ingest_document.delay(business_unit, object_key)
        logger.info("Enqueued ingestion for %s/%s", business_unit, object_key)
    return {"status": "ok"}


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
