"""MinIO connection for the Chart Generation Tool (ADR-0026) - a small
per-service duplicate of worker/minio_client.py's shape, per ADR-0022's
"no shared code across independently-deployable services" rationale."""
from minio import Minio

from config import settings


def get_client() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket(client: Minio, bucket: str) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
