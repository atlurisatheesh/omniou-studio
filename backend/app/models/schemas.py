"""
CLONEAI ULTRA — Pydantic Schemas
==================================
Request/response models for all API endpoints (Section 8).
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


# ── Enums ──

class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    VOICE_CLONING = "voice_cloning"
    FACE_ANIMATING = "face_animating"
    LIP_SYNCING = "lip_syncing"
    ENHANCING = "enhancing"
    POSTPROCESSING = "postprocessing"
    QUALITY_CHECK = "quality_check"
    ENCODING = "encoding"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Emotion(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SERIOUS = "serious"
    EXCITED = "excited"
    SAD = "sad"


class ExportFormat(str, Enum):
    INSTAGRAM_REEL = "instagram_reel"
    YOUTUBE_SHORT = "youtube_short"
    LINKEDIN = "linkedin"
    STANDARD = "standard"


# ── Clone ──

class CloneCreateRequest(BaseModel):
    """Request to create a new clone video (Section 8: POST /api/clone/create)."""
    photo_path: str = Field(..., description="Path to uploaded face photo/video")
    voice_path: str = Field(..., description="Path to uploaded voice sample (min 6s)")
    script_text: str = Field(..., min_length=1, max_length=5000, description="Text for the clone to speak")
    target_language: str = Field(default="en", description="ISO language code")
    emotion: str = Field(default="neutral", description="Emotion: neutral, happy, serious, excited")
    background: str = Field(default="blur", description="Background: blur, office, studio, custom")
    voice_id: Optional[str] = Field(default=None, description="Re-use a saved voice profile ID")

    model_config = {"json_schema_extra": {
        "example": {
            "photo_path": "uploads/photos/abc123.jpg",
            "voice_path": "uploads/voices/abc123.wav",
            "script_text": "Hello world, this is my AI clone speaking!",
            "target_language": "en",
            "emotion": "neutral",
            "background": "blur",
        }
    }}


class CloneCreateResponse(BaseModel):
    """Response after creating a clone job."""
    job_id: str
    status: JobStatus
    message: str


class CloneStatusResponse(BaseModel):
    """Status of a clone generation job."""
    job_id: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    step: str
    eta_seconds: Optional[int] = None
    result_url: Optional[str] = None
    error: Optional[str] = None
    quality_score: Optional[float] = None
    ai_detect_pct: Optional[float] = None


# ── Voice ──

class VoiceCloneRequest(BaseModel):
    """Request to clone a voice (audio only, no video)."""
    voice_path: str = Field(..., description="Path to voice sample file")
    script_text: str = Field(..., min_length=1, max_length=5000)
    target_language: str = Field(default="en")


class VoiceCloneResponse(BaseModel):
    """Response with cloned voice audio."""
    status: str
    audio_url: str
    duration_seconds: float


class VoiceProfileCreate(BaseModel):
    """Create a saved voice profile."""
    name: str = Field(default="My Voice", max_length=255)
    audio_path: str
    language: str = Field(default="en")


class VoiceProfileResponse(BaseModel):
    """Voice profile response."""
    id: str
    name: str
    language: str
    duration_sec: Optional[float]
    quality_score: Optional[float]
    created_at: datetime


# ── Upload ──

class UploadResponse(BaseModel):
    """Response after file upload."""
    status: str
    type: str
    file_id: str
    filename: Optional[str]
    path: str
    size_bytes: int
    content_type: Optional[str]


# ── User ──

class UserCreate(BaseModel):
    """Create a new user."""
    email: str = Field(..., description="User email")
    name: Optional[str] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    name: Optional[str]
    plan: str = "free"
    videos_used: int = 0
    videos_limit: int = 5
    created_at: datetime


class UserUpdateRequest(BaseModel):
    """Update user profile."""
    name: Optional[str] = None
    avatar_url: Optional[str] = None


# ── Video Export ──

class VideoExportRequest(BaseModel):
    """Export video in a specific format (Instagram, YouTube, LinkedIn)."""
    job_id: str
    format: ExportFormat = ExportFormat.STANDARD


class VideoExportResponse(BaseModel):
    """Exported video response."""
    status: str
    download_url: str
    format: str
    resolution: str


# ── Script AI ──

class ScriptGenerateRequest(BaseModel):
    """Request AI-generated script."""
    topic: str = Field(..., min_length=1, max_length=500)
    style: str = Field(default="professional", description="professional, casual, educational, marketing")
    language: str = Field(default="en")
    max_words: int = Field(default=150, ge=10, le=1000)


class ScriptGenerateResponse(BaseModel):
    """AI-generated script response."""
    script: str
    word_count: int
    estimated_duration_sec: float


# ── Admin ──

class AdminStatsResponse(BaseModel):
    """Admin dashboard stats."""
    total_users: int
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    active_jobs: int
    gpu_memory: Optional[dict] = None


# ── General ──

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    status_code: int = 500


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str
    device: str
    models_loaded: List[str] = []
