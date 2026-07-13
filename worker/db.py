"""Writes ingestion metadata to nova_core's `documents` table (ADR-0022).
Schema/migrations are owned by backend/ (ADR-0021) — this is a plain SQL
writer against a table this service doesn't manage the DDL for, using the
same trusted internal credentials as backend's own admin connection."""
import sqlalchemy as sa

from config import settings

_engine = sa.create_engine(settings.core_database_admin_url, pool_pre_ping=True)


def insert_pending(business_unit_code: str, object_key: str, title: str, format_: str) -> str:
    with _engine.begin() as conn:
        result = conn.execute(
            sa.text(
                """
                INSERT INTO documents (business_unit_code, object_key, title, format, status)
                VALUES (:business_unit_code, :object_key, :title, :format, 'pending')
                RETURNING id
                """
            ),
            {
                "business_unit_code": business_unit_code,
                "object_key": object_key,
                "title": title,
                "format": format_,
            },
        )
        return str(result.scalar_one())


def mark_ingested(document_id: str, title: str, chunk_count: int) -> None:
    with _engine.begin() as conn:
        conn.execute(
            sa.text(
                """
                UPDATE documents
                SET status = 'ingested', title = :title, chunk_count = :chunk_count, ingested_at = now()
                WHERE id = :id
                """
            ),
            {"title": title, "chunk_count": chunk_count, "id": document_id},
        )


def mark_failed(document_id: str, error_message: str) -> None:
    with _engine.begin() as conn:
        conn.execute(
            sa.text("UPDATE documents SET status = 'failed', error_message = :error_message WHERE id = :id"),
            {"error_message": error_message[:2000], "id": document_id},
        )
