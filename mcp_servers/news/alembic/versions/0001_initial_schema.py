"""initial schema — articles, article_engagement, ad_revenue, readonly role

Revision ID: 0001
Revises:
Create Date: 2026-07-12

"""
from alembic import op
import sqlalchemy as sa

from config import settings

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
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

    # Read-only role for the SQL Analytics Tool's runtime connection (ADR-0016).
    # Password comes from settings (NEWS_DB_READONLY_PASSWORD), never hardcoded.
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mcn_news_readonly') THEN
                    CREATE ROLE mcn_news_readonly LOGIN PASSWORD :password;
                END IF;
            END
            $$;
            """
        ).bindparams(password=settings.news_db_readonly_password)
    )
    op.execute("GRANT CONNECT ON DATABASE mcn_news TO mcn_news_readonly")
    op.execute("GRANT USAGE ON SCHEMA public TO mcn_news_readonly")
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcn_news_readonly")
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO mcn_news_readonly"
    )


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM mcn_news_readonly")
    op.drop_table("ad_revenue")
    op.drop_table("article_engagement")
    op.drop_table("articles")
