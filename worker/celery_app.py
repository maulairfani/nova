"""Celery app instance (ADR-0007/0022) — shared by both processes built
from this image: `worker` (the consumer, runs tasks.py's task) and
`ingestion-webhook` (the producer, only ever calls .delay())."""
from celery import Celery

from config import settings

celery_app = Celery("nova_worker", broker=settings.redis_url, backend=settings.redis_url, include=["tasks"])
