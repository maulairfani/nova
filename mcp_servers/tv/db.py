"""Async, read-only connection to postgres-tv for the SQL Analytics Tool."""
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from common.semantic_layer import load_semantic_layer
from config import settings

_engine = create_async_engine(settings.postgres_tv_url, pool_pre_ping=True)

# Semantic layer (ADR-0024) for the text-to-SQL prompt — table/column
# business meaning, glossary, derived metrics, and example queries for
# mcn_tv's dimensional schema (ADR-0023), not just table signatures.
SCHEMA_DESCRIPTION = load_semantic_layer(Path(__file__).parent / "semantic" / "schema.yaml")

_FORBIDDEN_KEYWORDS = ("insert", "update", "delete", "drop", "alter", "truncate", "grant", "revoke")


class NonSelectQueryError(Exception):
    pass


async def run_select(sql: str) -> list[dict]:
    normalized = sql.strip().lower()
    if not normalized.startswith("select"):
        raise NonSelectQueryError("Only SELECT statements are allowed.")
    if any(keyword in normalized for keyword in _FORBIDDEN_KEYWORDS):
        raise NonSelectQueryError("Query contains a forbidden keyword.")

    async with _engine.connect() as conn:
        result = await conn.execute(text(sql))
        return [dict(row._mapping) for row in result]
