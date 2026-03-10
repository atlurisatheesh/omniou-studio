"""
routers/multi_face.py — Multi-person video generation endpoints (Phase 12).

POST /multi-face/create   → create a group video job
GET  /multi-face/{id}     → status of a multi-face job
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.utils.security import get_current_user_optional

router = APIRouter(prefix="/multi-face", tags=["multi-face"])


# ── Schemas ──
class PersonInput(BaseModel):
    face_path: str
    voice_path: str
    script: str
    name: str = ""
    language: str = "en"
    emotion: str = "neutral"


class MultiJobCreate(BaseModel):
    persons: List[PersonInput] = Field(..., min_length=2, max_length=6)
    layout: str = "sequential"
    background_path: Optional[str] = None
    output_name: Optional[str] = None


class MultiJobResponse(BaseModel):
    job_id: str
    status: str
    person_count: int
    layout: str
    created_at: str


class MultiJobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    stage: str
    error: Optional[str]
    output_path: Optional[str]
    person_results: List[dict]


# In-memory job store
_multi_jobs: dict = {}


async def _run_multi_face_job(job_id: str, body: MultiJobCreate):
    from app.services.multi_face_pipeline import MultiFacePipeline, PersonSpec
    import tempfile

    job = _multi_jobs[job_id]
    job["status"] = "processing"
    job["progress"] = 0

    def update_progress(pct: float, stage: str):
        job["progress"] = pct
        job["stage"] = stage

    try:
        specs = [
            PersonSpec(
                face_path=p.face_path, voice_path=p.voice_path,
                script=p.script, name=p.name,
                language=p.language, emotion=p.emotion,
            )
            for p in body.persons
        ]

        with tempfile.TemporaryDirectory() as tmp:
            pipeline = MultiFacePipeline(temp_dir=tmp)
            out_name = body.output_name or f"multi_{job_id[:8]}.mp4"
            out_path = f"outputs/{out_name}"
            result = await pipeline.generate(
                persons=specs, output_path=out_path,
                layout=body.layout, background_path=body.background_path,
                progress_callback=update_progress,
            )

        job["status"] = "completed" if not result.error else "failed"
        job["output_path"] = result.final_video_path
        job["error"] = result.error
        job["progress"] = 100
        job["stage"] = "complete"
        job["person_results"] = [
            {
                "index": pr.index, "name": pr.spec.name,
                "duration_sec": pr.duration_sec,
                "error": pr.error, "has_video": bool(pr.video_path),
            }
            for pr in result.persons
        ]
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        job["stage"] = "failed"


# ── Endpoints ──
@router.post("/create", response_model=MultiJobResponse, status_code=202)
async def create_multi_face_job(
    body: MultiJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    if body.layout not in ("sequential", "grid", "spotlight"):
        raise HTTPException(status_code=422, detail="layout must be sequential, grid, or spotlight")

    job_id = str(uuid.uuid4())
    now_str = datetime.now(timezone.utc).isoformat()

    _multi_jobs[job_id] = {
        "job_id": job_id, "status": "queued", "progress": 0.0,
        "stage": "queued", "error": None, "output_path": None,
        "person_count": len(body.persons), "layout": body.layout,
        "person_results": [], "created_at": now_str,
    }

    background_tasks.add_task(_run_multi_face_job, job_id, body)

    return MultiJobResponse(
        job_id=job_id, status="queued",
        person_count=len(body.persons), layout=body.layout, created_at=now_str,
    )


@router.get("/{job_id}", response_model=MultiJobStatus)
async def get_multi_face_status(job_id: str):
    job = _multi_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Multi-face job not found")
    return MultiJobStatus(**{k: job[k] for k in MultiJobStatus.model_fields})
