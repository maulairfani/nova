"""One-off setup: creates each business unit's MinIO bucket and subscribes
it to the "INGEST" webhook notification target (configured via MinIO's own
MINIO_NOTIFY_WEBHOOK_* env vars, docker-compose.yaml) so uploads actually
trigger ingestion (ADR-0022). Idempotent — safe to re-run.

Usage: python bootstrap_buckets.py
"""
from minio.notificationconfig import NotificationConfig, QueueConfig

from minio_client import ensure_bucket, get_client

_BUCKETS = ["mcn-tv", "mcn-plus", "mcn-news"]

# Chart Generation Tool's output bucket (ADR-0026) - not a KB document
# source, so it's created but never subscribed to the ingestion webhook.
_CHARTS_BUCKET = "nova-charts"


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

    ensure_bucket(client, _CHARTS_BUCKET)
    print(f"{_CHARTS_BUCKET}: bucket ready (not subscribed to ingestion - not a KB source)")


if __name__ == "__main__":
    bootstrap()
