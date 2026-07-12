"""initial schema — titles, engagement, revenue, readonly role

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
        "titles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("product", sa.Text, nullable=False),
        sa.Column("genre", sa.Text, nullable=False),
        sa.Column("release_date", sa.Date, nullable=False),
        sa.CheckConstraint(
            "product IN ('streaming', 'shorts')",
            name="ck_titles_product",
        ),
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
        sa.CheckConstraint(
            "product IN ('streaming', 'shorts')",
            name="ck_engagement_product",
        ),
    )

    op.create_table(
        "revenue",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("product", sa.Text, nullable=False),
        sa.Column("subscription_revenue_idr", sa.BigInteger, nullable=False),
        sa.Column("coin_revenue_idr", sa.BigInteger, nullable=False),
        sa.Column("active_subscribers", sa.Integer, nullable=False),
        sa.CheckConstraint(
            "product IN ('streaming', 'shorts')",
            name="ck_revenue_product",
        ),
    )

    # Read-only role for the SQL Analytics Tool's runtime connection (ADR-0016).
    # Password comes from settings (PLUS_DB_READONLY_PASSWORD), never hardcoded.
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mcn_plus_readonly') THEN
                    CREATE ROLE mcn_plus_readonly LOGIN PASSWORD :password;
                END IF;
            END
            $$;
            """
        ).bindparams(password=settings.plus_db_readonly_password)
    )
    op.execute("GRANT CONNECT ON DATABASE mcn_plus TO mcn_plus_readonly")
    op.execute("GRANT USAGE ON SCHEMA public TO mcn_plus_readonly")
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcn_plus_readonly")
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO mcn_plus_readonly"
    )


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM mcn_plus_readonly")
    op.drop_table("revenue")
    op.drop_table("engagement")
    op.drop_table("titles")
