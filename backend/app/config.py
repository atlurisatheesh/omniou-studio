"""
CLONEAI ULTRA — Application Configuration
==========================================
Centralized settings using pydantic-settings.
All values configurable via environment variables or .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_NAME: str = "CloneAI Ultra"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://cloneai:cloneai_secret@localhost:5432/cloneai_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # MinIO (S3-compatible storage)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "cloneai_minio"
    MINIO_SECRET_KEY: str = "cloneai_minio_secret"
    MINIO_BUCKET: str = "cloneai-uploads"
    MINIO_USE_SSL: bool = False
    USE_MINIO: bool = False  # Set True when MinIO is running

    # Auth
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AI Models — Voice
    MODEL_CACHE_DIR: str = "./models"
    XTTS_MODEL_NAME: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    CHATTERBOX_MODEL: str = "resemble-ai/chatterbox"
    VOICE_ENGINE: str = "chatterbox"  # "chatterbox" | "xtts" | "auto"

    # AI Models — Face/Video
    FACE_ENGINE: str = "liveportrait"  # "liveportrait" | "basic"
    LIPSYNC_ENGINE: str = "musetalk"   # "musetalk" | "latentsync" | "basic"
    ENHANCE_ENGINE: str = "gfpgan"     # "gfpgan" | "realesrgan" | "basic"

    # Inference
    DEVICE: str = "cuda"
    CUDA_VISIBLE_DEVICES: str = "0"
    GPU_MEMORY_FRACTION: float = 0.9

    # Post-Processing (Section 5 — secret layer)
    ENABLE_MICROJITTER: bool = True
    ENABLE_FILM_GRAIN: bool = True
    ENABLE_LENS_DISTORTION: bool = True
    ENABLE_DOF: bool = True
    ENABLE_COLOR_GRADE: bool = True
    ENABLE_AUDIO_POST: bool = True
    GRAIN_INTENSITY: float = 0.08
    JITTER_MAX_PX: float = 2.0

    # Quality gates
    SYNCNET_MIN_SCORE: float = 7.0
    FACE_SIMILARITY_MIN: float = 0.6
    AI_DETECT_MAX_PCT: float = 30.0

    # Limits
    RATE_LIMIT_PER_MINUTE: int = 10
    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_VIDEO_DURATION_SECONDS: int = 300
    FREE_MONTHLY_LIMIT: int = 5
    PRO_MONTHLY_LIMIT: int = 9999

    # File retention (hours)
    FACE_RETENTION_HOURS: int = 24
    VIDEO_RETENTION_DAYS: int = 30

    # Ollama (local LLM for script AI)
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"


settings = Settings()
