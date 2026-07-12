"""One-off dummy-data seed for postgres-plus. Run after `alembic upgrade head`.

Usage: python -m seed.seed_postgres
"""
import datetime
import random

import sqlalchemy as sa

from config import settings

TITLES = [
    {"title": "Langit Senja", "product": "streaming", "genre": "drama", "release_date": "2023-02-14"},
    {"title": "Warisan Terakhir", "product": "streaming", "genre": "thriller", "release_date": "2022-09-01"},
    {"title": "Rahasia Hati", "product": "shorts", "genre": "romance", "release_date": "2024-01-10"},
    {"title": "Balas Dendam Cinta", "product": "shorts", "genre": "drama", "release_date": "2024-05-22"},
]


def seed() -> None:
    engine = sa.create_engine(settings.postgres_plus_admin_url)
    metadata = sa.MetaData()
    metadata.reflect(bind=engine, only=["titles", "engagement", "revenue"])
    titles_t = metadata.tables["titles"]
    engagement_t = metadata.tables["engagement"]
    revenue_t = metadata.tables["revenue"]

    with engine.begin() as conn:
        existing = conn.execute(sa.select(sa.func.count()).select_from(titles_t)).scalar()
        if existing:
            print(f"titles already has {existing} rows — skipping seed (idempotent no-op)")
            return

        title_ids = {}
        for t in TITLES:
            result = conn.execute(
                sa.insert(titles_t).values(**t).returning(titles_t.c.id)
            )
            title_ids[t["title"]] = (result.scalar_one(), t["product"])

        today = datetime.date.today()
        engagement_rows = []
        for title, (title_id, product) in title_ids.items():
            for i in range(43):
                date = today - datetime.timedelta(days=i)
                engagement_rows.append(
                    {
                        "title_id": title_id,
                        "date": date,
                        "watch_minutes": random.randint(5, 90) if product == "streaming" else random.randint(1, 15),
                        "completion_rate": round(random.uniform(0.3, 0.95), 2),
                        "viewers": random.randint(50_000, 900_000),
                        "product": product,
                    }
                )

        revenue_rows = []
        for i in range(0, 43, 7):  # weekly revenue, one row per product
            date = today - datetime.timedelta(days=i)
            revenue_rows.append(
                {
                    "date": date,
                    "product": "streaming",
                    "subscription_revenue_idr": random.randint(800_000_000, 2_500_000_000),
                    "coin_revenue_idr": 0,
                    "active_subscribers": random.randint(200_000, 600_000),
                }
            )
            revenue_rows.append(
                {
                    "date": date,
                    "product": "shorts",
                    "subscription_revenue_idr": 0,
                    "coin_revenue_idr": random.randint(150_000_000, 500_000_000),
                    "active_subscribers": random.randint(50_000, 250_000),
                }
            )

        conn.execute(sa.insert(engagement_t), engagement_rows)
        conn.execute(sa.insert(revenue_t), revenue_rows)

    print(f"Seeded {len(TITLES)} titles, {len(engagement_rows)} engagement rows, {len(revenue_rows)} revenue rows.")


if __name__ == "__main__":
    seed()
