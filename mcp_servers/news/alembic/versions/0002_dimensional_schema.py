"""dimensional schema — desks/authors/platforms, corrections (ADR-0023)

Drops the phase-1/2 flat schema (`articles`/`article_engagement`/
`ad_revenue`) and replaces it with a dimensional model: `desks`,
`authors`, `platforms`, `ad_slot_types` (dimensions); `articles`,
`article_engagement`, `ad_revenue`, `corrections` (facts).

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
    op.drop_table("article_engagement")
    op.drop_table("articles")

    # --- dimensions ---

    op.create_table(
        "desks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.Text, nullable=False, unique=True),
        sa.Column("name", sa.Text, nullable=False),
    )

    op.create_table(
        "authors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("desk_id", sa.Integer, sa.ForeignKey("desks.id"), nullable=False),
    )

    op.create_table(
        "platforms",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.Text, nullable=False, unique=True),
        sa.Column("name", sa.Text, nullable=False),
    )

    op.create_table(
        "ad_slot_types",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.Text, nullable=False, unique=True),
        sa.Column("name", sa.Text, nullable=False),
    )

    # --- facts ---

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("headline", sa.Text, nullable=False),
        sa.Column("desk_id", sa.Integer, sa.ForeignKey("desks.id"), nullable=False),
        sa.Column("author_id", sa.Integer, sa.ForeignKey("authors.id"), nullable=False),
        sa.Column("content_type", sa.Text, nullable=False),
        sa.Column("publish_date", sa.Date, nullable=False),
        sa.Column("is_breaking", sa.Boolean, nullable=False, server_default="false"),
        sa.CheckConstraint("content_type IN ('text', 'video', 'live_blog')", name="ck_articles_content_type"),
    )

    op.create_table(
        "article_engagement",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("article_id", sa.Integer, sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("platform_id", sa.Integer, sa.ForeignKey("platforms.id"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("page_views", sa.Integer, nullable=False),
        sa.Column("unique_visitors", sa.Integer, nullable=False),
        sa.Column("avg_time_on_page_seconds", sa.Integer, nullable=False),
        sa.Column("social_shares", sa.Integer, nullable=False),
        sa.Index("ix_article_engagement_article_date", "article_id", "date"),
    )

    op.create_table(
        "ad_revenue",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("ad_slot_type_id", sa.Integer, sa.ForeignKey("ad_slot_types.id"), nullable=False),
        sa.Column("platform_id", sa.Integer, sa.ForeignKey("platforms.id"), nullable=False),
        sa.Column("impressions", sa.BigInteger, nullable=False),
        sa.Column("revenue_idr", sa.BigInteger, nullable=False),
    )

    op.create_table(
        "corrections",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("article_id", sa.Integer, sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("correction_date", sa.Date, nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("severity", sa.Text, nullable=False),
        sa.CheckConstraint("severity IN ('minor', 'major', 'retraction')", name="ck_corrections_severity"),
    )

    # Re-grant SELECT on the new tables to the read-only role (ADR-0016).
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcn_news_readonly")


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM mcn_news_readonly")

    op.drop_table("corrections")
    op.drop_table("ad_revenue")
    op.drop_table("article_engagement")
    op.drop_table("articles")
    op.drop_table("ad_slot_types")
    op.drop_table("platforms")
    op.drop_table("authors")
    op.drop_table("desks")

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("headline", sa.Text, nullable=False),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("publish_date", sa.Date, nullable=False),
    )
    op.create_table(
        "article_engagement",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("article_id", sa.Integer, sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("page_views", sa.Integer, nullable=False),
        sa.Column("unique_visitors", sa.Integer, nullable=False),
        sa.Column("avg_time_on_page_seconds", sa.Integer, nullable=False),
    )
    op.create_table(
        "ad_revenue",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("ad_slot_type", sa.Text, nullable=False),
        sa.Column("revenue_idr", sa.BigInteger, nullable=False),
    )
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcn_news_readonly")
