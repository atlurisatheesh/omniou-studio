"""
CLONEAI ULTRA — Voice Router
==============================
Endpoints for voice operations + voice profile CRUD (Section 8).
"""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import VoiceProfile, get_db
from ..models.schemas import (
    VoiceCloneRequest,
    VoiceCloneResponse,
    VoiceProfileCreate,
    VoiceProfileResponse,
)

router = APIRouter()
logger = structlog.get_logger()

# Supported languages for XTTS v2 + Chatterbox
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "pl": "Polish",
    "tr": "Turkish",
    "ru": "Russian",
    "nl": "Dutch",
    "cs": "Czech",
    "ar": "Arabic",
    "zh": "Chinese",
    "ja": "Japanese",
    "hu": "Hungarian",
    "ko": "Korean",
    "hi": "Hindi",
}


@router.get("/voice/languages")
async def get_supported_languages():
    """Get all supported TTS languages."""
    return {
        "languages": [
            {"code": code, "name": name}
            for code, name in sorted(SUPPORTED_LANGUAGES.items(), key=lambda x: x[1])
        ],
        "total": len(SUPPORTED_LANGUAGES),
    }


@router.post("/voice/clone", response_model=VoiceCloneResponse)
async def clone_voice_only(request: VoiceCloneRequest):
    """
    Clone a voice and generate speech from text (voice only, no video).
    Returns a WAV file URL.
    """
    if request.target_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language: {request.target_language}. Supported: {list(SUPPORTED_LANGUAGES.keys())}",
        )

    logger.info(
        "voice.clone",
        language=request.target_language,
        text_length=len(request.script_text),
    )

    from ..services.voice_clone import VoiceCloneService

    try:
        service = VoiceCloneService()
        output_path = await service.clone_voice(
            voice_sample_path=request.voice_path,
            text=request.script_text,
            language=request.target_language,
        )
        return VoiceCloneResponse(
            status="success",
            audio_url=f"/outputs/{output_path.name}",
            duration_seconds=0,
        )
    except Exception as e:
        logger.error("voice.clone.failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice/preview")
async def preview_voice(voice_path: str, text: str = "Hello, this is a preview of my cloned voice."):
    """Quick preview of voice clone with short text."""
    from ..services.voice_clone import VoiceCloneService

    try:
        service = VoiceCloneService()
        output_path = await service.clone_voice(
            voice_sample_path=voice_path,
            text=text,
            language="en",
        )
        return {"status": "success", "audio_url": f"/outputs/{output_path.name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Voice Profile CRUD ──

@router.post("/voice/profiles", response_model=VoiceProfileResponse)
async def create_voice_profile(
    body: VoiceProfileCreate,
    db: AsyncSession = Depends(get_db),
):
    """Save a voice profile for re-use across multiple clone jobs."""
    profile = VoiceProfile(
        id=uuid.uuid4(),
        name=body.name,
        audio_path=body.audio_path,
        language=body.language,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    logger.info("voice.profile.created", profile_id=str(profile.id), name=body.name)
    return VoiceProfileResponse(
        id=str(profile.id),
        name=profile.name,
        language=profile.language,
        duration_sec=profile.duration_sec,
        quality_score=profile.quality_score,
        created_at=profile.created_at,
    )


@router.get("/voice/profiles")
async def list_voice_profiles(db: AsyncSession = Depends(get_db)):
    """List all saved voice profiles."""
    result = await db.execute(select(VoiceProfile).order_by(VoiceProfile.created_at.desc()))
    profiles = result.scalars().all()
    return {
        "profiles": [
            {
                "id": str(p.id),
                "name": p.name,
                "language": p.language,
                "duration_sec": p.duration_sec,
                "quality_score": p.quality_score,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in profiles
        ],
        "total": len(profiles),
    }


@router.get("/voice/profiles/{profile_id}", response_model=VoiceProfileResponse)
async def get_voice_profile(profile_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific voice profile."""
    result = await db.execute(
        select(VoiceProfile).where(VoiceProfile.id == uuid.UUID(profile_id))
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    return VoiceProfileResponse(
        id=str(profile.id),
        name=profile.name,
        language=profile.language,
        duration_sec=profile.duration_sec,
        quality_score=profile.quality_score,
        created_at=profile.created_at,
    )


@router.delete("/voice/profiles/{profile_id}")
async def delete_voice_profile(profile_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a saved voice profile."""
    result = await db.execute(
        select(VoiceProfile).where(VoiceProfile.id == uuid.UUID(profile_id))
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")

    await db.delete(profile)
    await db.commit()
    logger.info("voice.profile.deleted", profile_id=profile_id)
    return {"status": "deleted", "id": profile_id}
