"""MinIO connection for the Manage Documents upload/delete endpoints
(app/api/v1/endpoints/documents.py) - a deliberate small duplicate of
worker/minio_client.py's bucket naming (see ADR-0022's Alternatives
Considered on why worker/ doesn't share code with sibling services)."""
from minio import Minio

from app.core.config import settings

BUCKETS = {"tv": "mcn-tv", "plus": "mcn-plus", "news": "mcn-news"}

# Chart Generation Tool's output bucket (ADR-0026) - written by mcp-shared,
# read here for the Chart Endpoint (charts.py).
CHARTS_BUCKET = "nova-charts"


def get_minio_client() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )
