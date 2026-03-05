"""
CLONEAI ULTRA — User Router
=============================
User profile, plan management, and authentication endpoints.
Includes JWT token issuance for login/register.
"""

import uuid
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import User, get_db
from ..models.schemas import UserCreate, UserResponse, UserUpdateRequest
from ..utils.security import (
    authenticate_user,
    create_access_token,
    hash_password,
    require_user,
)

router = APIRouter()
logger = structlog.get_logger()


# ── Auth Models ──

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Auth Endpoints ──

@router.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return a JWT access token.
    Use the token in the Authorization header: Bearer <token>
    """
    user = await authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user_id=str(user.id), email=user.email)
    logger.info("auth.login", user_id=str(user.id), email=user.email)

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            plan=user.plan,
            videos_used=user.videos_used,
            videos_limit=user.videos_limit,
            created_at=user.created_at,
        ),
    )


@router.get("/auth/me", response_model=UserResponse)
async def get_me(user: User = Depends(require_user)):
    """Get the currently authenticated user's profile."""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        plan=user.plan,
        videos_used=user.videos_used,
        videos_limit=user.videos_limit,
        created_at=user.created_at,
    )


@router.post("/user", response_model=UserResponse)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user (or return existing by email)."""
    result = await db.execute(select(User).where(User.email == body.email))
    existing = result.scalar_one_or_none()
    if existing:
        return UserResponse(
            id=str(existing.id),
            email=existing.email,
            name=existing.name,
            plan=existing.plan,
            videos_used=existing.videos_used,
            videos_limit=existing.videos_limit,
            created_at=existing.created_at,
        )

    user = User(
        id=uuid.uuid4(),
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password) if body.password else None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("user.created", user_id=str(user.id), email=user.email)
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        plan=user.plan,
        videos_used=user.videos_used,
        videos_limit=user.videos_limit,
        created_at=user.created_at,
    )


@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get user profile by ID."""
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        plan=user.plan,
        videos_used=user.videos_used,
        videos_limit=user.videos_limit,
        created_at=user.created_at,
    )


@router.get("/user/by-email/{email}", response_model=UserResponse)
async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    """Get user profile by email."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        plan=user.plan,
        videos_used=user.videos_used,
        videos_limit=user.videos_limit,
        created_at=user.created_at,
    )


@router.put("/user/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update user profile."""
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.name is not None:
        user.name = body.name
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url
    user.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        plan=user.plan,
        videos_used=user.videos_used,
        videos_limit=user.videos_limit,
        created_at=user.created_at,
    )


@router.get("/user/{user_id}/usage")
async def get_usage(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get user's plan usage stats."""
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "plan": user.plan,
        "videos_used": user.videos_used,
        "videos_limit": user.videos_limit,
        "remaining": max(0, user.videos_limit - user.videos_used),
        "can_generate": user.videos_used < user.videos_limit,
    }
