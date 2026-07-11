"""initial schema — programs, viewership_ratings, ad_revenue, readonly role

Revision ID: 0001
Revises:
Create Date: 2026-07-11

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

    # Read-only role for the SQL Analytics Tool's runtime connection (ADR-0016).
    # Password comes from settings (TV_DB_READONLY_PASSWORD), never hardcoded.
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mcn_tv_readonly') THEN
                    CREATE ROLE mcn_tv_readonly LOGIN PASSWORD :password;
                END IF;
            END
            $$;
            """
        ).bindparams(password=settings.tv_db_readonly_password)
    )
    op.execute("GRANT CONNECT ON DATABASE mcn_tv TO mcn_tv_readonly")
    op.execute("GRANT USAGE ON SCHEMA public TO mcn_tv_readonly")
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcn_tv_readonly")
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO mcn_tv_readonly"
    )


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM mcn_tv_readonly")
    op.drop_table("ad_revenue")
    op.drop_table("viewership_ratings")
    op.drop_table("programs")
