"""Ominou Studio — Shared configuration across all services."""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class StudioSettings(BaseSettings):
    # Core
    APP_NAME: str = "Ominou Studio"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "ominou-studio-secret-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ominou_studio.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Storage
    S3_BUCKET: str = os.getenv("S3_BUCKET", "ominou-studio-assets")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "./storage")

    # AI API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    STABILITY_API_KEY: Optional[str] = os.getenv("STABILITY_API_KEY")
    ELEVENLABS_API_KEY: Optional[str] = os.getenv("ELEVENLABS_API_KEY")

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")

    # Service URLs (internal)
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    VOICE_SERVICE_URL: str = "http://localhost:8002"
    DESIGN_SERVICE_URL: str = "http://localhost:8003"
    CODE_SERVICE_URL: str = "http://localhost:8004"
    VIDEO_SERVICE_URL: str = "http://localhost:8005"
    WRITER_SERVICE_URL: str = "http://localhost:8006"
    MUSIC_SERVICE_URL: str = "http://localhost:8007"
    WORKFLOW_SERVICE_URL: str = "http://localhost:8008"
    BILLING_SERVICE_URL: str = "http://localhost:8009"
    STORAGE_SERVICE_URL: str = "http://localhost:8010"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # Credits
    FREE_MONTHLY_CREDITS: int = 50
    PRO_MONTHLY_CREDITS: int = 2000
    TEAM_MONTHLY_CREDITS: int = 10000

    class Config:
        env_file = ".env"
        extra = "allow"


settings = StudioSettings()
