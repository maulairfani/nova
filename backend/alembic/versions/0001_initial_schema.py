"""initial schema - users, business_units (incl. virtual "group" unit), business_unit_roles, membership

Generated from app/models.py via `alembic revision --autogenerate` - edit
models.py and regenerate for future schema changes, rather than hand-editing
migrations independently of it.

Revision ID: 0001
Revises:
Create Date: 2026-07-13

"""
from alembic import op
import sqlalchemy as sa


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_unit_roles",
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "business_units",
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "user_business_units",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("business_unit_code", sa.Text(), nullable=False),
        sa.Column("role_code", sa.Text(), server_default="employee", nullable=False),
        sa.ForeignKeyConstraint(["business_unit_code"], ["business_units.code"]),
        sa.ForeignKeyConstraint(["role_code"], ["business_unit_roles.code"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "business_unit_code"),
    )

    # Seed data (not something autogenerate detects - added by hand).
    op.execute(
        """
        INSERT INTO business_units (code, name) VALUES
            ('tv', 'MCN TV'),
            ('plus', 'MCN+'),
            ('news', 'MCN News'),
            ('group', 'MCN Group')
        """
    )
    op.execute(
        """
        INSERT INTO business_unit_roles (code, name) VALUES
            ('employee', 'Employee'),
            ('finance', 'Finance'),
            ('admin', 'Admin (Cross-Unit)')
        """
    )


def downgrade() -> None:
    op.drop_table("user_business_units")
    op.drop_table("users")
    op.drop_table("business_units")
    op.drop_table("business_unit_roles")
