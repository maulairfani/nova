"""Async, read-only connection to postgres-news for the SQL Analytics Tool."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from config import settings

_engine = create_async_engine(settings.postgres_news_url, pool_pre_ping=True)

# Hardcoded schema description for the text-to-SQL prompt (phase 1 — only
# three tables' worth of dummy data, so a hand-written description is simpler
# and more reliable than introspecting the DB at request time).
SCHEMA_DESCRIPTION = """
Tables in the mcn_news database (all read-only):

articles(id, headline, category, publish_date)
article_engagement(id, article_id -> articles.id, date, page_views int, unique_visitors int, avg_time_on_page_seconds int)
ad_revenue(id, date, ad_slot_type text, revenue_idr bigint)
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
