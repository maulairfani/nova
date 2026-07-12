"""One-off dummy-data seed for postgres-news. Run after `alembic upgrade head`.

Usage: python -m seed.seed_postgres
"""
import datetime
import random

import sqlalchemy as sa

from config import settings

ARTICLES = [
    {"headline": "Ekonomi Nasional Tumbuh 5,2% di Kuartal Ini", "category": "business", "publish_date": "2026-06-01"},
    {"headline": "Pemerintah Umumkan Kebijakan Energi Baru", "category": "national", "publish_date": "2026-06-10"},
    {"headline": "Timnas Raih Kemenangan Penting di Laga Tandang", "category": "sports", "publish_date": "2026-06-20"},
    {"headline": "Banjir Landa Beberapa Wilayah Jabodetabek", "category": "regional", "publish_date": "2026-06-25"},
]

AD_SLOT_TYPES = ["display_banner", "native_article", "video_preroll", "newsletter_sponsorship"]


def seed() -> None:
    engine = sa.create_engine(settings.postgres_news_admin_url)
    metadata = sa.MetaData()
    metadata.reflect(bind=engine, only=["articles", "article_engagement", "ad_revenue"])
    articles_t = metadata.tables["articles"]
    engagement_t = metadata.tables["article_engagement"]
    revenue_t = metadata.tables["ad_revenue"]

    with engine.begin() as conn:
        existing = conn.execute(sa.select(sa.func.count()).select_from(articles_t)).scalar()
        if existing:
            print(f"articles already has {existing} rows — skipping seed (idempotent no-op)")
            return

        article_ids = []
        for a in ARTICLES:
            result = conn.execute(
                sa.insert(articles_t).values(**a).returning(articles_t.c.id)
            )
            article_ids.append(result.scalar_one())

        today = datetime.date.today()
        engagement_rows = []
        for article_id in article_ids:
            for i in range(43):
                date = today - datetime.timedelta(days=i)
                engagement_rows.append(
                    {
                        "article_id": article_id,
                        "date": date,
                        "page_views": random.randint(2_000, 150_000),
                        "unique_visitors": random.randint(1_500, 90_000),
                        "avg_time_on_page_seconds": random.randint(30, 240),
                    }
                )

        revenue_rows = []
        for i in range(0, 43, 7):  # weekly ad revenue, per slot type
            date = today - datetime.timedelta(days=i)
            for slot_type in AD_SLOT_TYPES:
                revenue_rows.append(
                    {
                        "date": date,
                        "ad_slot_type": slot_type,
                        "revenue_idr": random.randint(20_000_000, 180_000_000),
                    }
                )

        conn.execute(sa.insert(engagement_t), engagement_rows)
        conn.execute(sa.insert(revenue_t), revenue_rows)

    print(f"Seeded {len(ARTICLES)} articles, {len(engagement_rows)} engagement rows, {len(revenue_rows)} revenue rows.")


if __name__ == "__main__":
    seed()
