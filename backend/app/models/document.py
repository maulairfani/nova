import uuid

from sqlalchemy import ForeignKey, Integer, Text, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Document(Base):
    """Ingestion pipeline metadata (ADR-0022) - written by worker/, not
    backend/, but the schema/migrations live here since backend/ is
    nova_core's owner (ADR-0021). worker/ writes to this table using the
    same trusted internal credentials as backend's own admin connection -
    unlike the SQL Analytics Tool's scoped read-only role, there's no
    untrusted/LLM-generated query involved here to guard against."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    business_unit_code: Mapped[str] = mapped_column(Text, ForeignKey("business_units.code"))
    object_key: Mapped[str] = mapped_column(Text)  # key within that unit's MinIO bucket
    title: Mapped[str] = mapped_column(Text)
    format: Mapped[str] = mapped_column(Text)  # "markdown" | "pdf"
    status: Mapped[str] = mapped_column(Text, server_default="pending")  # "pending" | "ingested" | "failed"
    chunk_count: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    ingested_at: Mapped[object | None] = mapped_column(TIMESTAMP(timezone=True))

    # Lets both the upload endpoint (creates the row up front, with a
    # human-provided title) and worker's insert_pending (the legacy
    # direct-MinIO-upload path, which has no row yet) safely get-or-create
    # by this pair instead of ever risking two rows for the same object.
    __table_args__ = (UniqueConstraint("business_unit_code", "object_key", name="uq_documents_unit_object_key"),)
