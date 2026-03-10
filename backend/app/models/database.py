"""
CLONEAI ULTRA — Database Models (SQLAlchemy 2.0)
=================================================
PostgreSQL database models matching Section 7 schema specification.
Covers users, voice profiles, clone jobs, and admin stats.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    TypeDecorator,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.types import CHAR

from ..config import settings


# ── UUID type that works with both PostgreSQL and SQLite ──

class GUID(TypeDecorator):
    """Platform-independent UUID type.
    Uses PostgreSQL's UUID on postgres, stores as CHAR(36) on SQLite."""
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value) if not isinstance(value, uuid.UUID) else value
        return value


class Base(DeclarativeBase):
    pass


# ── User ──────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    provider = Column(String(50), default="email")  # google, email, credentials
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    # Plan / billing  (free | creator | pro | enterprise)
    plan = Column(String(20), default="free")
    videos_used = Column(Integer, default=0)
    videos_limit = Column(Integer, default=5)  # free=5, creator=50, pro=unlimited

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    jobs = relationship("CloneJob", back_populates="user", cascade="all, delete-orphan")
    voice_profiles = relationship("VoiceProfile", back_populates="user", cascade="all, delete-orphan")


# ── Voice Profile ─────────────────────────────────────────

class VoiceProfile(Base):
    __tablename__ = "voice_profiles"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(255), default="My Voice")
    audio_path = Column(Text, nullable=False)           # MinIO/local path to voice sample
    embedding_path = Column(Text, nullable=True)         # Cached speaker embedding
    language = Column(String(10), default="en")
    duration_sec = Column(Float, nullable=True)           # Sample duration
    quality_score = Column(Float, nullable=True)          # Clone quality 0-1

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    user = relationship("User", back_populates="voice_profiles")


# ── Clone Job ─────────────────────────────────────────────

class CloneJob(Base):
    __tablename__ = "clone_jobs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=True)

    # Input
    voice_id = Column(GUID, ForeignKey("voice_profiles.id"), nullable=True)
    face_path = Column(Text, nullable=False)              # Photo or video input
    script = Column(Text, nullable=False)
    language = Column(String(10), default="en")
    emotion = Column(String(20), default="neutral")       # neutral, happy, serious, excited
    background = Column(String(50), default="blur")       # blur, office, studio, custom

    # Status tracking
    status = Column(String(20), default="queued")         # queued, processing, completed, failed, cancelled
    stage = Column(String(50), nullable=True)             # current pipeline stage
    progress = Column(Integer, default=0)                 # 0-100
    error_message = Column(Text, nullable=True)

    # Output
    output_path = Column(Text, nullable=True)             # Final video MinIO/local path
    output_audio_path = Column(Text, nullable=True)
    thumbnail_path = Column(Text, nullable=True)

    # Quality metrics
    quality_score = Column(Float, nullable=True)          # Final quality score
    ai_detect_pct = Column(Float, nullable=True)          # AI detection % (lower=better)
    sync_score = Column(Float, nullable=True)             # SyncNet lip sync score

    # Metadata
    duration_sec = Column(Float, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    processing_time_sec = Column(Float, nullable=True)

    # Celery integration
    celery_task_id = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relations
    user = relationship("User", back_populates="jobs")


# ── Analytics Event ───────────────────────────────────────

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    job_id = Column(String(36), nullable=True)
    metadata_json = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ── Video Template ────────────────────────────────────────

class VideoTemplate(Base):
    __tablename__ = "video_templates"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    default_emotion = Column(String(20), default="neutral")
    default_background = Column(String(50), default="blur")
    default_language = Column(String(10), default="en")
    script_template = Column(Text, nullable=True)
    thumbnail_emoji = Column(String(10), nullable=True)
    user_id = Column(String(36), nullable=True, index=True)  # NULL = built-in
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Database Engine ───────────────────────────────────────

# Build engine — falls back to SQLite for development without Postgres
_db_url = settings.DATABASE_URL
_is_sqlite = "sqlite" in _db_url

if settings.APP_ENV == "development" and not _is_sqlite:
    engine = create_async_engine(_db_url, echo=settings.APP_DEBUG)
elif _is_sqlite:
    engine = create_async_engine(_db_url, echo=settings.APP_DEBUG, connect_args={"check_same_thread": False})
else:
    engine = create_async_engine(_db_url, echo=False, pool_size=20, max_overflow=10)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

_SQLITE_FALLBACK = "sqlite+aiosqlite:///./cloneai_dev.db"


async def init_db():
    """Create all tables (for dev — use Alembic in production)."""
    global engine, async_session
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        if settings.APP_ENV == "development":
            import structlog
            log = structlog.get_logger("cloneai.db")
            log.warning("PostgreSQL unavailable, falling back to SQLite", error=str(exc))
            engine = create_async_engine(_SQLITE_FALLBACK, echo=settings.APP_DEBUG, connect_args={"check_same_thread": False})
            async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        else:
            raise


async def get_db():
    """FastAPI dependency for getting a DB session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
