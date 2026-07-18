"""Auth Endpoint (ADR-0021) - login only, no signup: accounts are seeded
(seed_users.py), not self-registered. Thin HTTP adapter - see
app/services/auth_service.py for the actual logic."""
from fastapi import APIRouter

from app.schemas.auth import LoginRequest, LoginResponse
from app.services import auth_service

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    return await auth_service.login(payload.email, payload.password)
