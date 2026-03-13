"""
AGRISENSE — Disease Detection Router
"""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import get_db
from ..services.disease_detection import detect_disease, get_scan_history, get_supported_crops

router = APIRouter(prefix="/disease", tags=["Disease Detection"])

UPLOAD_DIR = Path("uploads/scans")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/scan")
async def scan_crop(
    image: UploadFile = File(...),
    crop_type: str = Form(default="rice"),
    latitude: float = Form(default=None),
    longitude: float = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Upload a crop image for disease detection."""
    # Validate file type
    if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, or WebP images accepted")

    # Save uploaded image
    ext = image.filename.split(".")[-1] if image.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = UPLOAD_DIR / filename

    content = await image.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="Image must be under 10MB")

    with open(filepath, "wb") as f:
        f.write(content)

    result = await detect_disease(
        image_path=str(filepath),
        crop_type=crop_type,
        db=db,
        lat=latitude,
        lon=longitude,
    )

    return result


@router.get("/history")
async def get_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Get scan history."""
    # In production: extract user_id from JWT
    scans = await get_scan_history(db, user_id=None, limit=limit)
    return {"scans": scans}


@router.get("/crops")
async def list_supported_crops():
    """Get list of supported crops for disease detection."""
    return {"crops": get_supported_crops()}
