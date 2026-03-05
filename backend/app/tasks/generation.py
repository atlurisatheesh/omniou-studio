"""
CLONEAI ULTRA — Celery Task Definitions
========================================
Async background tasks for AI pipeline processing.
Updates database on completion/failure.
"""

import json
import time
from pathlib import Path

import structlog
from celery import Celery

from ..config import settings

logger = structlog.get_logger()

# ── Celery App ──
celery_app = Celery(
    "cloneai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # One task at a time (GPU constraint)
    task_soft_time_limit=600,  # 10 min soft limit
    task_time_limit=900,  # 15 min hard limit
)


def _publish_progress(job_id: str, data: dict):
    """Publish progress update to Redis pub/sub."""
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.publish(f"job:{job_id}:progress", json.dumps(data))
        r.close()
    except Exception as e:
        logger.debug("celery.publish_failed", error=str(e))


def _update_job_db(job_id: str, **kwargs):
    """Update clone job in database (sync, for Celery tasks)."""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from ..models.database import CloneJob, Base

        # Build sync database URL from async URL
        db_url = settings.DATABASE_URL
        if "asyncpg" in db_url:
            db_url = db_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
        elif "aiosqlite" in db_url:
            db_url = db_url.replace("sqlite+aiosqlite", "sqlite")

        # Handle dev SQLite fallback
        if settings.APP_ENV == "development" and "postgresql" in db_url:
            try:
                engine = create_engine(db_url)
                engine.connect().close()
            except Exception:
                db_url = "sqlite:///./cloneai_dev.db"
                engine = create_engine(db_url)
        else:
            engine = create_engine(db_url)

        import uuid as _uuid
        with Session(engine) as session:
            job = session.query(CloneJob).filter(CloneJob.id == _uuid.UUID(job_id)).first()
            if job:
                for k, v in kwargs.items():
                    if hasattr(job, k):
                        setattr(job, k, v)
                session.commit()
        engine.dispose()
    except Exception as e:
        logger.debug("celery.db_update_failed", error=str(e))


@celery_app.task(bind=True, name="cloneai.generate_clone_video")
def generate_clone_video(
    self,
    job_id: str,
    photo_path: str,
    voice_path: str,
    script_text: str,
    target_language: str = "en",
    emotion: str = "neutral",
    background: str = "blur",
):
    """
    Celery task: Run the full clone generation pipeline.

    Executes the ULTRA pipeline:
    1. Voice Clone (Chatterbox / XTTS v2)
    2. Face Animation (LivePortrait / basic)
    3. Lip Sync (MuseTalk / LatentSync)
    4. Enhancement (GFPGAN + Real-ESRGAN)
    5. Post-Processing (7-layer cinematic)
    6. Quality Check (SyncNet + InsightFace)
    7. Final Encode (FFmpeg)
    """
    import asyncio

    start_time = time.time()
    logger.info(
        "celery.task_started",
        job_id=job_id,
        task_id=self.request.id,
        language=target_language,
        emotion=emotion,
    )

    _publish_progress(job_id, {
        "status": "processing",
        "progress": 0,
        "step": "initializing",
    })
    _update_job_db(job_id, status="processing", stage="initializing", progress=0)

    try:
        from ..services.pipeline import PipelineOrchestrator

        orchestrator = PipelineOrchestrator(
            device=settings.DEVICE,
            model_cache_dir=settings.MODEL_CACHE_DIR,
            progress_callback=_publish_progress,
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                orchestrator.run(
                    job_id=job_id,
                    photo_path=photo_path,
                    voice_path=voice_path,
                    script_text=script_text,
                    target_language=target_language,
                )
            )
        finally:
            loop.close()

        elapsed = time.time() - start_time

        if result["status"] == "completed":
            _publish_progress(job_id, {
                "status": "completed",
                "progress": 100,
                "step": "completed",
                "download_url": result.get("download_url"),
                "processing_time": round(elapsed, 2),
            })

            from datetime import datetime
            _update_job_db(
                job_id,
                status="completed",
                stage="completed",
                progress=100,
                output_path=result.get("output_video"),
                output_audio_path=result.get("output_audio"),
                processing_time_sec=round(elapsed, 2),
                completed_at=datetime.utcnow(),
                quality_score=result.get("quality_score"),
                ai_detect_pct=result.get("ai_detect_pct"),
                sync_score=result.get("sync_score"),
            )

            logger.info(
                "celery.task_completed",
                job_id=job_id,
                time_seconds=round(elapsed, 2),
            )
        else:
            _publish_progress(job_id, {
                "status": "failed",
                "progress": 0,
                "step": "failed",
                "error": result.get("error", "Unknown error"),
            })
            _update_job_db(
                job_id,
                status="failed",
                stage="failed",
                error_message=result.get("error", "Unknown error"),
                processing_time_sec=round(elapsed, 2),
            )

        return result

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            "celery.task_failed",
            job_id=job_id,
            error=str(e),
            time_seconds=round(elapsed, 2),
        )

        _publish_progress(job_id, {
            "status": "failed",
            "progress": 0,
            "step": "failed",
            "error": str(e),
        })
        _update_job_db(
            job_id,
            status="failed",
            stage="failed",
            error_message=str(e),
            processing_time_sec=round(elapsed, 2),
        )

        raise


@celery_app.task(bind=True, name="cloneai.voice_clone_only")
def voice_clone_only(
    self,
    job_id: str,
    voice_path: str,
    script_text: str,
    target_language: str = "en",
):
    """Celery task: Voice cloning only (no video)."""
    import asyncio

    logger.info("celery.voice_only_started", job_id=job_id)

    from ..services.voice_clone import VoiceCloneService

    service = VoiceCloneService(
        device=settings.DEVICE,
        model_cache_dir=settings.MODEL_CACHE_DIR,
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        output_path = loop.run_until_complete(
            service.clone_voice(
                voice_sample_path=voice_path,
                text=script_text,
                language=target_language,
            )
        )
        return {"status": "completed", "output": str(output_path)}
    except Exception as e:
        logger.error("celery.voice_only_failed", error=str(e))
        return {"status": "failed", "error": str(e)}
    finally:
        loop.close()
