"""
CLONEAI ULTRA — Project Router
=================================
API endpoints for long-form video projects with identity-locked generation.

Endpoints:
  POST   /project/create          → Create a long-form video project
  GET    /project/{id}            → Get project details + scenes + consistency
  PUT    /project/{id}/scenes     → Update scene list
  POST   /project/{id}/generate   → Start identity-locked multi-scene generation
  GET    /project/{id}/progress   → Per-scene progress + consistency scores
  GET    /project/{id}/consistency → Full consistency report
  POST   /project/{id}/regenerate/{idx} → Regenerate a single scene
  DELETE /project/{id}            → Delete project
"""

import json
import uuid
from datetime import datetime
from typing import Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import settings
from ..models.database import ProjectScene, VideoProject, get_db
from ..models.schemas import (
    ProjectCreateRequest,
    ProjectProgressResponse,
    ProjectResponse,
    SceneResponse,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/project", tags=["Project"])


# ── Helpers ──

def _project_to_response(project: VideoProject) -> ProjectResponse:
    """Convert DB model to response."""
    scenes = []
    if project.scenes:
        for s in sorted(project.scenes, key=lambda x: x.scene_index):
            scenes.append(SceneResponse(
                id=str(s.id),
                scene_index=s.scene_index,
                script_text=s.script_text,
                duration_seconds=s.duration_seconds,
                emotion=s.emotion or "neutral",
                background=s.background or "original",
                transition_type=s.transition_type or "crossfade",
                status=s.status or "pending",
                identity_score=s.identity_score,
                color_consistency_score=s.color_consistency_score,
                cross_scene_score=s.cross_scene_score,
                drift_frame_count=s.drift_frame_count or 0,
            ))

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        status=project.status or "draft",
        total_scenes=project.total_scenes or 0,
        completed_scenes=project.completed_scenes or 0,
        target_duration_minutes=project.target_duration_minutes or 0,
        overall_identity_score=project.overall_identity_score,
        overall_color_score=project.overall_color_score,
        output_path=project.output_path,
        processing_time_seconds=project.processing_time_seconds,
        scenes=scenes,
        created_at=project.created_at or datetime.utcnow(),
        updated_at=project.updated_at,
    )


# ── Create Project ──

@router.post("/create")
async def create_project(
    request: ProjectCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new long-form video project.
    
    This will:
      1. Create the project record
      2. Create an identity anchor from the avatar photo + voice
      3. Analyze the script and split into scenes
      4. Save scene records to the database
    """
    project_id = uuid.uuid4()

    # Build settings JSON
    proj_settings = {}
    if request.settings:
        proj_settings = request.settings.model_dump()
    if request.consistency_settings:
        proj_settings["consistency"] = request.consistency_settings.model_dump()

    # Create project record
    project = VideoProject(
        id=project_id,
        name=request.name,
        full_script=request.script_text,
        target_duration_minutes=request.target_duration_minutes,
        avatar_photo_path=request.avatar_config.photo_path,
        avatar_voice_path=request.avatar_config.voice_path,
        status="analyzing",
        settings_json=json.dumps(proj_settings),
    )

    db.add(project)
    await db.flush()

    # Analyze script and create scenes
    try:
        from ..services.identity_anchor import IdentityAnchorService
        from ..services.director_agent import DirectorAgent

        # Create identity anchor
        anchor_service = IdentityAnchorService()
        anchor = await anchor_service.create_anchor(
            photo_path=request.avatar_config.photo_path,
            voice_path=request.avatar_config.voice_path,
        )

        # Save anchor
        anchor_path = await anchor_service.save_anchor(anchor, str(project_id))
        project.identity_anchor_id = anchor.anchor_id
        project.identity_anchor_path = anchor_path

        # Analyze script into scenes
        director = DirectorAgent(identity_anchor=anchor)
        scene_split_method = proj_settings.get("scene_split_method", "sentence_group")
        default_emotion = proj_settings.get("default_emotion", "neutral")
        default_background = proj_settings.get("background", "original")
        transition_type = proj_settings.get("transition_type", "crossfade")

        scene_specs = await director.analyze_script(
            script_text=request.script_text,
            target_duration_minutes=request.target_duration_minutes,
            scene_split_method=scene_split_method,
            default_emotion=default_emotion,
            default_background=default_background,
            default_transition=transition_type,
        )

        project.total_scenes = len(scene_specs)
        project.status = "draft"

        # Create scene records
        for spec in scene_specs:
            scene = ProjectScene(
                id=uuid.uuid4(),
                project_id=project_id,
                scene_index=spec.scene_index,
                script_text=spec.script_text,
                duration_seconds=spec.duration_seconds,
                emotion=spec.emotion,
                background=spec.background,
                transition_type=spec.transition_type,
                transition_duration=spec.transition_duration,
                status="pending",
            )
            db.add(scene)

    except Exception as e:
        logger.error("project.analysis_failed", error=str(e))
        project.status = "draft"
        project.total_scenes = 0

    await db.commit()
    await db.refresh(project)

    # Re-query with scenes loaded
    result = await db.execute(
        select(VideoProject)
        .where(VideoProject.id == project_id)
        .options(selectinload(VideoProject.scenes))
    )
    project = result.scalar_one()

    logger.info(
        "project.created",
        project_id=str(project_id),
        scenes=project.total_scenes,
    )

    return _project_to_response(project)


# ── Get Project ──

@router.get("/{project_id}")
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get project details with all scenes and consistency scores."""
    result = await db.execute(
        select(VideoProject)
        .where(VideoProject.id == uuid.UUID(project_id))
        .options(selectinload(VideoProject.scenes))
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return _project_to_response(project)


# ── Start Generation ──

@router.post("/{project_id}/generate")
async def generate_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Start identity-locked multi-scene generation for a project.
    Runs in the background — track progress via GET /project/{id}/progress.
    """
    result = await db.execute(
        select(VideoProject)
        .where(VideoProject.id == uuid.UUID(project_id))
        .options(selectinload(VideoProject.scenes))
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.status == "generating":
        raise HTTPException(status_code=409, detail="Project is already generating")

    project.status = "generating"
    project.completed_scenes = 0
    await db.commit()

    # Start generation in background
    background_tasks.add_task(
        _run_project_generation,
        str(project.id),
        project.identity_anchor_path,
        project.identity_anchor_id,
        project.avatar_photo_path,
        project.avatar_voice_path,
    )

    return {
        "status": "generating",
        "project_id": project_id,
        "message": f"Started generation for {project.total_scenes} scenes",
    }


# ── Generation Progress ──

@router.get("/{project_id}/progress")
async def get_project_progress(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get real-time generation progress."""
    result = await db.execute(
        select(VideoProject)
        .where(VideoProject.id == uuid.UUID(project_id))
        .options(selectinload(VideoProject.scenes))
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    total = project.total_scenes or 1
    completed = project.completed_scenes or 0
    progress = (completed / total) * 100 if total > 0 else 0

    # Find current generating scene
    current_scene = None
    if project.scenes:
        for s in project.scenes:
            if s.status == "generating":
                current_scene = s.scene_index
                break

    return ProjectProgressResponse(
        project_id=project_id,
        status=project.status or "unknown",
        total_scenes=total,
        completed_scenes=completed,
        current_scene_index=current_scene,
        overall_identity_score=project.overall_identity_score,
        progress_percent=round(progress, 1),
    )


# ── Consistency Report ──

@router.get("/{project_id}/consistency")
async def get_consistency_report(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get full identity consistency report for a completed project."""
    result = await db.execute(
        select(VideoProject)
        .where(VideoProject.id == uuid.UUID(project_id))
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.consistency_report_json:
        return json.loads(project.consistency_report_json)

    return {
        "project_id": project_id,
        "status": "no report available",
        "overall_identity_score": project.overall_identity_score,
        "overall_color_score": project.overall_color_score,
    }


# ── Regenerate Scene ──

@router.post("/{project_id}/regenerate/{scene_index}")
async def regenerate_scene(
    project_id: str,
    scene_index: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Regenerate a single scene using the same identity anchor."""
    result = await db.execute(
        select(VideoProject)
        .where(VideoProject.id == uuid.UUID(project_id))
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Find the scene
    scene_result = await db.execute(
        select(ProjectScene)
        .where(
            ProjectScene.project_id == uuid.UUID(project_id),
            ProjectScene.scene_index == scene_index,
        )
    )
    scene = scene_result.scalar_one_or_none()

    if not scene:
        raise HTTPException(status_code=404, detail=f"Scene {scene_index} not found")

    scene.status = "pending"
    scene.identity_score = None
    scene.color_consistency_score = None
    scene.retries = 0
    await db.commit()

    return {
        "status": "queued",
        "scene_index": scene_index,
        "message": f"Scene {scene_index} queued for regeneration",
    }


# ── Delete Project ──

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a project and all its scenes."""
    result = await db.execute(
        select(VideoProject)
        .where(VideoProject.id == uuid.UUID(project_id))
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()

    return {"status": "deleted", "project_id": project_id}


# ── List Projects ──

@router.get("/")
async def list_projects(
    status: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all projects with optional status filter."""
    query = select(VideoProject).order_by(VideoProject.created_at.desc())

    if status:
        query = query.where(VideoProject.status == status)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query.options(selectinload(VideoProject.scenes)))
    projects = result.scalars().all()

    return [_project_to_response(p) for p in projects]


# ── Background Generation Task ──

async def _run_project_generation(
    project_id: str,
    anchor_path: Optional[str],
    anchor_id: Optional[str],
    photo_path: str,
    voice_path: Optional[str],
):
    """Background task to run multi-scene generation."""
    from ..models.database import async_session
    from ..services.identity_anchor import IdentityAnchorService
    from ..services.director_agent import DirectorAgent, SceneSpec

    try:
        # Load identity anchor
        anchor_service = IdentityAnchorService()

        if anchor_path and anchor_id:
            anchor = await anchor_service.load_anchor(project_id, anchor_id)
        else:
            anchor = await anchor_service.create_anchor(photo_path, voice_path)

        # Load scenes from DB
        async with async_session() as db:
            result = await db.execute(
                select(VideoProject)
                .where(VideoProject.id == uuid.UUID(project_id))
                .options(selectinload(VideoProject.scenes))
            )
            project = result.scalar_one()

            scene_specs = []
            for s in sorted(project.scenes, key=lambda x: x.scene_index):
                scene_specs.append(SceneSpec(
                    scene_index=s.scene_index,
                    script_text=s.script_text,
                    duration_seconds=s.duration_seconds,
                    emotion=s.emotion or "neutral",
                    background=s.background or "original",
                    transition_type=s.transition_type or "crossfade",
                    transition_duration=s.transition_duration or 0.5,
                    word_count=len(s.script_text.split()),
                ))

        # Run director agent
        director = DirectorAgent(
            identity_anchor=anchor,
            device=settings.DEVICE,
            model_cache_dir=settings.MODEL_CACHE_DIR,
        )

        gen_result = await director.generate_project(project_id, scene_specs)

        # Update DB with results
        async with async_session() as db:
            result = await db.execute(
                select(VideoProject)
                .where(VideoProject.id == uuid.UUID(project_id))
                .options(selectinload(VideoProject.scenes))
            )
            project = result.scalar_one()

            project.status = gen_result.status
            project.completed_scenes = gen_result.completed_scenes
            project.overall_identity_score = gen_result.overall_identity_score
            project.overall_color_score = gen_result.overall_color_score
            project.output_path = gen_result.final_video_path
            project.processing_time_seconds = gen_result.processing_time_seconds

            if gen_result.consistency_report:
                project.consistency_report_json = json.dumps(gen_result.consistency_report)

            # Update individual scene records
            for sr in gen_result.scene_results:
                for db_scene in project.scenes:
                    if db_scene.scene_index == sr.scene_index:
                        db_scene.status = sr.status
                        db_scene.output_path = sr.video_path
                        db_scene.output_audio_path = sr.audio_path
                        db_scene.identity_score = sr.identity_score
                        db_scene.color_consistency_score = sr.color_score
                        db_scene.cross_scene_score = sr.cross_scene_score
                        db_scene.drift_frame_count = sr.drift_frame_count
                        db_scene.retries = sr.retries
                        break

            await db.commit()

        logger.info("project.generation_complete", project_id=project_id)

    except Exception as e:
        logger.error("project.generation_failed", project_id=project_id, error=str(e))

        async with async_session() as db:
            result = await db.execute(
                select(VideoProject)
                .where(VideoProject.id == uuid.UUID(project_id))
            )
            project = result.scalar_one_or_none()
            if project:
                project.status = "failed"
                await db.commit()
