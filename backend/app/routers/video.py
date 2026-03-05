"""
CLONEAI ULTRA — Video Router
==============================
Endpoints for video download, preview, metadata, and format export.
Protected: download and export require authentication.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..models.database import User
from ..utils.security import require_user, get_current_user_optional

router = APIRouter()
logger = structlog.get_logger()

OUTPUT_DIR = Path("outputs")


class ExportRequest(BaseModel):
    format: str = "youtube"  # youtube | instagram | linkedin | tiktok | square


EXPORT_PRESETS = {
    "youtube":   {"w": 1920, "h": 1080, "label": "16:9"},
    "instagram": {"w": 1080, "h": 1920, "label": "9:16"},
    "tiktok":    {"w": 1080, "h": 1920, "label": "9:16"},
    "linkedin":  {"w": 1080, "h": 1080, "label": "1:1"},
    "square":    {"w": 1080, "h": 1080, "label": "1:1"},
}


@router.get("/video/{job_id}/download")
async def download_video(job_id: str, user: User = Depends(require_user)):
    """Download the generated video for a given job. Requires authentication."""
    video_path = OUTPUT_DIR / f"{job_id}" / "final_output.mp4"

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found. Job may still be processing.")

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"cloneai_{job_id}.mp4",
    )


@router.get("/video/{job_id}/preview")
async def preview_video(job_id: str):
    """Get preview/thumbnail for a generated video."""
    thumb_path = OUTPUT_DIR / f"{job_id}" / "thumbnail.jpg"

    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Preview not available yet.")

    return FileResponse(path=str(thumb_path), media_type="image/jpeg")


@router.get("/video/{job_id}/metadata")
async def video_metadata(job_id: str):
    """Get metadata for a generated video."""
    video_path = OUTPUT_DIR / f"{job_id}" / "final_output.mp4"

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found.")

    size_bytes = os.path.getsize(video_path)

    return {
        "job_id": job_id,
        "file_size_bytes": size_bytes,
        "file_size_mb": round(size_bytes / (1024 * 1024), 2),
        "format": "mp4",
        "codec": "h264",
        "download_url": f"/api/v1/video/{job_id}/download",
    }


@router.post("/video/{job_id}/export")
async def export_video(job_id: str, req: ExportRequest, user: User = Depends(require_user)):
    """
    Re-encode video to a specific platform format (aspect ratio / resolution).
    
    Supported: youtube (16:9), instagram (9:16), linkedin (1:1), tiktok (9:16), square (1:1)
    """
    source_path = OUTPUT_DIR / f"{job_id}" / "final_output.mp4"
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="Source video not found.")

    preset = EXPORT_PRESETS.get(req.format)
    if not preset:
        raise HTTPException(status_code=400, detail=f"Unknown format: {req.format}. Use: {list(EXPORT_PRESETS.keys())}")

    out_name = f"export_{req.format}.mp4"
    out_path = OUTPUT_DIR / f"{job_id}" / out_name

    # If already exported, return immediately
    if out_path.exists():
        return {
            "job_id": job_id,
            "format": req.format,
            "resolution": f"{preset['w']}x{preset['h']}",
            "download_url": f"/api/v1/video/{job_id}/export/{req.format}/download",
        }

    # FFmpeg: scale + pad to target resolution (letterbox / pillarbox as needed)
    w, h = preset["w"], preset["h"]
    vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(source_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(out_path),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="FFmpeg not found on this server.")
    except subprocess.CalledProcessError as e:
        logger.error("video.export_failed", job_id=job_id, format=req.format, error=e.stderr.decode()[:500])
        raise HTTPException(status_code=500, detail="Export encoding failed.")

    logger.info("video.exported", job_id=job_id, format=req.format, resolution=f"{w}x{h}")

    return {
        "job_id": job_id,
        "format": req.format,
        "resolution": f"{w}x{h}",
        "download_url": f"/api/v1/video/{job_id}/export/{req.format}/download",
    }


@router.get("/video/{job_id}/export/{fmt}/download")
async def download_export(job_id: str, fmt: str):
    """Download an exported format."""
    out_path = OUTPUT_DIR / f"{job_id}" / f"export_{fmt}.mp4"
    if not out_path.exists():
        raise HTTPException(status_code=404, detail=f"Export in '{fmt}' format not found. Call POST /export first.")

    return FileResponse(
        path=str(out_path),
        media_type="video/mp4",
        filename=f"cloneai_{job_id}_{fmt}.mp4",
    )
