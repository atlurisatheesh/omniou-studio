"""
AGRISENSE — Database Models (SQLAlchemy 2.0)
=============================================
Agricultural intelligence platform database schema.
Covers users, crop scans, soil tests, crop calendars, market data, community.
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


# ── UUID type compatible with SQLite ──

class GUID(TypeDecorator):
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
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)
    language = Column(String(10), default="en")  # en, hi, te, ta, kn, mr, bn, pa
    region = Column(String(100), nullable=True)   # State/District
    is_active = Column(Boolean, default=True)
    plan = Column(String(20), default="free")     # free, pro, enterprise

    # Farm details
    farm_size_acres = Column(Float, nullable=True)
    primary_crops = Column(Text, nullable=True)  # JSON array of crop names
    soil_type = Column(String(50), nullable=True)  # clay, sandy, loam, silt, etc.
    irrigation_type = Column(String(50), nullable=True)  # rainfed, borewell, canal, drip

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    crop_scans = relationship("CropScan", back_populates="user", cascade="all, delete-orphan")
    soil_tests = relationship("SoilTest", back_populates="user", cascade="all, delete-orphan")
    crop_calendars = relationship("CropCalendar", back_populates="user", cascade="all, delete-orphan")
    community_posts = relationship("CommunityPost", back_populates="user", cascade="all, delete-orphan")


# ── Crop Scan (Disease Detection) ─────────────────────────

class CropScan(Base):
    __tablename__ = "crop_scans"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    # Input
    image_path = Column(Text, nullable=False)
    crop_type = Column(String(50), nullable=True)  # rice, wheat, tomato, cotton, etc.

    # Detection results
    disease_name = Column(String(255), nullable=True)
    confidence = Column(Float, nullable=True)     # 0-1
    severity = Column(Integer, nullable=True)     # 1-5
    is_healthy = Column(Boolean, default=False)

    # Treatment
    treatment_chemical = Column(Text, nullable=True)
    treatment_organic = Column(Text, nullable=True)
    prevention_tips = Column(Text, nullable=True)

    # Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="crop_scans")


# ── Soil Test ─────────────────────────────────────────────

class SoilTest(Base):
    __tablename__ = "soil_tests"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    # Soil parameters
    ph = Column(Float, nullable=True)
    nitrogen_kg_ha = Column(Float, nullable=True)  # N available kg/ha
    phosphorus_kg_ha = Column(Float, nullable=True)  # P available kg/ha
    potassium_kg_ha = Column(Float, nullable=True)  # K available kg/ha
    organic_carbon_pct = Column(Float, nullable=True)  # OC %
    ec_ds_m = Column(Float, nullable=True)  # Electrical conductivity dS/m
    zinc_ppm = Column(Float, nullable=True)
    iron_ppm = Column(Float, nullable=True)
    manganese_ppm = Column(Float, nullable=True)
    boron_ppm = Column(Float, nullable=True)
    sulphur_ppm = Column(Float, nullable=True)
    soil_type = Column(String(50), nullable=True)

    # Recommendations (stored as JSON text)
    fertilizer_recommendation = Column(Text, nullable=True)
    deficiency_alerts = Column(Text, nullable=True)
    overall_health_score = Column(Float, nullable=True)  # 0-100

    # Target crop
    target_crop = Column(String(50), nullable=True)
    field_name = Column(String(100), nullable=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="soil_tests")


# ── Crop Calendar ─────────────────────────────────────────

class CropCalendar(Base):
    __tablename__ = "crop_calendars"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    crop = Column(String(50), nullable=False)
    variety = Column(String(100), nullable=True)
    sowing_date = Column(DateTime, nullable=False)
    expected_harvest_date = Column(DateTime, nullable=True)
    field_name = Column(String(100), nullable=True)
    field_size_acres = Column(Float, nullable=True)
    region = Column(String(100), nullable=True)

    # Status
    status = Column(String(20), default="active")  # active, harvested, failed
    current_stage = Column(String(50), nullable=True)  # germination, vegetative, flowering, etc.

    # Activities log (JSON text)
    activities_json = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="crop_calendars")


# ── Community Post ────────────────────────────────────────

class CommunityPost(Base):
    __tablename__ = "community_posts"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    image_path = Column(Text, nullable=True)
    category = Column(String(50), default="general")  # disease, pest, soil, market, general
    crop = Column(String(50), nullable=True)
    region = Column(String(100), nullable=True)

    # Engagement
    upvotes = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)
    is_answered = Column(Boolean, default=False)
    is_expert_reply = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="community_posts")
    replies = relationship("CommunityReply", back_populates="post", cascade="all, delete-orphan")


class CommunityReply(Base):
    __tablename__ = "community_replies"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    post_id = Column(GUID, ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    body = Column(Text, nullable=False)
    image_path = Column(Text, nullable=True)
    is_expert = Column(Boolean, default=False)
    upvotes = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("CommunityPost", back_populates="replies")


# ── Market Price (cached) ─────────────────────────────────

class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    commodity = Column(String(100), nullable=False, index=True)
    market_name = Column(String(200), nullable=False)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)

    min_price = Column(Float, nullable=True)  # Rs per quintal
    max_price = Column(Float, nullable=True)
    modal_price = Column(Float, nullable=True)

    arrival_date = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)


# ── Pest Alert ────────────────────────────────────────────

class PestAlert(Base):
    __tablename__ = "pest_alerts"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    crop = Column(String(50), nullable=False)
    pest_name = Column(String(200), nullable=False)
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    region = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    description = Column(Text, nullable=True)
    prevention = Column(Text, nullable=True)
    treatment = Column(Text, nullable=True)

    # Weather conditions that triggered alert
    temp_c = Column(Float, nullable=True)
    humidity_pct = Column(Float, nullable=True)

    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


# ── Database Engine ───────────────────────────────────────

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """FastAPI dependency for getting a DB session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
