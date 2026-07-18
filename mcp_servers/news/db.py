"""Async, read-only connection to postgres-news for the SQL Analytics Tool."""
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from common.semantic_layer import load_semantic_layer
from config import settings

_engine = create_async_engine(settings.postgres_news_url, pool_pre_ping=True)

# Semantic layer (ADR-0024) for the text-to-SQL prompt — table/column
# business meaning, glossary, derived metrics, and example queries for
# mcn_news's dimensional schema (ADR-0023), not just table signatures.
SCHEMA_DESCRIPTION = load_semantic_layer(Path(__file__).parent / "semantic" / "schema.yaml")

_FORBIDDEN_KEYWORDS = ("insert", "update", "delete", "drop", "alter", "truncate", "grant", "revoke")


class NonSelectQueryError(Exception):
    pass


async def run_select(sql: str) -> list[dict]:
    normalized = sql.strip().lower()
    # A CTE (`WITH ... SELECT ...`) is a legitimate, read-only query - the
    # SQL Analytics Tool's own text-to-SQL step reaches for one on any
    # question involving a comparison (e.g. week-over-week/month-over-month),
    # and rejecting it here as "not a SELECT" was a real bug, not just an
    # overly cautious guard: it made every WoW/MoM-style question fail
    # every time, deterministically, regardless of how the query was worded.
    if not (normalized.startswith("select") or normalized.startswith("with")):
        raise NonSelectQueryError("Only SELECT statements are allowed.")
    if any(keyword in normalized for keyword in _FORBIDDEN_KEYWORDS):
        raise NonSelectQueryError("Query contains a forbidden keyword.")

    async with _engine.connect() as conn:
        result = await conn.execute(text(sql))
        return [dict(row._mapping) for row in result]
