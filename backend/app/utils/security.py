"""
CLONEAI ULTRA — Security & JWT Authentication
===============================================
JWT token creation, verification, and FastAPI dependency injection
for protecting endpoints.

Usage in routers:
    from app.utils.security import require_user, get_current_user_optional

    @router.post("/protected")
    async def protected_endpoint(user: User = Depends(require_user)):
        ...

    @router.get("/optional-auth")
    async def optional_endpoint(user: Optional[User] = Depends(get_current_user_optional)):
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
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# ── Bearer Token Extraction ──
# auto_error=False: returns None instead of 401 when no token present
security_scheme = HTTPBearer(auto_error=False)


# ── Password Utilities ──

def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Token Creation ──

def create_access_token(
    user_id: str,
    email: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        user_id: UUID of the user (stored as "sub" claim)
        email: User's email (stored as "email" claim)
        expires_delta: Custom expiration time (default: 7 days)

    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": "cloneai-ultra",
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT access token.

    Returns:
        Payload dict with "sub" (user_id), "email", "exp", etc.

    Raises:
        JWTError: If token is invalid, expired, or tampered with
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


# ── FastAPI Dependency Injection ──

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Extract and validate the current user from a Bearer token.
    Returns None if no token provided or token is invalid.
    Use this for endpoints that work with or without auth.
    """
    if not credentials:
        return None

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")

        if user_id is None:
            return None

        # Look up user in database
        result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()

        if user is None:
            logger.warning("security.user_not_found", user_id=user_id)
            return None

        if not user.is_active:
            logger.warning("security.user_inactive", user_id=user_id)
            return None

        return user

    except JWTError as e:
        logger.debug("security.invalid_token", error=str(e))
        return None
    except Exception as e:
        logger.warning("security.auth_error", error=str(e))
        return None


async def require_user(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """
    Require a valid authenticated user. Raises 401 if not authenticated.
    Use this for endpoints that MUST have a logged-in user.
    """
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
    """
    Require an admin user. Raises 403 if user is not admin.
    """
    if user.plan != "enterprise":  # Only enterprise plan has admin access
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user


# ── Auth Router Helpers ──

async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> Optional[User]:
    """
    Authenticate a user by email and password.

    Returns:
        User object if credentials valid, None otherwise
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if user is None:
        return None

    if not user.hashed_password:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user
