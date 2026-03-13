"""
AGRISENSE — Auth Router
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.database import User, get_db
from ..models.schemas import UserCreate, UserLogin, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _create_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        phone=user.phone,
        language=user.language,
        region=user.region,
        plan=user.plan,
        farm_size_acres=user.farm_size_acres,
        primary_crops=user.primary_crops,
        soil_type=user.soil_type,
        irrigation_type=user.irrigation_type,
    )


@router.post("/register", response_model=TokenResponse)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=body.name,
        email=body.email,
        phone=body.phone,
        language=body.language,
        region=body.region,
        hashed_password=pwd_context.hash(body.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return TokenResponse(
        access_token=_create_token(str(user.id)),
        user=_user_response(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not pwd_context.verify(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return TokenResponse(
        access_token=_create_token(str(user.id)),
        user=_user_response(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(db: AsyncSession = Depends(get_db)):
    # In production: extract user from JWT token
    # For demo: return first user or raise
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _user_response(user)
