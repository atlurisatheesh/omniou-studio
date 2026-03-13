"""JWT authentication utilities shared across services."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_api_key_token(user_id: int, key_name: str) -> str:
    return jwt.encode(
        {"sub": str(user_id), "type": "api_key", "name": key_name, "iat": datetime.now(timezone.utc)},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    return {
        "id": int(user_id),
        "email": payload.get("email", ""),
        "plan": payload.get("plan", "free"),
        "type": payload.get("type", "access"),
    }


def require_plan(min_plan: str):
    """Dependency that requires a minimum plan level."""
    plan_levels = {"free": 0, "pro": 1, "team": 2, "enterprise": 3}

    async def check_plan(user: dict = Depends(get_current_user)):
        user_level = plan_levels.get(user.get("plan", "free"), 0)
        required_level = plan_levels.get(min_plan, 0)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {min_plan} plan or higher",
            )
        return user

    return check_plan
