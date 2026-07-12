"""Async, read-only connection to postgres-plus for the SQL Analytics Tool."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from config import settings

_engine = create_async_engine(settings.postgres_plus_url, pool_pre_ping=True)

# Hardcoded schema description for the text-to-SQL prompt (phase 1 — only
# three tables' worth of dummy data, so a hand-written description is simpler
# and more reliable than introspecting the DB at request time).
SCHEMA_DESCRIPTION = """
Tables in the mcn_plus database (all read-only). MCN+ spans two products,
distinguished by the `product` column: 'streaming' (OTT) or 'shorts' (micro-drama).

titles(id, title, product['streaming'|'shorts'], genre, release_date)
engagement(id, title_id -> titles.id, date, watch_minutes int, completion_rate numeric, viewers int, product['streaming'|'shorts'])
revenue(id, date, product['streaming'|'shorts'], subscription_revenue_idr bigint, coin_revenue_idr bigint, active_subscribers int)
"""

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
