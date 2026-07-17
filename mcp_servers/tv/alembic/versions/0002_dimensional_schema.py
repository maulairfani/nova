"""dimensional schema — Nielsen-style ratings, ad sales, channels/programs (ADR-0023)

Drops the phase-1/2 flat schema (`programs`/`viewership_ratings`/
`ad_revenue`) and replaces it with a dimensional model: `channels`,
`programs`, `dma_regions`, `demographic_segments`, `advertisers`,
`ad_campaigns`, `rate_cards` (dimensions); `episodes`, `airings`,
`nielsen_ratings`, `ad_slots`, `ad_revenue` (facts).

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-17

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- drop the old flat schema ---
    op.drop_table("ad_revenue")
    op.drop_table("viewership_ratings")
    op.drop_table("programs")

    # --- dimensions ---

    op.create_table(
        "channels",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.Text, nullable=False, unique=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("coverage_type", sa.Text, nullable=False),
        sa.CheckConstraint("coverage_type IN ('national', 'regional')", name="ck_channels_coverage_type"),
    )

    op.create_table(
        "programs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("genre", sa.Text, nullable=False),
        sa.Column("format", sa.Text, nullable=False),
        sa.Column("production_type", sa.Text, nullable=False),
        sa.Column("premiere_date", sa.Date, nullable=False),
        sa.CheckConstraint(
            "format IN ('drama', 'variety', 'news', 'sports', 'reality', 'film', 'children')",
            name="ck_programs_format",
        ),
        sa.CheckConstraint(
            "production_type IN ('in_house', 'acquired')",
            name="ck_programs_production_type",
        ),
    )

    op.create_table(
        "dma_regions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.Text, nullable=False, unique=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("universe_estimate_households", sa.Integer, nullable=False),
        sa.Column("universe_estimate_persons", sa.Integer, nullable=False),
    )

    op.create_table(
        "demographic_segments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.Text, nullable=False, unique=True),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("min_age", sa.Integer, nullable=False),
        sa.Column("max_age", sa.Integer, nullable=True),
        sa.Column("gender", sa.Text, nullable=False),
        sa.CheckConstraint("gender IN ('all', 'male', 'female')", name="ck_demographic_segments_gender"),
    )

    op.create_table(
        "advertisers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("industry_sector", sa.Text, nullable=False),
    )

    op.create_table(
        "ad_campaigns",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("advertiser_id", sa.Integer, sa.ForeignKey("advertisers.id"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("target_demographic_segment_id", sa.Integer, sa.ForeignKey("demographic_segments.id"), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("target_grp", sa.Numeric(8, 2), nullable=False),
    )

    op.create_table(
        "rate_cards",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("daypart", sa.Text, nullable=False),
        sa.Column("demographic_segment_id", sa.Integer, sa.ForeignKey("demographic_segments.id"), nullable=False),
        sa.Column("price_per_grp_idr", sa.BigInteger, nullable=False),
        sa.Column("effective_start_date", sa.Date, nullable=False),
        sa.Column("effective_end_date", sa.Date, nullable=True),
        sa.CheckConstraint(
            "daypart IN ('prime_time', 'day_time', 'late_night')",
            name="ck_rate_cards_daypart",
        ),
    )

    # --- facts ---

    op.create_table(
        "episodes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("program_id", sa.Integer, sa.ForeignKey("programs.id"), nullable=False),
        sa.Column("season_number", sa.Integer, nullable=False),
        sa.Column("episode_number", sa.Integer, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("duration_minutes", sa.Integer, nullable=False),
    )

    op.create_table(
        "airings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("episode_id", sa.Integer, sa.ForeignKey("episodes.id"), nullable=False),
        sa.Column("channel_id", sa.Integer, sa.ForeignKey("channels.id"), nullable=False),
        sa.Column("air_date", sa.Date, nullable=False),
        sa.Column("air_time", sa.Time, nullable=False),
        sa.Column("daypart", sa.Text, nullable=False),
        sa.Column("is_rerun", sa.Boolean, nullable=False, server_default="false"),
        sa.CheckConstraint(
            "daypart IN ('prime_time', 'day_time', 'late_night')",
            name="ck_airings_daypart",
        ),
    )

    op.create_table(
        "nielsen_ratings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("airing_id", sa.Integer, sa.ForeignKey("airings.id"), nullable=False),
        sa.Column("dma_id", sa.Integer, sa.ForeignKey("dma_regions.id"), nullable=False),
        sa.Column("demographic_segment_id", sa.Integer, sa.ForeignKey("demographic_segments.id"), nullable=False),
        sa.Column("measurement_type", sa.Text, nullable=False),
        sa.Column("rating_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("share_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("grp", sa.Numeric(6, 2), nullable=False),
        sa.Column("hut_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("sample_size", sa.Integer, nullable=False),
        sa.CheckConstraint(
            "measurement_type IN ('overnight', 'live_plus_7')",
            name="ck_nielsen_ratings_measurement_type",
        ),
        sa.Index(
            "ix_nielsen_ratings_airing_dma_segment",
            "airing_id", "dma_id", "demographic_segment_id",
        ),
    )

    op.create_table(
        "ad_slots",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("airing_id", sa.Integer, sa.ForeignKey("airings.id"), nullable=False),
        sa.Column("advertiser_id", sa.Integer, sa.ForeignKey("advertisers.id"), nullable=False),
        sa.Column("campaign_id", sa.Integer, sa.ForeignKey("ad_campaigns.id"), nullable=True),
        sa.Column("slot_position", sa.Integer, nullable=False),
        sa.Column("duration_seconds", sa.Integer, nullable=False),
        sa.Column("rate_card_id", sa.Integer, sa.ForeignKey("rate_cards.id"), nullable=True),
        sa.Column("price_idr", sa.BigInteger, nullable=False),
    )

    op.create_table(
        "ad_revenue",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("channel_id", sa.Integer, sa.ForeignKey("channels.id"), nullable=False),
        sa.Column("air_date", sa.Date, nullable=False),
        sa.Column("slot_count", sa.Integer, nullable=False),
        sa.Column("grp_delivered", sa.Numeric(8, 2), nullable=False),
        sa.Column("revenue_idr", sa.BigInteger, nullable=False),
    )

    # Re-grant SELECT on the new tables to the read-only role (ADR-0016).
    # Belt-and-suspenders alongside 0001's `ALTER DEFAULT PRIVILEGES`,
    # which already covers tables created by the same migration role.
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcn_tv_readonly")


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM mcn_tv_readonly")

    op.drop_table("ad_revenue")
    op.drop_table("ad_slots")
    op.drop_table("nielsen_ratings")
    op.drop_table("airings")
    op.drop_table("episodes")
    op.drop_table("rate_cards")
    op.drop_table("ad_campaigns")
    op.drop_table("advertisers")
    op.drop_table("demographic_segments")
    op.drop_table("dma_regions")
    op.drop_table("programs")
    op.drop_table("channels")

    op.create_table(
        "programs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("genre", sa.Text, nullable=False),
        sa.Column("daypart", sa.Text, nullable=False),
        sa.Column("premiere_date", sa.Date, nullable=False),
        sa.CheckConstraint(
            "daypart IN ('prime_time', 'day_time', 'late_night')",
            name="ck_programs_daypart",
        ),
    )
    op.create_table(
        "viewership_ratings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("program_id", sa.Integer, sa.ForeignKey("programs.id"), nullable=False),
        sa.Column("air_date", sa.Date, nullable=False),
        sa.Column("rating", sa.Numeric(4, 2), nullable=False),
        sa.Column("households_reached", sa.Integer, nullable=False),
        sa.Column("region", sa.Text, nullable=False),
    )
    op.create_table(
        "ad_revenue",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("program_id", sa.Integer, sa.ForeignKey("programs.id"), nullable=False),
        sa.Column("air_date", sa.Date, nullable=False),
        sa.Column("slot_count", sa.Integer, nullable=False),
        sa.Column("revenue_idr", sa.BigInteger, nullable=False),
    )
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcn_tv_readonly")
