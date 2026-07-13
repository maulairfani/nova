"""One-off dummy-user seed for nova_core (ADR-0021). Run after
`alembic upgrade head`. No signup flow exists - accounts are seeded here,
not self-registered.

Usage: python seed_users.py
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import User, UserBusinessUnit

DEFAULT_PASSWORD = "Nova123!"  # dev-only dummy credential, same for every seeded user

USERS = [
    {
        "email": "andi.wijaya@mcngroup.example",
        "display_name": "Andi Wijaya",
        "memberships": [("tv", "employee")],
    },
    {
        "email": "budi.santoso@mcngroup.example",
        "display_name": "Budi Santoso",
        "memberships": [("plus", "finance")],
    },
    {
        "email": "citra.lestari@mcngroup.example",
        "display_name": "Citra Lestari",
        "memberships": [("news", "employee")],
    },
    {
        "email": "dewi.anggraini@mcngroup.example",
        "display_name": "Dewi Anggraini",  # HR, corporate - no unit-specific data access
        "memberships": [("group", "employee")],
    },
    {
        "email": "eko.prasetyo@mcngroup.example",
        "display_name": "Eko Prasetyo",  # Platform/Engineering - cross-unit access
        "memberships": [("group", "admin")],
    },
    {
        "email": "fajar.nugroho@mcngroup.example",
        "display_name": "Fajar Nugroho",  # works across two units at once
        "memberships": [("tv", "employee"), ("plus", "employee")],
    },
]


def seed() -> None:
    engine = create_engine(settings.core_database_admin_url)
    with Session(engine) as session:
        existing = session.query(User).count()
        if existing:
            print(f"users already has {existing} rows — skipping seed (idempotent no-op)")
            return

        for u in USERS:
            user = User(
                email=u["email"],
                password_hash=hash_password(DEFAULT_PASSWORD),
                display_name=u["display_name"],
            )
            session.add(user)
            session.flush()  # populate user.id
            for business_unit_code, role_code in u["memberships"]:
                session.add(
                    UserBusinessUnit(
                        user_id=user.id,
                        business_unit_code=business_unit_code,
                        role_code=role_code,
                    )
                )
        session.commit()

    print(f"Seeded {len(USERS)} users (password: {DEFAULT_PASSWORD!r} for all — dev only).")


if __name__ == "__main__":
    seed()
