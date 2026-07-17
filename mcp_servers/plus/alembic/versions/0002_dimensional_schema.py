"""dimensional schema — titles/seasons/episodes, subscriptions, coins, licensing (ADR-0023)

Drops the phase-1/2 flat schema (`titles`/`engagement`/`revenue`) and
replaces it with a dimensional model covering both MCN+ products
(streaming + shorts, ADR-0014): `titles`, `seasons`, `episodes`,
`subscription_plans`, `coin_packages`, `subscribers`, `devices`,
`regions`, `licensors` (dimensions); `engagement`, `subscriptions`,
`subscription_transactions`, `coin_transactions`,
`content_licensing_costs`, `revenue` (facts).

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
    op.drop_table("revenue")
    op.drop_table("engagement")
    op.drop_table("titles")

    # --- dimensions ---

    op.create_table(
        "regions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
    )

    op.create_table(
        "devices",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("device_type", sa.Text, nullable=False),
        sa.Column("platform", sa.Text, nullable=False),
        sa.CheckConstraint("device_type IN ('mobile', 'smart_tv', 'web', 'tablet')", name="ck_devices_device_type"),
        sa.CheckConstraint("platform IN ('ios', 'android', 'web', 'tvos', 'other')", name="ck_devices_platform"),
    )

    op.create_table(
        "licensors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("country", sa.Text, nullable=False),
    )

    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.Text, nullable=False, unique=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("price_idr", sa.BigInteger, nullable=False),
        sa.Column("max_concurrent_streams", sa.Integer, nullable=False),
    )

    op.create_table(
        "coin_packages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.Text, nullable=False, unique=True),
        sa.Column("coin_amount", sa.Integer, nullable=False),
        sa.Column("price_idr", sa.BigInteger, nullable=False),
    )

    op.create_table(
        "titles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("product", sa.Text, nullable=False),
        sa.Column("content_type", sa.Text, nullable=False),
        sa.Column("genre", sa.Text, nullable=False),
        sa.Column("maturity_rating", sa.Text, nullable=False),
        sa.Column("licensor_id", sa.Integer, sa.ForeignKey("licensors.id"), nullable=True),
        sa.Column("release_date", sa.Date, nullable=False),
        sa.CheckConstraint("product IN ('streaming', 'shorts')", name="ck_titles_product"),
        sa.CheckConstraint("content_type IN ('movie', 'series', 'microdrama')", name="ck_titles_content_type"),
        sa.CheckConstraint("maturity_rating IN ('SU', '13+', '17+', '21+')", name="ck_titles_maturity_rating"),
    )

    op.create_table(
        "seasons",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title_id", sa.Integer, sa.ForeignKey("titles.id"), nullable=False),
        sa.Column("season_number", sa.Integer, nullable=False),
    )

    op.create_table(
        "subscribers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("external_subscriber_code", sa.Text, nullable=False, unique=True),
        sa.Column("signup_date", sa.Date, nullable=False),
        sa.Column("region_id", sa.Integer, sa.ForeignKey("regions.id"), nullable=False),
        sa.Column("primary_device_id", sa.Integer, sa.ForeignKey("devices.id"), nullable=True),
    )

    # --- facts ---

    op.create_table(
        "episodes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title_id", sa.Integer, sa.ForeignKey("titles.id"), nullable=False),
        sa.Column("season_id", sa.Integer, sa.ForeignKey("seasons.id"), nullable=True),
        sa.Column("episode_number", sa.Integer, nullable=False),
        sa.Column("duration_seconds", sa.Integer, nullable=False),
        sa.Column("release_date", sa.Date, nullable=False),
    )

    op.create_table(
        "engagement",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title_id", sa.Integer, sa.ForeignKey("titles.id"), nullable=False),
        sa.Column("episode_id", sa.Integer, sa.ForeignKey("episodes.id"), nullable=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("product", sa.Text, nullable=False),
        sa.Column("device_id", sa.Integer, sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("region_id", sa.Integer, sa.ForeignKey("regions.id"), nullable=False),
        sa.Column("watch_minutes", sa.Integer, nullable=False),
        sa.Column("completion_rate", sa.Numeric(4, 2), nullable=False),
        sa.Column("viewers", sa.Integer, nullable=False),
        sa.CheckConstraint("product IN ('streaming', 'shorts')", name="ck_engagement_product"),
        sa.Index("ix_engagement_title_date", "title_id", "date"),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("subscriber_id", sa.Integer, sa.ForeignKey("subscribers.id"), nullable=False),
        sa.Column("plan_id", sa.Integer, sa.ForeignKey("subscription_plans.id"), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("churn_reason", sa.Text, nullable=True),
        sa.CheckConstraint("status IN ('active', 'paused', 'churned')", name="ck_subscriptions_status"),
    )

    op.create_table(
        "subscription_transactions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("subscriber_id", sa.Integer, sa.ForeignKey("subscribers.id"), nullable=False),
        sa.Column("plan_id", sa.Integer, sa.ForeignKey("subscription_plans.id"), nullable=False),
        sa.Column("billing_date", sa.Date, nullable=False),
        sa.Column("amount_idr", sa.BigInteger, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.CheckConstraint("status IN ('paid', 'failed', 'refunded')", name="ck_subscription_transactions_status"),
    )

    op.create_table(
        "coin_transactions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("subscriber_id", sa.Integer, sa.ForeignKey("subscribers.id"), nullable=False),
        sa.Column("coin_package_id", sa.Integer, sa.ForeignKey("coin_packages.id"), nullable=False),
        sa.Column("title_id", sa.Integer, sa.ForeignKey("titles.id"), nullable=True),
        sa.Column("transaction_date", sa.Date, nullable=False),
        sa.Column("coins_spent", sa.Integer, nullable=False),
        sa.Column("amount_idr", sa.BigInteger, nullable=False),
    )

    op.create_table(
        "content_licensing_costs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title_id", sa.Integer, sa.ForeignKey("titles.id"), nullable=False),
        sa.Column("licensor_id", sa.Integer, sa.ForeignKey("licensors.id"), nullable=False),
        sa.Column("license_fee_idr", sa.BigInteger, nullable=False),
        sa.Column("license_start_date", sa.Date, nullable=False),
        sa.Column("license_end_date", sa.Date, nullable=False),
    )

    op.create_table(
        "revenue",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("product", sa.Text, nullable=False),
        sa.Column("subscription_revenue_idr", sa.BigInteger, nullable=False),
        sa.Column("coin_revenue_idr", sa.BigInteger, nullable=False),
        sa.Column("active_subscribers", sa.Integer, nullable=False),
        sa.CheckConstraint("product IN ('streaming', 'shorts')", name="ck_revenue_product"),
    )

    # Re-grant SELECT on the new tables to the read-only role (ADR-0016).
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcn_plus_readonly")


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM mcn_plus_readonly")

    op.drop_table("revenue")
    op.drop_table("content_licensing_costs")
    op.drop_table("coin_transactions")
    op.drop_table("subscription_transactions")
    op.drop_table("subscriptions")
    op.drop_table("engagement")
    op.drop_table("episodes")
    op.drop_table("subscribers")
    op.drop_table("seasons")
    op.drop_table("titles")
    op.drop_table("coin_packages")
    op.drop_table("subscription_plans")
    op.drop_table("licensors")
    op.drop_table("devices")
    op.drop_table("regions")

    op.create_table(
        "titles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("product", sa.Text, nullable=False),
        sa.Column("genre", sa.Text, nullable=False),
        sa.Column("release_date", sa.Date, nullable=False),
        sa.CheckConstraint("product IN ('streaming', 'shorts')", name="ck_titles_product"),
    )
    op.create_table(
        "engagement",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title_id", sa.Integer, sa.ForeignKey("titles.id"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("watch_minutes", sa.Integer, nullable=False),
        sa.Column("completion_rate", sa.Numeric(4, 2), nullable=False),
        sa.Column("viewers", sa.Integer, nullable=False),
        sa.Column("product", sa.Text, nullable=False),
        sa.CheckConstraint("product IN ('streaming', 'shorts')", name="ck_engagement_product"),
    )
    op.create_table(
        "revenue",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("product", sa.Text, nullable=False),
        sa.Column("subscription_revenue_idr", sa.BigInteger, nullable=False),
        sa.Column("coin_revenue_idr", sa.BigInteger, nullable=False),
        sa.Column("active_subscribers", sa.Integer, nullable=False),
        sa.CheckConstraint("product IN ('streaming', 'shorts')", name="ck_revenue_product"),
    )
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcn_plus_readonly")
