"""Authentication routes — register, login, token refresh."""
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
from shared.database import get_db
from shared.auth import create_access_token, get_current_user, create_api_key_token
from ..models import (
    User, APIKey, UserRegister, UserLogin, UserResponse, TokenResponse,
    UserUpdate, APIKeyCreate, APIKeyResponse, PasswordChange, CreditUsage,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

auth_router = APIRouter()
users_router = APIRouter()


# ─── Authentication ──────────────────────────────────────────────
@auth_router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=data.email,
        password_hash=pwd_context.hash(data.password),
        full_name=data.full_name,
        company=data.company,
        plan="free",
        credits_remaining=50,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email, "plan": user.plan})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@auth_router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    token = create_access_token({"sub": str(user.id), "email": user.email, "plan": user.plan})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@auth_router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


# ─── User Profile ──────────────────────────────────────────────
@users_router.put("/profile", response_model=UserResponse)
async def update_profile(data: UserUpdate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@users_router.post("/change-password")
async def change_password(data: PasswordChange, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one_or_none()
    if not user or not pwd_context.verify(data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    user.password_hash = pwd_context.hash(data.new_password)
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Password changed successfully"}


@users_router.get("/credits", response_model=CreditUsage)
async def get_credits(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return CreditUsage(credits_remaining=user.credits_remaining, credits_used_total=user.credits_used_total, plan=user.plan)


# ─── API Keys ──────────────────────────────────────────────
@users_router.post("/api-keys", response_model=dict, status_code=201)
async def create_api_key(data: APIKeyCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    raw_key = f"osk_{secrets.token_urlsafe(32)}"
    key_obj = APIKey(
        user_id=current_user["id"],
        name=data.name,
        key_hash=pwd_context.hash(raw_key),
        key_prefix=raw_key[:12],
        permissions=data.permissions or "*",
    )
    db.add(key_obj)
    await db.commit()
    await db.refresh(key_obj)
    return {"key": raw_key, "id": key_obj.id, "name": key_obj.name, "prefix": key_obj.key_prefix}


@users_router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(APIKey).where(APIKey.user_id == current_user["id"], APIKey.is_active == True))
    return [APIKeyResponse.model_validate(k) for k in result.scalars().all()]


@users_router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user["id"]))
    key_obj = result.scalar_one_or_none()
    if not key_obj:
        raise HTTPException(status_code=404, detail="API key not found")
    key_obj.is_active = False
    await db.commit()
    return {"message": "API key deleted"}
