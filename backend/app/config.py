"""
AGRISENSE — Application Configuration
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AgriSense"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True

    DATABASE_URL: str = "sqlite+aiosqlite:///./agrisense_dev.db"

    JWT_SECRET: str = "agrisense-dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    WEATHER_API_KEY: str = ""
    WEATHER_API_URL: str = "https://api.openweathermap.org/data/2.5"

    MARKET_API_KEY: str = ""

    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
