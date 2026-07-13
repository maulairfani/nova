"""Auth Endpoint (ADR-0021) - login only, no signup: accounts are seeded
(seed_users.py), not self-registered."""
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.db import async_session
from app.core.security import create_access_token, verify_password
from app.models import User, UserBusinessUnit
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    async with async_session() as session:
        user = (await session.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
        if user is None or not user.is_active or not user.password_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        memberships = (
            (await session.execute(select(UserBusinessUnit).where(UserBusinessUnit.user_id == user.id)))
            .scalars()
            .all()
        )

    # Claims embedded at login time (stateless JWT, no per-request DB hit) -
    # a membership change only takes effect on the user's next login.
    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "business_units": [
                {"code": m.business_unit_code, "role": m.role_code} for m in memberships
            ],
        }
    )
    return LoginResponse(access_token=token)
