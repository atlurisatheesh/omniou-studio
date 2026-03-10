"""
routers/streaming.py — Real-time frame streaming via SSE (Phase 12).

GET /stream/{job_id}/frames   → SSE stream of base64-encoded JPEG frames
GET /stream/{job_id}/status   → current streaming status
"""

from __future__ import annotations

import asyncio
import base64
import json
import time
from typing import AsyncGenerator

import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import get_db, CloneJob

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/stream", tags=["streaming"])

FRAME_POLL_INTERVAL = 0.1
STREAM_TIMEOUT = 300


def _get_redis():
    try:
        import redis as sync_redis
        from app.config import settings
        r = sync_redis.from_url(settings.REDIS_URL, decode_responses=False)
        r.ping()
        return r
    except Exception:
        return None


async def _frame_generator(job_id: str, start_frame: int = 0) -> AsyncGenerator[str, None]:
    r = _get_redis()
    start = time.time()
    frame_idx = start_frame
    last_heartbeat = time.time()

    while time.time() - start < STREAM_TIMEOUT:
        if time.time() - last_heartbeat > 5:
            yield f"event: heartbeat\ndata: {json.dumps({'ts': time.time()})}\n\n"
            last_heartbeat = time.time()

        if r:
            frame_key = f"cloneai:preview:{job_id}:frame:{frame_idx}"
            try:
                frame_bytes = r.get(frame_key)
            except Exception:
                frame_bytes = None

            if frame_bytes:
                b64 = base64.b64encode(frame_bytes).decode()
                meta_raw = r.get(f"cloneai:preview:{job_id}:meta") or b"{}"
                meta = json.loads(meta_raw)
                payload = json.dumps({
                    "frame": b64,
                    "frame_idx": frame_idx,
                    "stage": meta.get("stage", "processing"),
                    "progress": meta.get("progress", 0),
                    "ts": time.time(),
                })
                yield f"data: {payload}\n\n"
                frame_idx += 1
                continue

            status_key = f"cloneai:preview:{job_id}:status"
            status_val = r.get(status_key)
            if status_val and status_val.decode() in ("completed", "failed"):
                yield f"event: done\ndata: {json.dumps({'status': status_val.decode()})}\n\n"
                return

        await asyncio.sleep(FRAME_POLL_INTERVAL)

    yield f"event: timeout\ndata: {json.dumps({'message': 'Stream timeout'})}\n\n"


@router.get("/{job_id}/frames")
async def stream_frames(
    job_id: str,
    since_frame: int = 0,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CloneJob).where(CloneJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return StreamingResponse(
        _frame_generator(job_id, since_frame),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/{job_id}/status")
async def stream_status(job_id: str):
    r = _get_redis()
    if not r:
        return {"available": False, "frame_count": 0}
    try:
        meta_raw = r.get(f"cloneai:preview:{job_id}:meta") or b"{}"
        meta = json.loads(meta_raw)
        status_raw = r.get(f"cloneai:preview:{job_id}:status")
        status_val = status_raw.decode() if status_raw else "pending"
        return {
            "available": True,
            "frame_count": meta.get("frame_count", 0),
            "stage": meta.get("stage", "pending"),
            "progress": meta.get("progress", 0),
            "status": status_val,
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


# ── Publisher (called from pipeline / workers) ──
def publish_preview_frame(job_id: str, frame_bytes: bytes, frame_idx: int, stage: str, progress: float):
    try:
        import redis as sync_redis
        from app.config import settings
        r = sync_redis.from_url(settings.REDIS_URL)
        r.setex(f"cloneai:preview:{job_id}:frame:{frame_idx}", 600, frame_bytes)
        r.setex(f"cloneai:preview:{job_id}:meta", 600, json.dumps({
            "stage": stage, "progress": progress, "frame_count": frame_idx + 1,
        }).encode())
    except Exception as e:
        log.debug("preview_frame_publish_failed", error=str(e))


def mark_stream_complete(job_id: str, status: str = "completed"):
    try:
        import redis as sync_redis
        from app.config import settings
        r = sync_redis.from_url(settings.REDIS_URL)
        r.setex(f"cloneai:preview:{job_id}:status", 600, status.encode())
    except Exception:
        pass
