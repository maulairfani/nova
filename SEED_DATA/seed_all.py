"""Consolidated dummy-data seed for all 3 business-unit analytics
databases (ADR-0025). Run after each unit's `alembic upgrade head`.

Usage: docker compose run --rm seed-data python seed_all.py
"""
import sqlalchemy as sa

import news_data
import plus_data
import tv_data
from config import settings


def main() -> None:
    tv_engine = sa.create_engine(settings.postgres_tv_admin_url)
    plus_engine = sa.create_engine(settings.postgres_plus_admin_url)
    news_engine = sa.create_engine(settings.postgres_news_admin_url)

    tv_data.seed(tv_engine)
    plus_data.seed(plus_engine)
    news_data.seed(news_engine)


if __name__ == "__main__":
    main()
