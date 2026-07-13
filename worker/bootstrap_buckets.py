"""One-off setup: creates each business unit's MinIO bucket and subscribes
it to the "INGEST" webhook notification target (configured via MinIO's own
MINIO_NOTIFY_WEBHOOK_* env vars, docker-compose.yaml) so uploads actually
trigger ingestion (ADR-0022). Idempotent — safe to re-run.

Usage: python bootstrap_buckets.py
"""
from minio.notificationconfig import NotificationConfig, QueueConfig

from minio_client import ensure_bucket, get_client

_BUCKETS = ["mcn-tv", "mcn-plus", "mcn-news"]


def bootstrap() -> None:
    client = get_client()
    for bucket in _BUCKETS:
        ensure_bucket(client, bucket)
        client.set_bucket_notification(
            bucket,
            NotificationConfig(
                queue_config_list=[
                    QueueConfig(
                        events=["s3:ObjectCreated:*"],
                        config_id=f"{bucket}-ingest",
                        queue="arn:minio:sqs::INGEST:webhook",
                    ),
                ],
            ),
        )
        print(f"{bucket}: bucket ready, subscribed to INGEST webhook")


if __name__ == "__main__":
    bootstrap()
