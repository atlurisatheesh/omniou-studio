"""
CLONEAI ULTRA — Quick Generate Router
=======================================
One-click video generation from script text.
No project creation needed — just paste script, upload photo, get video.

POST /api/v1/quick-generate
{
    "photo_path": "uploads/photos/me.jpg",
    "voice_path": "uploads/voices/me.wav",
    "script_text": "Welcome to AtluriIn AI...",
    "emotion": "professional",
    "name": "Product Overview"
}
"""

import json
import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import settings
from ..models.database import ProjectScene, VideoProject, get_db

logger = structlog.get_logger()

router = APIRouter(prefix="/quick-generate", tags=["QuickGenerate"])


class QuickGenerateRequest(BaseModel):
    """One-shot video generation from script."""
    photo_path: str = Field(..., description="Path to uploaded face photo")
    voice_path: Optional[str] = Field(default=None, description="Path to voice sample")
    script_text: str = Field(..., min_length=10, max_length=50000, description="Full script")
    emotion: str = Field(default="professional", description="Emotion for all scenes")
    background: str = Field(default="original")
    name: str = Field(default="Quick Video", max_length=255)
    identity_threshold: float = Field(default=0.75, ge=0.5, le=0.95)
    scene_split_method: str = Field(default="sentence_group", description="ai | paragraph | sentence_group")


class QuickGenerateResponse(BaseModel):
    project_id: str
    status: str
    total_scenes: int
    estimated_duration_seconds: float
    message: str


@router.post("/", response_model=QuickGenerateResponse)
async def quick_generate(
    request: QuickGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    One-click video generation from a script.
    
    This endpoint:
      1. Creates an identity anchor from your photo + voice
      2. Analyzes and splits the script into optimal scenes
      3. Starts identity-locked generation in the background
    
    Track progress via GET /api/v1/project/{id}/progress
    """
    project_id = uuid.uuid4()
    
    try:
        from ..services.identity_anchor import IdentityAnchorService
        from ..services.director_agent import DirectorAgent
        
        # Create identity anchor
        anchor_service = IdentityAnchorService()
        anchor = await anchor_service.create_anchor(
            photo_path=request.photo_path,
            voice_path=request.voice_path,
        )
        
        # Save anchor
        anchor_path = await anchor_service.save_anchor(anchor, str(project_id))
        
        # Analyze script
        director = DirectorAgent(identity_anchor=anchor)
        word_count = len(request.script_text.split())
        target_minutes = max(1, word_count / 150)
        
        scene_specs = await director.analyze_script(
            script_text=request.script_text,
            target_duration_minutes=target_minutes,
            scene_split_method=request.scene_split_method,
            default_emotion=request.emotion,
            default_background=request.background,
        )
        
        total_duration = sum(s.duration_seconds for s in scene_specs)
        
        # Create project in DB
        project = VideoProject(
            id=project_id,
            name=request.name,
            full_script=request.script_text,
            target_duration_minutes=target_minutes,
            avatar_photo_path=request.photo_path,
            avatar_voice_path=request.voice_path,
            identity_anchor_id=anchor.anchor_id,
            identity_anchor_path=anchor_path,
            status="generating",
            total_scenes=len(scene_specs),
            settings_json=json.dumps({
                "emotion": request.emotion,
                "background": request.background,
                "identity_threshold": request.identity_threshold,
                "scene_split_method": request.scene_split_method,
                "quick_generate": True,
            }),
        )
        
        db.add(project)
        await db.flush()
        
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
                status="pending",
            )
            db.add(scene)
        
        await db.commit()
        
        # Start generation in background
        from ..routers.project import _run_project_generation
        
        background_tasks.add_task(
            _run_project_generation,
            str(project_id),
            anchor_path,
            anchor.anchor_id,
            request.photo_path,
            request.voice_path,
        )
        
        logger.info(
            "quick_generate.started",
            project_id=str(project_id),
            scenes=len(scene_specs),
            words=word_count,
            duration=round(total_duration, 1),
        )
        
        return QuickGenerateResponse(
            project_id=str(project_id),
            status="generating",
            total_scenes=len(scene_specs),
            estimated_duration_seconds=round(total_duration, 1),
            message=f"Started generating {len(scene_specs)} scenes (~{total_duration/60:.1f} min). Track progress: GET /api/v1/project/{project_id}/progress",
        )
    
    except Exception as e:
        logger.error("quick_generate.failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
