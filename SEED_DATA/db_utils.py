"""Shared helpers for SEED_DATA's per-unit generators (ADR-0025).

Only the mechanics (idempotency check, bulk insert with ordered
RETURNING ids) are shared — each unit's dimension/fact content lives in
its own `<unit>_data.py`.
"""
import sqlalchemy as sa


def already_seeded(conn: sa.Connection, table: sa.Table) -> bool:
    """True if `table` already has rows — makes seeding a no-op on a
    second run, same guarantee the old per-unit seed scripts made."""
    count = conn.execute(sa.select(sa.func.count()).select_from(table)).scalar()
    return bool(count)


def bulk_insert_returning_ids(conn: sa.Connection, table: sa.Table, rows: list[dict]) -> list[int]:
    """Bulk-insert `rows` and return their generated `id`s in the same
    order as `rows` — relies on SQLAlchemy 2.0's "insertmanyvalues"
    feature, which preserves input order for a single-statement bulk
    INSERT ... RETURNING against PostgreSQL."""
    if not rows:
        return []
    result = conn.execute(sa.insert(table).returning(table.c.id), rows)
    return [row[0] for row in result.fetchall()]
