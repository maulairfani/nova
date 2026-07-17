"""Dummy analytics data generator for mcn_news (ADR-0023's dimensional
schema). Run via seed_all.py — see README.md.

Generates ~6 months of newsroom activity: 6 desks, 18 authors, 6
platforms, 4 ad slot types, ~150 articles published across that window
(a handful flagged breaking news, a subset later corrected/retracted),
each with per-platform engagement decaying over the two weeks after
publish, plus a daily ad revenue rollup per slot type/platform.
"""
import datetime
import random

import sqlalchemy as sa

from db_utils import already_seeded, bulk_insert_returning_ids

SEED_DAYS = 180
ARTICLE_COUNT = 150

DESKS = [
    ("politics", "Politik"), ("business", "Ekonomi & Bisnis"), ("sports", "Olahraga"),
    ("regional", "Daerah"), ("entertainment", "Hiburan"), ("tech", "Teknologi"),
]

AUTHOR_NAMES = [
    "Siti Rahma", "Budi Santoso", "Andi Wijaya", "Dewi Lestari", "Rizky Pratama",
    "Nadia Putri", "Fajar Nugroho", "Maya Anggraini", "Hendra Kusuma", "Lina Marlina",
    "Agus Setiawan", "Ratna Sari", "Yoga Pramudya", "Intan Permata", "Dimas Aditya",
    "Wulan Sari", "Bayu Firmansyah", "Citra Ayu",
]

PLATFORMS = [
    ("web", "MCN News Website"), ("mobile_app", "MCN News App"), ("facebook", "Facebook"),
    ("instagram", "Instagram"), ("x", "X (Twitter)"), ("newsletter", "Email Newsletter"),
]

AD_SLOT_TYPES = [
    ("display_banner", "Display Banner"), ("native_article", "Native Article"),
    ("video_preroll", "Video Pre-roll"), ("newsletter_sponsorship", "Newsletter Sponsorship"),
]

HEADLINE_TEMPLATES = {
    "politics": ["Pemerintah Umumkan Kebijakan Baru di Sektor {x}", "DPR Bahas RUU {x}", "Menteri {x} Tanggapi Isu Terkini"],
    "business": ["Ekonomi Nasional Tumbuh {x}% di Kuartal Ini", "Rupiah Menguat Terhadap Dolar AS", "IHSG Ditutup {x} Hari Ini"],
    "sports": ["Timnas Raih Kemenangan di Laga {x}", "Atlet Indonesia Juara di {x}", "Liga {x} Musim Ini Diprediksi Ketat"],
    "regional": ["Banjir Landa Wilayah {x}", "Pemda {x} Luncurkan Program Baru", "Infrastruktur {x} Rampung Tahun Ini"],
    "entertainment": ["Film {x} Raih Sukses di Box Office", "Musisi {x} Rilis Album Baru", "Selebriti {x} Umumkan Proyek Baru"],
    "tech": ["Startup {x} Raih Pendanaan Baru", "Teknologi {x} Mulai Diadopsi Perusahaan", "Peluncuran Produk {x} Terbaru"],
}
FILLERS = ["Nasional", "Jabodetabek", "5,2", "Merah", "Timur", "Jawa", "AI", "Digital", "Kuartal III", "2026"]


def _seed_dimensions(conn, meta):
    desks_t = meta.tables["desks"]
    authors_t = meta.tables["authors"]
    platforms_t = meta.tables["platforms"]
    ad_slot_types_t = meta.tables["ad_slot_types"]

    desk_ids = dict(zip(
        [d[0] for d in DESKS],
        bulk_insert_returning_ids(conn, desks_t, [{"code": code, "name": name} for code, name in DESKS]),
    ))

    author_rows = [
        {"name": name, "desk_id": random.choice(list(desk_ids.values()))}
        for name in AUTHOR_NAMES
    ]
    author_ids = bulk_insert_returning_ids(conn, authors_t, author_rows)

    platform_ids = dict(zip(
        [p[0] for p in PLATFORMS],
        bulk_insert_returning_ids(conn, platforms_t, [{"code": code, "name": name} for code, name in PLATFORMS]),
    ))

    ad_slot_type_ids = dict(zip(
        [a[0] for a in AD_SLOT_TYPES],
        bulk_insert_returning_ids(conn, ad_slot_types_t, [{"code": code, "name": name} for code, name in AD_SLOT_TYPES]),
    ))

    return {
        "desk_ids": desk_ids, "author_ids": author_ids,
        "platform_ids": list(platform_ids.values()), "ad_slot_type_ids": list(ad_slot_type_ids.values()),
    }


def _seed_facts(conn, meta, dims):
    articles_t = meta.tables["articles"]
    engagement_t = meta.tables["article_engagement"]
    ad_revenue_t = meta.tables["ad_revenue"]
    corrections_t = meta.tables["corrections"]

    today = datetime.date.today()

    article_rows = []
    for _ in range(ARTICLE_COUNT):
        desk_code = random.choice(list(DESKS))[0]
        headline = random.choice(HEADLINE_TEMPLATES[desk_code]).format(x=random.choice(FILLERS))
        article_rows.append({
            "headline": headline,
            "desk_id": dims["desk_ids"][desk_code],
            "author_id": random.choice(dims["author_ids"]),
            "content_type": random.choices(["text", "video", "live_blog"], weights=[0.75, 0.2, 0.05])[0],
            "publish_date": today - datetime.timedelta(days=random.randint(0, SEED_DAYS - 1)),
            "is_breaking": random.random() < 0.12,
        })
    article_ids = bulk_insert_returning_ids(conn, articles_t, article_rows)

    engagement_rows = []
    for article_id, article in zip(article_ids, article_rows):
        publish_date = article["publish_date"]
        active_platforms = random.sample(dims["platform_ids"], k=random.randint(2, len(dims["platform_ids"])))
        for platform_id in active_platforms:
            base_views = random.randint(5_000, 150_000)
            days_visible = min(14, (today - publish_date).days + 1)
            for day_offset in range(days_visible):
                date = publish_date + datetime.timedelta(days=day_offset)
                if date > today:
                    break
                decay = max(0.05, 1 - day_offset * 0.15)
                page_views = int(base_views * decay * random.uniform(0.7, 1.3))
                engagement_rows.append({
                    "article_id": article_id, "platform_id": platform_id, "date": date,
                    "page_views": page_views,
                    "unique_visitors": int(page_views * random.uniform(0.55, 0.85)),
                    "avg_time_on_page_seconds": random.randint(30, 240),
                    "social_shares": int(page_views * random.uniform(0.001, 0.03)),
                })
    bulk_insert_returning_ids(conn, engagement_t, engagement_rows)

    revenue_rows = []
    for day_offset in range(SEED_DAYS):
        date = today - datetime.timedelta(days=day_offset)
        for slot_type_id in dims["ad_slot_type_ids"]:
            for platform_id in dims["platform_ids"]:
                impressions = random.randint(50_000, 2_000_000)
                revenue_rows.append({
                    "date": date, "ad_slot_type_id": slot_type_id, "platform_id": platform_id,
                    "impressions": impressions,
                    "revenue_idr": int(impressions * random.uniform(3, 25)),
                })
    bulk_insert_returning_ids(conn, ad_revenue_t, revenue_rows)

    correction_rows = []
    for article_id in random.sample(article_ids, k=int(ARTICLE_COUNT * 0.08)):
        severity = random.choices(["minor", "major", "retraction"], weights=[0.6, 0.3, 0.1])[0]
        reason = {
            "minor": "Perbaikan salah ketik/ejaan pada nama atau angka.",
            "major": "Koreksi fakta signifikan setelah verifikasi ulang narasumber.",
            "retraction": "Artikel ditarik karena kesalahan fakta mendasar yang tidak dapat diperbaiki secara parsial.",
        }[severity]
        correction_rows.append({
            "article_id": article_id,
            "correction_date": today - datetime.timedelta(days=random.randint(0, SEED_DAYS - 1)),
            "reason": reason, "severity": severity,
        })
    bulk_insert_returning_ids(conn, corrections_t, correction_rows)

    return len(engagement_rows), len(revenue_rows), len(correction_rows)


def seed(engine: sa.Engine) -> None:
    meta = sa.MetaData()
    meta.reflect(bind=engine)
    articles_t = meta.tables["articles"]

    with engine.begin() as conn:
        if already_seeded(conn, articles_t):
            print("mcn_news: articles already seeded — skipping (idempotent no-op)")
            return

        dims = _seed_dimensions(conn, meta)
        n_engagement, n_revenue, n_corrections = _seed_facts(conn, meta, dims)

    print(
        f"mcn_news: seeded {len(DESKS)} desks, {len(AUTHOR_NAMES)} authors, "
        f"{len(PLATFORMS)} platforms, {len(AD_SLOT_TYPES)} ad slot types, "
        f"{ARTICLE_COUNT} articles, {n_engagement} article_engagement rows, "
        f"{n_revenue} ad_revenue rows, {n_corrections} corrections."
    )
