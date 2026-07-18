import uuid

from sqlalchemy import ForeignKey, Index, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Conversation(Base):
    """Sidebar metadata (title, ownership, recency) for a chat thread.

    Deliberately separate from LangGraph's own checkpoint tables, same
    split as Document/ADR-0022: the checkpointer owns message content and
    agent state under this same `id` as its `thread_id`, this table only
    owns what the sidebar needs to list/search/rename/delete threads
    without touching LangGraph's storage. Row is upserted by chat.py on
    each message (created on the first message of a thread, updated_at
    bumped on every subsequent one); deleting a row must also delete the
    matching checkpointer thread (done in the conversations endpoint, not
    here, since that's the checkpointer's API, not the ORM's)."""

    __tablename__ = "conversations"

    # Text, not UUID: this is the LangGraph thread_id the frontend already
    # generates via crypto.randomUUID() - stored as an opaque string key
    # rather than re-validated as a UUID type.
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_conversations_user_id_updated_at", "user_id", "updated_at"),)
