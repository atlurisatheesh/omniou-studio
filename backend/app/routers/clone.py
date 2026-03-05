"""
CLONEAI ULTRA — Clone Generation Router
========================================
Core endpoints for creating AI clone videos.
All jobs persisted to database (Section 8).
Protected endpoints require JWT authentication.
"""

import uuid
from datetime import datetime
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import CloneJob, User, get_db
from ..models.schemas import (
    CloneCreateRequest,
    CloneCreateResponse,
    CloneStatusResponse,
    JobStatus,
)
from ..tasks.generation import generate_clone_video
from ..utils.security import require_user, get_current_user_optional

router = APIRouter()
logger = structlog.get_logger()


@router.post("/clone/create", response_model=CloneCreateResponse)
async def create_clone(
    request: CloneCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    """
    Create a new clone video generation job.
    Requires authentication.

    Persists to database, dispatches Celery task, returns job ID
    for WebSocket progress tracking.
    """
    job_id = str(uuid.uuid4())

    logger.info(
        "clone.create",
        job_id=job_id,
        language=request.target_language,
        emotion=request.emotion,
        script_length=len(request.script_text),
    )

    # Persist job to database (owned by authenticated user)
    job = CloneJob(
        id=uuid.UUID(job_id),
        user_id=user.id,
        face_path=request.photo_path,
        script=request.script_text,
        language=request.target_language,
        emotion=request.emotion,
        background=request.background,
        status="queued",
        stage="queued",
        progress=0,
    )
    if request.voice_id:
        job.voice_id = uuid.UUID(request.voice_id)

    db.add(job)
    await db.commit()

    # Dispatch Celery task
    try:
        task = generate_clone_video.delay(
            job_id=job_id,
            photo_path=request.photo_path,
            voice_path=request.voice_path,
            script_text=request.script_text,
            target_language=request.target_language,
            emotion=request.emotion,
            background=request.background,
        )
        job.celery_task_id = task.id
        await db.commit()
    except Exception as e:
        logger.error("clone.create.failed", job_id=job_id, error=str(e))
        job.status = "failed"
        job.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to queue job: {str(e)}")

    return CloneCreateResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        message="Job queued successfully. Connect to WebSocket for real-time progress.",
    )


@router.get("/clone/{job_id}/status", response_model=CloneStatusResponse)
async def get_clone_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get the current status of a clone generation job."""
    result = await db.execute(
        select(CloneJob).where(CloneJob.id == uuid.UUID(job_id))
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return CloneStatusResponse(
        job_id=str(job.id),
        status=job.status,
        progress=job.progress or 0,
        step=job.stage or "unknown",
        eta_seconds=None,
        result_url=f"/api/v1/video/{job.id}/download" if job.status == "completed" else None,
        error=job.error_message,
        quality_score=job.quality_score,
        ai_detect_pct=job.ai_detect_pct,
    )


@router.get("/clone/history")
async def get_clone_history(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Get clone jobs (paginated, most recent first). Filters by user if authenticated."""
    query = select(CloneJob).order_by(desc(CloneJob.created_at)).limit(limit).offset(offset)
    if user:
        query = query.where(CloneJob.user_id == user.id)
    result = await db.execute(query)
    jobs = result.scalars().all()

    return {
        "jobs": [
            {
                "job_id": str(j.id),
                "status": j.status,
                "progress": j.progress or 0,
                "step": j.stage,
                "emotion": j.emotion,
                "background": j.background,
                "quality_score": j.quality_score,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                "processing_time_sec": j.processing_time_sec,
                "result_url": f"/api/v1/video/{j.id}/download" if j.status == "completed" else None,
            }
            for j in jobs
        ],
        "total": len(jobs),
    }


@router.delete("/clone/{job_id}")
async def cancel_clone(job_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(require_user)):
    """Cancel a running clone job."""
    result = await db.execute(
        select(CloneJob).where(CloneJob.id == uuid.UUID(job_id))
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in ("completed", "failed"):
        raise HTTPException(status_code=400, detail="Job already finished")

    # Revoke Celery task
    if job.celery_task_id:
        try:
            from ..tasks.generation import celery_app
            celery_app.control.revoke(job.celery_task_id, terminate=True)
        except Exception:
            pass

    job.status = "cancelled"
    job.stage = "cancelled"
    await db.commit()

    logger.info("clone.cancelled", job_id=job_id)
    return {"status": "cancelled", "job_id": job_id}


# ── WebSocket for real-time progress ──

@router.websocket("/clone/{job_id}/ws")
async def clone_progress_ws(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time clone generation progress.

    Sends JSON messages:
    {"progress": 0-100, "step": "voice_cloning", "status": "processing"}
    """
    await websocket.accept()
    logger.info("ws.connected", job_id=job_id)

    try:
        import asyncio
        import json
        import redis.asyncio as aioredis

        from ..config import settings

        r = aioredis.from_url(settings.REDIS_URL)
        pubsub = r.pubsub()
        await pubsub.subscribe(f"job:{job_id}:progress")

        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["data"]:
                data = json.loads(message["data"])
                await websocket.send_json(data)

                if data.get("status") in ("completed", "failed", "cancelled"):
                    break

            await asyncio.sleep(0.5)

        await pubsub.unsubscribe(f"job:{job_id}:progress")
        await r.close()

    except WebSocketDisconnect:
        logger.info("ws.disconnected", job_id=job_id)
    except Exception as e:
        logger.error("ws.error", job_id=job_id, error=str(e))
        await websocket.close(code=1011)
