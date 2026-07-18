"""Auth business logic (ADR-0021): verifying credentials and shaping the
JWT's embedded claims. app/api/v1/endpoints/auth.py stays a thin HTTP
adapter around this."""
from fastapi import HTTPException

from app.core.db import async_session
from app.core.security import create_access_token, verify_password
from app.repositories import user_repository
from app.schemas.auth import LoginResponse


async def login(email: str, password: str) -> LoginResponse:
    async with async_session() as session:
        user = await user_repository.get_by_email(session, email)
        if user is None or not user.is_active or not user.password_hash:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        memberships = await user_repository.list_business_units(session, user.id)

    # Claims embedded at login time (stateless JWT, no per-request DB hit) -
    # a membership change only takes effect on the user's next login.
    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "business_units": [{"code": m.business_unit_code, "role": m.role_code} for m in memberships],
        }
    )
    return LoginResponse(access_token=token)
