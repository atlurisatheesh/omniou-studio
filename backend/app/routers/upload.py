"""
CLONEAI PRO — File Upload Router
=================================
Secure file upload with validation for photos, audio, and video files.
"""

import uuid
from pathlib import Path
from typing import Literal

import aiofiles
import structlog
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from ..config import settings

router = APIRouter()
logger = structlog.get_logger()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed MIME types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3", "audio/mp4", "audio/m4a", "audio/ogg", "audio/flac"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}

MAX_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def _validate_file(file: UploadFile, allowed_types: set[str], label: str) -> None:
    """Validate file type and size."""
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Invalid {label} file type: {file.content_type}. Allowed: {', '.join(allowed_types)}",
        )
    if file.size and file.size > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )


async def _save_upload(file: UploadFile, subfolder: str) -> dict:
    """Save uploaded file to disk and return metadata."""
    file_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix if file.filename else ".bin"
    save_dir = UPLOAD_DIR / subfolder
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / f"{file_id}{ext}"

    async with aiofiles.open(save_path, "wb") as f:
        content = await file.read()
        if len(content) > MAX_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="File too large")
        await f.write(content)

    logger.info("upload.saved", file_id=file_id, path=str(save_path), size=len(content))

    return {
        "file_id": file_id,
        "filename": file.filename,
        "path": str(save_path),
        "size_bytes": len(content),
        "content_type": file.content_type,
    }


@router.post("/upload/photo")
async def upload_photo(file: UploadFile = File(...)):
    """Upload a face photo for avatar generation."""
    _validate_file(file, ALLOWED_IMAGE_TYPES, "image")
    result = await _save_upload(file, "photos")
    return {"status": "success", "type": "photo", **result}


@router.post("/upload/voice")
async def upload_voice(file: UploadFile = File(...)):
    """Upload a voice sample for voice cloning (min 30 seconds)."""
    _validate_file(file, ALLOWED_AUDIO_TYPES, "audio")
    result = await _save_upload(file, "voices")
    return {"status": "success", "type": "voice", **result}


@router.post("/upload/video")
async def upload_video(file: UploadFile = File(...)):
    """Upload a reference video (optional)."""
    _validate_file(file, ALLOWED_VIDEO_TYPES, "video")
    result = await _save_upload(file, "videos")
    return {"status": "success", "type": "video", **result}
