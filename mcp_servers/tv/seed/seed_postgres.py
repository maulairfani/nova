"""One-off dummy-data seed for postgres-tv. Run after `alembic upgrade head`.

Usage: python -m seed.seed_postgres
"""
import datetime
import random

import sqlalchemy as sa

from config import settings

PROGRAMS = [
    {"title": "Jakarta Malam", "genre": "variety", "daypart": "prime_time", "premiere_date": "2023-01-09"},
    {"title": "Cinta di Ujung Senja", "genre": "drama", "daypart": "prime_time", "premiere_date": "2022-06-05"},
    {"title": "Fakta Pagi", "genre": "news", "daypart": "day_time", "premiere_date": "2021-03-15"},
    {"title": "Layar Tengah Malam", "genre": "film", "daypart": "late_night", "premiere_date": "2020-11-02"},
]

REGIONS = ["Jabodetabek", "Jawa Barat", "Jawa Timur", "Sumatera", "Nasional"]


def seed() -> None:
    engine = sa.create_engine(settings.postgres_tv_admin_url)
    metadata = sa.MetaData()
    metadata.reflect(bind=engine, only=["programs", "viewership_ratings", "ad_revenue"])
    programs_t = metadata.tables["programs"]
    ratings_t = metadata.tables["viewership_ratings"]
    revenue_t = metadata.tables["ad_revenue"]

    with engine.begin() as conn:
        existing = conn.execute(sa.select(sa.func.count()).select_from(programs_t)).scalar()
        if existing:
            print(f"programs already has {existing} rows — skipping seed (idempotent no-op)")
            return

        program_ids = {}
        for p in PROGRAMS:
            result = conn.execute(
                sa.insert(programs_t).values(**p).returning(programs_t.c.id)
            )
            program_ids[p["title"]] = result.scalar_one()

        today = datetime.date.today()
        ratings_rows = []
        revenue_rows = []
        for title, program_id in program_ids.items():
            for i in range(43):  # 6 weeks of daily ratings
                air_date = today - datetime.timedelta(days=i)
                ratings_rows.append(
                    {
                        "program_id": program_id,
                        "air_date": air_date,
                        "rating": round(random.uniform(3, 15), 2),
                        "households_reached": random.randint(400_000, 1_300_000),
                        "region": random.choice(REGIONS),
                    }
                )
            for i in range(0, 43, 7):  # weekly ad revenue
                air_date = today - datetime.timedelta(days=i)
                revenue_rows.append(
                    {
                        "program_id": program_id,
                        "air_date": air_date,
                        "slot_count": random.randint(4, 11),
                        "revenue_idr": random.randint(50_000_000, 300_000_000),
                    }
                )

        conn.execute(sa.insert(ratings_t), ratings_rows)
        conn.execute(sa.insert(revenue_t), revenue_rows)

    print(f"Seeded {len(PROGRAMS)} programs, {len(ratings_rows)} ratings rows, {len(revenue_rows)} revenue rows.")


if __name__ == "__main__":
    seed()
