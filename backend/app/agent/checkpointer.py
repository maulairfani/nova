"""Checkpointer (TDD §5.2) — LangGraph's Postgres checkpointer against
`nova_core`. `.setup()` is run once as an explicit step (see README), not on
every app startup."""
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.config import settings


def get_checkpointer_cm():
    """Returns the async context manager; caller enters it once at app
    startup and keeps the resulting saver for the app's lifetime."""
    return AsyncPostgresSaver.from_conn_string(settings.core_database_url)
