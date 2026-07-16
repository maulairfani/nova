"""Writes ingestion metadata to nova_core's `documents` table (ADR-0022).
Schema/migrations are owned by backend/ (ADR-0021) — this is a plain SQL
writer against a table this service doesn't manage the DDL for, using the
same trusted internal credentials as backend's own admin connection."""
import sqlalchemy as sa

from config import settings

_engine = sa.create_engine(settings.core_database_admin_url, pool_pre_ping=True)


def insert_pending(business_unit_code: str, object_key: str, title: str, format_: str) -> str:
    """Get-or-create by (business_unit_code, object_key) - a row may
    already exist here if the backend's upload endpoint pre-created it
    (with a human-provided title) before writing the object to MinIO.
    The legacy direct-MinIO-upload path (no pre-existing row) still works
    unchanged: no row is found, so one is inserted here exactly as
    before, with `title` defaulting to the raw object_key."""
    with _engine.begin() as conn:
        existing = conn.execute(
            sa.text("SELECT id FROM documents WHERE business_unit_code = :business_unit_code AND object_key = :object_key"),
            {"business_unit_code": business_unit_code, "object_key": object_key},
        ).scalar_one_or_none()
        if existing is not None:
            return str(existing)

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


def pre_create(business_unit_code: str, object_key: str, title: str, format_: str) -> None:
    """Registers a human-readable title for a document before it's
    uploaded to MinIO - same mechanism as backend's Manage Documents
    upload endpoint (pre-creating the row so mark_ingested's title != object_key
    check preserves it instead of falling back to the PDF parser's
    filename-only title, see parser.py's _parse_pdf). ON CONFLICT DO
    NOTHING keeps this idempotent to re-run without disturbing a row
    insert_pending or a later re-upload may have already touched."""
    with _engine.begin() as conn:
        conn.execute(
            sa.text(
                """
                INSERT INTO documents (business_unit_code, object_key, title, format, status)
                VALUES (:business_unit_code, :object_key, :title, :format, 'pending')
                ON CONFLICT (business_unit_code, object_key) DO NOTHING
                """
            ),
            {
                "business_unit_code": business_unit_code,
                "object_key": object_key,
                "title": title,
                "format": format_,
            },
        )


def mark_ingested(document_id: str, title: str, chunk_count: int) -> None:
    """Only overwrites `title` with the parser's extracted title when the
    row is still using its object_key placeholder (the legacy path's
    insert_pending default) - a human-provided title (set by the upload
    endpoint before this row was even ingested) is never clobbered."""
    with _engine.begin() as conn:
        conn.execute(
            sa.text(
                """
                UPDATE documents
                SET status = 'ingested',
                    title = CASE WHEN title = object_key THEN :title ELSE title END,
                    chunk_count = :chunk_count, ingested_at = now(), error_message = NULL
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
