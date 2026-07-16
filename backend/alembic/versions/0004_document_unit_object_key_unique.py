"""add unique constraint on documents (business_unit_code, object_key)

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-16 09:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_documents_unit_object_key", "documents", ["business_unit_code", "object_key"])


def downgrade() -> None:
    op.drop_constraint("uq_documents_unit_object_key", "documents", type_="unique")
