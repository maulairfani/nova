import uuid

from sqlalchemy import Boolean, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    email: Mapped[str] = mapped_column(Text, unique=True)
    # Nullable: the real auth mechanism (session/JWT/SSO) is a separate,
    # not-yet-made decision - this model stays agnostic to it.
    password_hash: Mapped[str | None] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
