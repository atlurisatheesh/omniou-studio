"""
CLONEAI ULTRA — Admin Router
==============================
Admin dashboard statistics and job management (Section 8).
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import CloneJob, User, VoiceProfile, get_db
from ..models.schemas import AdminStatsResponse

router = APIRouter()
logger = structlog.get_logger()


@router.get("/admin/stats", response_model=AdminStatsResponse)
async def admin_stats(db: AsyncSession = Depends(get_db)):
    """Get system-wide statistics for admin dashboard."""
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_jobs = (await db.execute(select(func.count(CloneJob.id)))).scalar() or 0
    completed = (await db.execute(
        select(func.count(CloneJob.id)).where(CloneJob.status == "completed")
    )).scalar() or 0
    failed = (await db.execute(
        select(func.count(CloneJob.id)).where(CloneJob.status == "failed")
    )).scalar() or 0
    active = (await db.execute(
        select(func.count(CloneJob.id)).where(CloneJob.status.in_(["queued", "processing"]))
    )).scalar() or 0

    # GPU info
    gpu_info = None
    try:
        import torch
        if torch.cuda.is_available():
            gpu_info = {
                "name": torch.cuda.get_device_name(0),
                "memory_total_gb": round(torch.cuda.get_device_properties(0).total_mem / (1024**3), 1),
                "memory_used_gb": round(torch.cuda.memory_allocated(0) / (1024**3), 2),
            }
    except Exception:
        pass

    return AdminStatsResponse(
        total_users=total_users,
        total_jobs=total_jobs,
        completed_jobs=completed,
        failed_jobs=failed,
        active_jobs=active,
        gpu_memory=gpu_info,
    )


@router.get("/admin/jobs")
async def admin_list_jobs(
    status: str = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List all jobs with optional status filter."""
    query = select(CloneJob).order_by(CloneJob.created_at.desc()).limit(limit).offset(offset)
    if status:
        query = query.where(CloneJob.status == status)
    result = await db.execute(query)
    jobs = result.scalars().all()

    return {
        "jobs": [
            {
                "job_id": str(j.id),
                "user_id": str(j.user_id) if j.user_id else None,
                "status": j.status,
                "stage": j.stage,
                "progress": j.progress,
                "emotion": j.emotion,
                "background": j.background,
                "quality_score": j.quality_score,
                "ai_detect_pct": j.ai_detect_pct,
                "sync_score": j.sync_score,
                "processing_time_sec": j.processing_time_sec,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            }
            for j in jobs
        ],
        "total": len(jobs),
    }


@router.get("/admin/users")
async def admin_list_users(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List all users."""
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    )
    users = result.scalars().all()

    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "name": u.name,
                "plan": u.plan,
                "videos_used": u.videos_used,
                "videos_limit": u.videos_limit,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": len(users),
    }
