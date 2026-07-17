"""Dummy analytics data generator for mcn_tv (ADR-0023's dimensional
schema, Nielsen-style ratings). Run via seed_all.py — see README.md.

Generates ~6 months of daily broadcast activity: 4 channels, 16 programs
and their episodes, 10 DMAs, 8 demographic segments, 15 advertisers and
their campaigns, rate cards, then per-day airings with Nielsen ratings
(sampled across DMAs/segments/measurement type), ad slot bookings, and a
daily ad revenue rollup per channel.
"""
import datetime
import random

import sqlalchemy as sa

from db_utils import already_seeded, bulk_insert_returning_ids

SEED_DAYS = 180

CHANNELS = [
    {"code": "MCN1", "name": "MCN 1", "coverage_type": "national"},
    {"code": "MCN2", "name": "MCN 2", "coverage_type": "national"},
    {"code": "MCN3", "name": "MCN 3", "coverage_type": "national"},
    {"code": "MCN_SPORT", "name": "MCN Sport", "coverage_type": "regional"},
]

# (title, genre, format, production_type, premiere_date, episode_count, preferred_daypart)
PROGRAMS = [
    ("Jakarta Malam", "variety", "variety", "in_house", "2020-01-09", 52, "prime_time"),
    ("Cinta di Ujung Senja", "drama", "drama", "in_house", "2022-06-05", 60, "prime_time"),
    ("Fakta Pagi", "news", "news", "in_house", "2019-03-15", 180, "day_time"),
    ("Layar Tengah Malam", "film", "film", "acquired", "2020-11-02", 24, "late_night"),
    ("Warisan Keluarga", "drama", "drama", "in_house", "2021-02-14", 60, "prime_time"),
    ("Arena Juara", "sports", "sports", "in_house", "2018-08-01", 45, "prime_time"),
    ("Dunia Anak", "children", "children", "in_house", "2021-07-10", 60, "day_time"),
    ("Kabar Malam", "news", "news", "in_house", "2018-01-01", 180, "prime_time"),
    ("Realita Kita", "reality", "reality", "acquired", "2022-09-01", 40, "prime_time"),
    ("Panggung Komedi", "variety", "variety", "in_house", "2020-05-20", 45, "prime_time"),
    ("Bincang Bisnis", "news", "news", "in_house", "2021-04-01", 90, "day_time"),
    ("Misteri Kota", "drama", "drama", "acquired", "2023-01-15", 30, "late_night"),
    ("Sahur Ceria", "variety", "variety", "in_house", "2022-03-01", 30, "day_time"),
    ("Kelas Inspirasi", "children", "children", "in_house", "2020-08-08", 45, "day_time"),
    ("Aksi Tengah Malam", "film", "film", "acquired", "2019-06-01", 20, "late_night"),
    ("Piala Nusantara", "sports", "sports", "in_house", "2022-11-01", 30, "prime_time"),
]

DMAS = [
    ("JABO", "Jabodetabek", 8_500_000, 30_000_000),
    ("JABAR", "Jawa Barat (ex-Jabodetabek)", 6_200_000, 22_000_000),
    ("JATIM", "Jawa Timur", 5_800_000, 20_500_000),
    ("JATENG", "Jawa Tengah & DIY", 5_100_000, 18_000_000),
    ("SUMUT", "Sumatera Utara", 2_400_000, 8_500_000),
    ("SUMSEL", "Sumatera Selatan", 1_600_000, 5_700_000),
    ("KALSEL", "Kalimantan Selatan", 900_000, 3_200_000),
    ("SULSEL", "Sulawesi Selatan", 1_100_000, 3_900_000),
    ("BALI_NUSRA", "Bali & Nusa Tenggara", 1_300_000, 4_600_000),
    ("NASIONAL", "Nasional (all DMAs combined)", 33_000_000, 116_000_000),
]

DEMOGRAPHIC_SEGMENTS = [
    ("ALL_5PLUS", "All Individuals 5+", 5, None, "all"),
    ("ADULTS_18_49", "Adults 18-49", 18, 49, "all"),
    ("ADULTS_25_54", "Adults 25-54", 25, 54, "all"),
    ("WOMEN_18_49", "Women 18-49", 18, 49, "female"),
    ("MEN_18_49", "Men 18-49", 18, 49, "male"),
    ("KIDS_5_14", "Kids 5-14", 5, 14, "all"),
    ("ADULTS_50PLUS", "Adults 50+", 50, None, "all"),
    ("HOUSEWIVES", "Housewives", 25, None, "female"),
]

ADVERTISER_NAMES = [
    ("Nusantara Foods", "FMCG"), ("Java Motors", "automotive"), ("Telkomas", "telco"),
    ("BankSentosa", "banking"), ("Cantik Kosmetik", "FMCG"), ("Sehat Farma", "pharma"),
    ("Rumah Properti", "real_estate"), ("Warung Digital", "e_commerce"), ("Kopi Nusantara", "FMCG"),
    ("Merdeka Insurance", "insurance"), ("Cepat Logistik", "logistics"), ("Anak Bangsa Snack", "FMCG"),
    ("Gaya Fashion", "retail"), ("Energi Prima", "energy"), ("EduCerdas", "education"),
]

DAYPARTS = ["prime_time", "day_time", "late_night"]


def _seed_dimensions(conn, meta):
    channels_t = meta.tables["channels"]
    programs_t = meta.tables["programs"]
    episodes_t = meta.tables["episodes"]
    dmas_t = meta.tables["dma_regions"]
    segments_t = meta.tables["demographic_segments"]
    advertisers_t = meta.tables["advertisers"]
    campaigns_t = meta.tables["ad_campaigns"]
    rate_cards_t = meta.tables["rate_cards"]

    channel_ids = dict(zip(
        [c["code"] for c in CHANNELS],
        bulk_insert_returning_ids(conn, channels_t, CHANNELS),
    ))

    program_ids = bulk_insert_returning_ids(conn, programs_t, [
        {
            "title": p[0], "genre": p[1], "format": p[2],
            "production_type": p[3], "premiere_date": p[4],
        }
        for p in PROGRAMS
    ])

    episode_ids_by_program = {}
    episode_ids_by_daypart: dict[str, list[int]] = {d: [] for d in DAYPARTS}
    for program_id, p in zip(program_ids, PROGRAMS):
        n_episodes = p[5]
        preferred_daypart = p[6]
        episode_rows = [
            {
                "program_id": program_id,
                "season_number": i // 13 + 1,
                "episode_number": i % 13 + 1,
                "title": f"{p[0]} - Eps {i + 1}",
                "duration_minutes": random.choice([24, 30, 44, 60, 90]),
            }
            for i in range(n_episodes)
        ]
        ids = bulk_insert_returning_ids(conn, episodes_t, episode_rows)
        episode_ids_by_program[program_id] = ids
        episode_ids_by_daypart[preferred_daypart].extend(ids)

    dma_ids = dict(zip(
        [d[0] for d in DMAS],
        bulk_insert_returning_ids(conn, dmas_t, [
            {"code": d[0], "name": d[1], "universe_estimate_households": d[2], "universe_estimate_persons": d[3]}
            for d in DMAS
        ]),
    ))

    segment_ids = dict(zip(
        [s[0] for s in DEMOGRAPHIC_SEGMENTS],
        bulk_insert_returning_ids(conn, segments_t, [
            {"code": s[0], "label": s[1], "min_age": s[2], "max_age": s[3], "gender": s[4]}
            for s in DEMOGRAPHIC_SEGMENTS
        ]),
    ))

    advertiser_ids = bulk_insert_returning_ids(conn, advertisers_t, [
        {"name": name, "industry_sector": sector} for name, sector in ADVERTISER_NAMES
    ])

    today = datetime.date.today()
    seed_start = today - datetime.timedelta(days=SEED_DAYS)
    segment_id_list = list(segment_ids.values())

    campaign_rows = []
    for advertiser_id in advertiser_ids:
        for _ in range(random.randint(1, 2)):
            start_offset = random.randint(0, SEED_DAYS - 30)
            campaign_rows.append({
                "advertiser_id": advertiser_id,
                "name": f"Campaign {advertiser_id}-{start_offset}",
                "target_demographic_segment_id": random.choice(segment_id_list),
                "start_date": seed_start + datetime.timedelta(days=start_offset),
                "end_date": seed_start + datetime.timedelta(days=min(start_offset + random.randint(14, 45), SEED_DAYS)),
                "target_grp": round(random.uniform(200, 1500), 2),
            })
    campaign_ids = bulk_insert_returning_ids(conn, campaigns_t, campaign_rows)

    rate_card_rows = []
    rate_card_lookup: dict[tuple[str, int], int] = {}
    for daypart in DAYPARTS:
        base_price = {"prime_time": 25_000_000, "day_time": 9_000_000, "late_night": 6_000_000}[daypart]
        for seg_code, seg_id in segment_ids.items():
            rate_card_rows.append({
                "daypart": daypart,
                "demographic_segment_id": seg_id,
                "price_per_grp_idr": base_price + random.randint(-1_500_000, 3_000_000),
                "effective_start_date": seed_start,
                "effective_end_date": None,
            })
    rate_card_ids = bulk_insert_returning_ids(conn, rate_cards_t, rate_card_rows)
    idx = 0
    for daypart in DAYPARTS:
        for seg_id in segment_ids.values():
            rate_card_lookup[(daypart, seg_id)] = rate_card_ids[idx]
            idx += 1

    return {
        "channel_ids": list(channel_ids.values()),
        "program_ids": program_ids,
        "episode_ids_by_program": episode_ids_by_program,
        "episode_ids_by_daypart": episode_ids_by_daypart,
        "dma_ids": list(dma_ids.values()),
        "segment_ids": segment_id_list,
        "advertiser_ids": advertiser_ids,
        "campaign_ids": campaign_ids,
        "rate_card_lookup": rate_card_lookup,
    }


def _seed_facts(conn, meta, dims):
    airings_t = meta.tables["airings"]
    ratings_t = meta.tables["nielsen_ratings"]
    ad_slots_t = meta.tables["ad_slots"]
    ad_revenue_t = meta.tables["ad_revenue"]

    today = datetime.date.today()
    all_episode_ids = [eid for eids in dims["episode_ids_by_program"].values() for eid in eids]

    def _episode_for_daypart(daypart: str) -> int:
        pool = dims["episode_ids_by_daypart"].get(daypart) or all_episode_ids
        return random.choice(pool)

    total_airings = 0
    total_ratings = 0
    total_slots = 0

    for day_offset in range(SEED_DAYS):
        air_date = today - datetime.timedelta(days=SEED_DAYS - day_offset)

        for channel_id in dims["channel_ids"]:
            second_daypart = random.choice(["day_time", "late_night"])
            second_air_time = datetime.time(10, 0) if second_daypart == "day_time" else datetime.time(23, 0)
            day_airing_rows = []
            for daypart, air_time in (("prime_time", datetime.time(19, 30)), (second_daypart, second_air_time)):
                day_airing_rows.append({
                    "episode_id": _episode_for_daypart(daypart),
                    "channel_id": channel_id,
                    "air_date": air_date,
                    "air_time": air_time,
                    "daypart": daypart,
                    "is_rerun": random.random() < 0.15,
                })
            airing_ids = bulk_insert_returning_ids(conn, airings_t, day_airing_rows)
            total_airings += len(airing_ids)

            rating_rows = []
            slot_rows = []
            for airing_id, airing in zip(airing_ids, day_airing_rows):
                sampled_dmas = random.sample(dims["dma_ids"], k=4)
                sampled_segments = random.sample(dims["segment_ids"], k=3)
                for dma_id in sampled_dmas:
                    for seg_id in sampled_segments:
                        base_rating = round(random.uniform(1.5, 14.0), 2)
                        hut = round(random.uniform(35, 60), 2)
                        share = min(round(base_rating / hut * 100, 2), 99.9)
                        grp = base_rating
                        rating_rows.append({
                            "airing_id": airing_id, "dma_id": dma_id, "demographic_segment_id": seg_id,
                            "measurement_type": "overnight", "rating_pct": base_rating, "share_pct": share,
                            "grp": grp, "hut_pct": hut, "sample_size": random.randint(300, 1800),
                        })
                        if random.random() < 0.4:
                            lifted = round(base_rating * random.uniform(1.05, 1.35), 2)
                            rating_rows.append({
                                "airing_id": airing_id, "dma_id": dma_id, "demographic_segment_id": seg_id,
                                "measurement_type": "live_plus_7", "rating_pct": lifted,
                                "share_pct": min(round(lifted / hut * 100, 2), 99.9),
                                "grp": lifted, "hut_pct": hut, "sample_size": random.randint(300, 1800),
                            })

                for slot_position in range(1, random.randint(4, 9)):
                    advertiser_id = random.choice(dims["advertiser_ids"])
                    campaign_id = random.choice(dims["campaign_ids"]) if random.random() < 0.5 else None
                    rate_card_id = dims["rate_card_lookup"].get((airing["daypart"], random.choice(dims["segment_ids"])))
                    slot_rows.append({
                        "airing_id": airing_id, "advertiser_id": advertiser_id, "campaign_id": campaign_id,
                        "slot_position": slot_position, "duration_seconds": random.choice([15, 30, 60]),
                        "rate_card_id": rate_card_id,
                        "price_idr": random.randint(15_000_000, 90_000_000),
                    })

            bulk_insert_returning_ids(conn, ratings_t, rating_rows)
            bulk_insert_returning_ids(conn, ad_slots_t, slot_rows)
            total_ratings += len(rating_rows)
            total_slots += len(slot_rows)

        # end of day: one ad_revenue rollup row per channel
        revenue_rows = [
            {
                "channel_id": channel_id,
                "air_date": air_date,
                "slot_count": random.randint(8, 16),
                "grp_delivered": round(random.uniform(50, 400), 2),
                "revenue_idr": random.randint(120_000_000, 900_000_000),
            }
            for channel_id in dims["channel_ids"]
        ]
        bulk_insert_returning_ids(conn, ad_revenue_t, revenue_rows)

    return total_airings, total_ratings, total_slots


def seed(engine: sa.Engine) -> None:
    meta = sa.MetaData()
    meta.reflect(bind=engine)
    programs_t = meta.tables["programs"]

    with engine.begin() as conn:
        if already_seeded(conn, programs_t):
            print("mcn_tv: programs already seeded — skipping (idempotent no-op)")
            return

        dims = _seed_dimensions(conn, meta)
        total_airings, total_ratings, total_slots = _seed_facts(conn, meta, dims)

    print(
        f"mcn_tv: seeded {len(CHANNELS)} channels, {len(PROGRAMS)} programs, "
        f"{sum(len(v) for v in dims['episode_ids_by_program'].values())} episodes, "
        f"{len(DMAS)} DMAs, {len(DEMOGRAPHIC_SEGMENTS)} demographic segments, "
        f"{len(ADVERTISER_NAMES)} advertisers, {len(dims['campaign_ids'])} campaigns, "
        f"{len(dims['rate_card_lookup'])} rate cards, {total_airings} airings, "
        f"{total_ratings} nielsen_ratings rows, {total_slots} ad_slots, "
        f"{SEED_DAYS * len(CHANNELS)} ad_revenue rollup rows."
    )
