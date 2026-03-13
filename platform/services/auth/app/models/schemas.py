"""Pydantic schemas for auth service."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
    company: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    plan: str = "free"
    credits_remaining: int = 50
    is_verified: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    timezone_str: Optional[str] = None
    language: Optional[str] = None
    avatar_url: Optional[str] = None


class APIKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    permissions: Optional[str] = "*"


class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    permissions: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class CreditUsage(BaseModel):
    credits_remaining: int
    credits_used_total: int
    plan: str
