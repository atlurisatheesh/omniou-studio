"""
CLONEAI ULTRA — Security & JWT Authentication (Phase 12)
=========================================================
JWT with refresh tokens, Redis-backed blacklist, token rotation.

Usage in routers:
    from app.utils.security import require_user, get_current_user_optional

    @router.post("/protected")
    async def protected_endpoint(user: User = Depends(require_user)):
        ...
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.database import User, get_db

logger = structlog.get_logger()

# ── Password Hashing ──
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── JWT Config ──
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

# ── Bearer Token Extraction ──
bearer_scheme = HTTPBearer(auto_error=False)
# Keep old alias for backward compat
security_scheme = bearer_scheme


# ── Password Utilities ──

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ── Redis Blacklist Helpers ──

def _get_redis():
    try:
        import redis as _redis
        r = _redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.ping()
        return r
    except Exception:
        return None


def _blacklist_key(jti: str) -> str:
    return f"cloneai:token:blacklist:{jti}"


def blacklist_token(jti: str, expires_in_seconds: int) -> None:
    r = _get_redis()
    if r:
        r.setex(_blacklist_key(jti), expires_in_seconds, "1")


def is_token_blacklisted(jti: str) -> bool:
    r = _get_redis()
    if r:
        return r.exists(_blacklist_key(jti)) > 0
    return False


# ── Token Creation ──

def _make_token(
    subject: str,
    token_type: str,
    expire_delta: timedelta,
    extra_claims: Optional[dict] = None,
) -> tuple:
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": now,
        "exp": now + expire_delta,
        "iss": "cloneai-ultra",
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token, jti


def create_access_token(user_id: str, email: str, expires_delta: Optional[timedelta] = None) -> tuple:
    return _make_token(
        subject=str(user_id),
        token_type=ACCESS_TOKEN_TYPE,
        expire_delta=expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims={"email": email},
    )


def create_refresh_token(user_id: str) -> tuple:
    return _make_token(
        subject=str(user_id),
        token_type=REFRESH_TOKEN_TYPE,
        expire_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )


def create_token_pair(user_id: str, email: str) -> dict:
    access_token, _ = create_access_token(user_id, email)
    refresh_token, _ = create_refresh_token(user_id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def decode_token(token: str) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise credentials_exception
    jti = payload.get("jti", "")
    if jti and is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


# Backward compat alias
def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


# ── FastAPI Dependencies ──

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise credentials_exception

    payload = decode_token(credentials.credentials)
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — use access token",
        )
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def require_user(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_admin(
    user: User = Depends(require_user),
) -> User:
    if user.plan != "enterprise":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user


# ── Auth Router Helpers ──

async def authenticate_user(
    db: AsyncSession, email: str, password: str,
) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def refresh_access_token(refresh_token: str, db: AsyncSession) -> dict:
    payload = decode_token(refresh_token)
    if payload.get("type") != REFRESH_TOKEN_TYPE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — use refresh token",
        )
    user_id = payload.get("sub")
    jti = payload.get("jti", "")
    exp = payload.get("exp", 0)

    # Blacklist used refresh token (rotation)
    now_ts = int(datetime.now(timezone.utc).timestamp())
    remaining_ttl = max(exp - now_ts, 1)
    blacklist_token(jti, remaining_ttl)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return create_token_pair(str(user.id), user.email)


def logout_token(access_token: str, refresh_token: Optional[str] = None) -> None:
    for token in filter(None, [access_token, refresh_token]):
        try:
            payload = decode_token(token)
            jti = payload.get("jti", "")
            exp = payload.get("exp", 0)
            now_ts = int(datetime.now(timezone.utc).timestamp())
            ttl = max(exp - now_ts, 1)
            blacklist_token(jti, ttl)
        except HTTPException:
            pass
