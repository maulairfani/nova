"""Data access for users/business-unit memberships (nova_core, ADR-0021).
No business logic here (password verification, claims shaping) - that's
app/services/auth_service.py."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserBusinessUnit


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    return (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()


async def list_business_units(session: AsyncSession, user_id: uuid.UUID) -> list[UserBusinessUnit]:
    return (
        (await session.execute(select(UserBusinessUnit).where(UserBusinessUnit.user_id == user_id)))
        .scalars()
        .all()
    )
