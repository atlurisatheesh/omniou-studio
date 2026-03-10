"""
routers/auth.py — Authentication endpoints (Phase 12).

POST /auth/login    → { access_token, refresh_token, token_type, expires_in }
POST /auth/refresh  → { access_token, refresh_token, token_type, expires_in }
POST /auth/logout   → { message }
GET  /auth/me       → UserResponse
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db, User
from app.utils.security import (
    verify_password,
    create_token_pair,
    refresh_access_token,
    logout_token,
    get_current_user,
    bearer_scheme,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Schemas ──
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    plan: str
    videos_used: int
    videos_limit: int

    class Config:
        from_attributes = True


# ── Endpoints ──
@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user: Optional[User] = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    return create_token_pair(str(user.id), user.email)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await refresh_access_token(body.refresh_token, db)


@router.post("/logout")
async def logout(
    body: LogoutRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    access_token = credentials.credentials if credentials else None
    if access_token:
        logout_token(access_token, body.refresh_token)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
