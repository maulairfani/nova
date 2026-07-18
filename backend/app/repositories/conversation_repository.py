"""Data access for the Conversation model (sidebar metadata, app/models/conversation.py).
No ownership/authorization checks or checkpointer calls here - those live
in app/services/conversation_service.py and app/services/chat_service.py."""
import uuid

from sqlalchemy import delete as sa_delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation


async def list_by_user(session: AsyncSession, user_id: uuid.UUID) -> list[Conversation]:
    return (
        (
            await session.execute(
                select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc())
            )
        )
        .scalars()
        .all()
    )


async def get(session: AsyncSession, conversation_id: str) -> Conversation | None:
    return await session.get(Conversation, conversation_id)


async def touch(session: AsyncSession, thread_id: str, user_id: uuid.UUID, title_if_new: str) -> None:
    """Upserts a thread's sidebar row - created with `title_if_new` on the
    first message, bumped (updated_at only, title unchanged) on every
    later one."""
    conversation = await session.get(Conversation, thread_id)
    if conversation is None:
        session.add(Conversation(id=thread_id, user_id=user_id, title=title_if_new))
    else:
        conversation.updated_at = func.now()
    await session.commit()


async def rename(session: AsyncSession, conversation: Conversation, title: str) -> Conversation:
    conversation.title = title
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def delete(session: AsyncSession, conversation_id: str) -> None:
    await session.execute(sa_delete(Conversation).where(Conversation.id == conversation_id))
    await session.commit()
