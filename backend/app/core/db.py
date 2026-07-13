"""Async engine for querying nova_core's identity/access schema (ADR-0021)
at request runtime - separate from checkpointer.py's own connection
(LangGraph manages that one directly, not through SQLAlchemy)."""
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings

_engine = create_async_engine(settings.core_database_admin_url, pool_pre_ping=True)
async_session = async_sessionmaker(_engine, expire_on_commit=False)
