"""Chart Endpoint business logic (ADR-0026) - streams a chart image the
Chart Generation Tool (mcp-shared) rendered and uploaded to MinIO.
app/api/v1/endpoints/charts.py stays a thin HTTP adapter around this."""
import uuid

from fastapi import HTTPException
from minio.error import S3Error

from app.core.storage import CHARTS_BUCKET, get_minio_client


def get_chart_stream(chart_id: uuid.UUID):
    """Returns a byte stream for the chart's PNG content. Raises
    HTTPException(404) if it doesn't exist."""
    minio = get_minio_client()
    try:
        response = minio.get_object(CHARTS_BUCKET, f"{chart_id}.png")
    except S3Error:
        raise HTTPException(status_code=404, detail="Chart not found.")

    def stream():
        try:
            yield from response.stream(32 * 1024)
        finally:
            response.close()
            response.release_conn()

    return stream()
