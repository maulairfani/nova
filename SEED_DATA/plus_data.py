"""Dummy analytics data generator for mcn_plus (ADR-0023's dimensional
schema, streaming + shorts). Run via seed_all.py — see README.md.

Generates ~6 months of activity across both MCN+ products: 20 titles
(streaming movies/series + shorts microdramas), their seasons/episodes,
~600 subscribers, subscriptions + billing (streaming), coin transactions
(shorts), content licensing costs, daily engagement, and a daily revenue
rollup per product.
"""
import datetime
import random

import sqlalchemy as sa

from db_utils import already_seeded, bulk_insert_returning_ids

SEED_DAYS = 180
SUBSCRIBER_COUNT = 600

REGIONS = ["Jakarta", "Jawa Barat", "Jawa Timur", "Jawa Tengah", "Sumatera Utara", "Sumatera Selatan", "Kalimantan", "Sulawesi"]

DEVICES = [
    ("mobile", "ios"), ("mobile", "android"), ("smart_tv", "tvos"),
    ("smart_tv", "other"), ("web", "web"), ("tablet", "android"),
]

LICENSORS = [
    ("Garuda Studios", "Indonesia"), ("Nusantara Pictures", "Indonesia"),
    ("K-Wave Entertainment", "South Korea"), ("Pan Asia Films", "Thailand"),
    ("Global Drama Co", "United States"), ("Sakura Vision", "Japan"),
]

SUBSCRIPTION_PLANS = [
    ("BASIC", "Basic", 39_000, 1),
    ("STANDARD", "Standard", 69_000, 2),
    ("PREMIUM", "Premium", 109_000, 4),
]

COIN_PACKAGES = [
    ("COINS_50", 50, 15_000),
    ("COINS_100", 100, 28_000),
    ("COINS_300", 300, 75_000),
    ("COINS_650", 650, 150_000),
]

# (title, product, content_type, genre, maturity_rating, licensed(bool), seasons)
TITLES = [
    ("Langit Senja", "streaming", "series", "drama", "13+", False, 2),
    ("Warisan Terakhir", "streaming", "series", "thriller", "17+", True, 1),
    ("Jejak Cinta", "streaming", "movie", "romance", "13+", False, 0),
    ("Malam Tanpa Bintang", "streaming", "series", "horror", "17+", True, 1),
    ("Petualangan Kecil", "streaming", "series", "children", "SU", False, 3),
    ("Kota Tanpa Nama", "streaming", "movie", "action", "17+", True, 0),
    ("Cinta di Musim Hujan", "streaming", "series", "drama", "13+", False, 2),
    ("Rahasia Keluarga", "streaming", "series", "drama", "17+", True, 2),
    ("Bintang Kejora", "streaming", "movie", "family", "SU", False, 0),
    ("Dendam Membara", "streaming", "series", "thriller", "21+", True, 1),
    ("Rahasia Hati", "shorts", "microdrama", "romance", "13+", False, 0),
    ("Balas Dendam Cinta", "shorts", "microdrama", "drama", "17+", False, 0),
    ("Cinta Terlarang", "shorts", "microdrama", "romance", "17+", True, 0),
    ("Pengantin Bayangan", "shorts", "microdrama", "drama", "17+", False, 0),
    ("Suami Rahasia", "shorts", "microdrama", "romance", "17+", True, 0),
    ("Anak Konglomerat", "shorts", "microdrama", "drama", "13+", False, 0),
    ("Selingkuh di Kantor", "shorts", "microdrama", "drama", "21+", False, 0),
    ("Kembalinya Sang CEO", "shorts", "microdrama", "romance", "17+", True, 0),
    ("Cinderella Modern", "shorts", "microdrama", "romance", "13+", False, 0),
    ("Balas Budi", "shorts", "microdrama", "drama", "13+", False, 0),
]


def _seed_dimensions(conn, meta):
    regions_t = meta.tables["regions"]
    devices_t = meta.tables["devices"]
    licensors_t = meta.tables["licensors"]
    plans_t = meta.tables["subscription_plans"]
    coins_t = meta.tables["coin_packages"]
    titles_t = meta.tables["titles"]
    seasons_t = meta.tables["seasons"]
    episodes_t = meta.tables["episodes"]
    subscribers_t = meta.tables["subscribers"]

    region_ids = bulk_insert_returning_ids(conn, regions_t, [{"name": r} for r in REGIONS])
    device_ids = bulk_insert_returning_ids(conn, devices_t, [
        {"device_type": dt, "platform": p} for dt, p in DEVICES
    ])
    licensor_ids = bulk_insert_returning_ids(conn, licensors_t, [
        {"name": name, "country": country} for name, country in LICENSORS
    ])
    plan_ids = bulk_insert_returning_ids(conn, plans_t, [
        {"code": code, "name": name, "price_idr": price, "max_concurrent_streams": streams}
        for code, name, price, streams in SUBSCRIPTION_PLANS
    ])
    coin_package_ids = bulk_insert_returning_ids(conn, coins_t, [
        {"code": code, "coin_amount": amount, "price_idr": price}
        for code, amount, price in COIN_PACKAGES
    ])

    title_rows = []
    for title, product, content_type, genre, rating, licensed, _seasons in TITLES:
        title_rows.append({
            "title": title, "product": product, "content_type": content_type,
            "genre": genre, "maturity_rating": rating,
            "licensor_id": random.choice(licensor_ids) if licensed else None,
            "release_date": (datetime.date.today() - datetime.timedelta(days=random.randint(60, 900))).isoformat(),
        })
    title_ids = bulk_insert_returning_ids(conn, titles_t, title_rows)

    season_ids_by_title: dict[int, list[int]] = {}
    episode_ids_by_title: dict[int, list[int]] = {}
    for title_id, (title, product, content_type, genre, rating, licensed, n_seasons) in zip(title_ids, TITLES):
        if n_seasons > 0:
            season_rows = [{"title_id": title_id, "season_number": s + 1} for s in range(n_seasons)]
            season_ids = bulk_insert_returning_ids(conn, seasons_t, season_rows)
            season_ids_by_title[title_id] = season_ids

            episode_rows = []
            for season_id in season_ids:
                for ep in range(random.randint(8, 16)):
                    episode_rows.append({
                        "title_id": title_id, "season_id": season_id, "episode_number": ep + 1,
                        "duration_seconds": random.randint(20 * 60, 55 * 60),
                        "release_date": (datetime.date.today() - datetime.timedelta(days=random.randint(30, 800))).isoformat(),
                    })
            episode_ids_by_title[title_id] = bulk_insert_returning_ids(conn, episodes_t, episode_rows)
        elif content_type == "microdrama":
            episode_rows = [
                {
                    "title_id": title_id, "season_id": None, "episode_number": ep + 1,
                    "duration_seconds": random.randint(60, 5 * 60),
                    "release_date": (datetime.date.today() - datetime.timedelta(days=random.randint(10, 400))).isoformat(),
                }
                for ep in range(random.randint(20, 60))
            ]
            episode_ids_by_title[title_id] = bulk_insert_returning_ids(conn, episodes_t, episode_rows)
        else:  # a movie: single "episode" row
            episode_rows = [{
                "title_id": title_id, "season_id": None, "episode_number": 1,
                "duration_seconds": random.randint(80 * 60, 140 * 60),
                "release_date": (datetime.date.today() - datetime.timedelta(days=random.randint(60, 900))).isoformat(),
            }]
            episode_ids_by_title[title_id] = bulk_insert_returning_ids(conn, episodes_t, episode_rows)

    subscriber_rows = [
        {
            "external_subscriber_code": f"SUB-{i:05d}",
            "signup_date": (datetime.date.today() - datetime.timedelta(days=random.randint(1, 900))).isoformat(),
            "region_id": random.choice(region_ids),
            "primary_device_id": random.choice(device_ids),
        }
        for i in range(SUBSCRIBER_COUNT)
    ]
    subscriber_ids = bulk_insert_returning_ids(conn, subscribers_t, subscriber_rows)

    streaming_title_ids = [tid for tid, t in zip(title_ids, TITLES) if t[1] == "streaming"]
    shorts_title_ids = [tid for tid, t in zip(title_ids, TITLES) if t[1] == "shorts"]

    return {
        "region_ids": region_ids, "device_ids": device_ids, "licensor_ids": licensor_ids,
        "plan_ids": plan_ids, "coin_package_ids": coin_package_ids,
        "title_ids": title_ids, "episode_ids_by_title": episode_ids_by_title,
        "subscriber_ids": subscriber_ids,
        "streaming_title_ids": streaming_title_ids, "shorts_title_ids": shorts_title_ids,
    }


def _seed_facts(conn, meta, dims):
    engagement_t = meta.tables["engagement"]
    subscriptions_t = meta.tables["subscriptions"]
    sub_tx_t = meta.tables["subscription_transactions"]
    coin_tx_t = meta.tables["coin_transactions"]
    licensing_t = meta.tables["content_licensing_costs"]
    revenue_t = meta.tables["revenue"]

    today = datetime.date.today()

    # --- subscriptions + billing (streaming) ---
    streaming_subscribers = random.sample(dims["subscriber_ids"], k=int(SUBSCRIBER_COUNT * 0.7))
    subscription_rows = []
    for subscriber_id in streaming_subscribers:
        status = random.choices(["active", "paused", "churned"], weights=[0.75, 0.1, 0.15])[0]
        start_date = today - datetime.timedelta(days=random.randint(30, SEED_DAYS))
        end_date = None
        churn_reason = None
        if status == "churned":
            end_date = min(start_date + datetime.timedelta(days=random.randint(15, SEED_DAYS)), today)
            churn_reason = random.choice(["price", "content", "competitor", "no_longer_needed"])
        subscription_rows.append({
            "subscriber_id": subscriber_id, "plan_id": random.choice(dims["plan_ids"]),
            "start_date": start_date, "end_date": end_date,
            "status": status, "churn_reason": churn_reason,
        })
    subscription_ids = bulk_insert_returning_ids(conn, subscriptions_t, subscription_rows)

    sub_tx_rows = []
    for sub, sub_row in zip(subscription_ids, subscription_rows):
        billing_date = sub_row["start_date"]
        cutoff = sub_row["end_date"] or today
        while billing_date <= cutoff:
            sub_tx_rows.append({
                "subscriber_id": sub_row["subscriber_id"], "plan_id": sub_row["plan_id"],
                "billing_date": billing_date,
                "amount_idr": random.randint(35_000, 115_000),
                "status": random.choices(["paid", "failed", "refunded"], weights=[0.92, 0.06, 0.02])[0],
            })
            billing_date += datetime.timedelta(days=30)
    bulk_insert_returning_ids(conn, sub_tx_t, sub_tx_rows)

    # --- coin transactions (shorts) ---
    coin_tx_rows = []
    for _ in range(1800):
        subscriber_id = random.choice(dims["subscriber_ids"])
        package_id = random.choice(dims["coin_package_ids"])
        title_id = random.choice(dims["shorts_title_ids"]) if random.random() < 0.8 else None
        coin_tx_rows.append({
            "subscriber_id": subscriber_id, "coin_package_id": package_id, "title_id": title_id,
            "transaction_date": today - datetime.timedelta(days=random.randint(0, SEED_DAYS)),
            "coins_spent": random.randint(10, 300) if title_id else 0,
            "amount_idr": random.randint(15_000, 150_000),
        })
    bulk_insert_returning_ids(conn, coin_tx_t, coin_tx_rows)

    # --- content licensing costs (only for titles marked licensed in TITLES) ---
    licensing_rows = [
        {
            "title_id": title_id,
            "licensor_id": random.choice(dims["licensor_ids"]),
            "license_fee_idr": random.randint(500_000_000, 4_000_000_000),
            "license_start_date": today - datetime.timedelta(days=random.randint(200, 900)),
            "license_end_date": today + datetime.timedelta(days=random.randint(30, 500)),
        }
        for title_id, t in zip(dims["title_ids"], TITLES) if t[5]  # licensed flag
    ]
    bulk_insert_returning_ids(conn, licensing_t, licensing_rows)

    # --- engagement ---
    engagement_rows = []
    for title_id in dims["title_ids"]:
        product = "streaming" if title_id in dims["streaming_title_ids"] else "shorts"
        episode_pool = dims["episode_ids_by_title"].get(title_id, [])
        for day_offset in range(SEED_DAYS):
            if random.random() < 0.6:  # not every title has activity every day
                continue
            date = today - datetime.timedelta(days=day_offset)
            for _ in range(random.randint(1, 3)):
                engagement_rows.append({
                    "title_id": title_id,
                    "episode_id": random.choice(episode_pool) if episode_pool else None,
                    "date": date, "product": product,
                    "device_id": random.choice(dims["device_ids"]),
                    "region_id": random.choice(dims["region_ids"]),
                    "watch_minutes": random.randint(5, 90) if product == "streaming" else random.randint(1, 15),
                    "completion_rate": round(random.uniform(0.25, 0.97), 2),
                    "viewers": random.randint(500, 250_000),
                })
    bulk_insert_returning_ids(conn, engagement_t, engagement_rows)

    # --- daily revenue rollup ---
    revenue_rows = []
    for day_offset in range(SEED_DAYS):
        date = today - datetime.timedelta(days=day_offset)
        revenue_rows.append({
            "date": date, "product": "streaming",
            "subscription_revenue_idr": random.randint(800_000_000, 2_500_000_000),
            "coin_revenue_idr": 0,
            "active_subscribers": random.randint(200_000, 600_000),
        })
        revenue_rows.append({
            "date": date, "product": "shorts",
            "subscription_revenue_idr": 0,
            "coin_revenue_idr": random.randint(150_000_000, 500_000_000),
            "active_subscribers": random.randint(50_000, 250_000),
        })
    bulk_insert_returning_ids(conn, revenue_t, revenue_rows)

    return len(subscription_ids), len(sub_tx_rows), len(coin_tx_rows), len(licensing_rows), len(engagement_rows)


def seed(engine: sa.Engine) -> None:
    meta = sa.MetaData()
    meta.reflect(bind=engine)
    titles_t = meta.tables["titles"]

    with engine.begin() as conn:
        if already_seeded(conn, titles_t):
            print("mcn_plus: titles already seeded — skipping (idempotent no-op)")
            return

        dims = _seed_dimensions(conn, meta)
        n_subs, n_sub_tx, n_coin_tx, n_licensing, n_engagement = _seed_facts(conn, meta, dims)

    print(
        f"mcn_plus: seeded {len(TITLES)} titles, {SUBSCRIBER_COUNT} subscribers, "
        f"{n_subs} subscriptions, {n_sub_tx} subscription_transactions, "
        f"{n_coin_tx} coin_transactions, {n_licensing} content_licensing_costs rows, "
        f"{n_engagement} engagement rows, {SEED_DAYS * 2} revenue rollup rows."
    )
