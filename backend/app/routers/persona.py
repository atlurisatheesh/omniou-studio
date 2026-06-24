"""
CLONEAI ULTRA — Persona Router (Self-Cloning Agent API)
==========================================================
API endpoints for managing persistent personas (digital clones).

Endpoints:
  POST   /persona/create          → Create a persona from photo + voice
  GET    /persona/                → List all personas
  GET    /persona/{id}            → Get persona details
  POST   /persona/{id}/generate   → Generate video using persona
  DELETE /persona/{id}            → Delete persona
"""

import json
import uuid
from datetime import datetime

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.database import Persona, get_db
from ..models.schemas import (
    PersonaCreateRequest,
    PersonaGenerateRequest,
    PersonaResponse,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/persona", tags=["Persona"])


# ── Create Persona ──

@router.post("/create")
async def create_persona(
    request: PersonaCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a persistent persona (digital clone).
    
    Extracts and stores:
      - Face identity anchor (InsightFace embedding + appearance)
      - Voice embedding (XTTS conditioning latent)
      - Speaking style profile
    
    This persona can be reused across unlimited video generations.
    """
    persona_id = uuid.uuid4()

    try:
        from ..services.identity_anchor import IdentityAnchorService

        # Create identity anchor
        anchor_service = IdentityAnchorService()
        anchor = await anchor_service.create_anchor(
            photo_path=request.photo_path,
            voice_path=request.voice_path,
        )

        # Save anchor
        anchor_path = await anchor_service.save_anchor(anchor, f"persona_{persona_id}")

        persona = Persona(
            id=persona_id,
            name=request.name,
            photo_path=request.photo_path,
            voice_path=request.voice_path,
            identity_anchor_path=anchor_path,
        )

        db.add(persona)
        await db.commit()
        await db.refresh(persona)

        logger.info("persona.created", persona_id=str(persona_id), name=request.name)

        return PersonaResponse(
            id=str(persona.id),
            name=persona.name,
            videos_generated=0,
            is_active=True,
            created_at=persona.created_at,
        )

    except Exception as e:
        logger.error("persona.create_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create persona: {str(e)}")


# ── List Personas ──

@router.get("/")
async def list_personas(db: AsyncSession = Depends(get_db)):
    """List all personas."""
    result = await db.execute(
        select(Persona).where(Persona.is_active == True).order_by(Persona.created_at.desc())
    )
    personas = result.scalars().all()

    return [
        PersonaResponse(
            id=str(p.id),
            name=p.name,
            videos_generated=p.videos_generated or 0,
            avg_identity_score=p.avg_identity_score,
            is_active=p.is_active,
            created_at=p.created_at,
        )
        for p in personas
    ]


# ── Get Persona ──

@router.get("/{persona_id}")
async def get_persona(
    persona_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get persona details."""
    result = await db.execute(
        select(Persona).where(Persona.id == uuid.UUID(persona_id))
    )
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    return PersonaResponse(
        id=str(persona.id),
        name=persona.name,
        videos_generated=persona.videos_generated or 0,
        avg_identity_score=persona.avg_identity_score,
        is_active=persona.is_active,
        created_at=persona.created_at,
    )


# ── Generate Video with Persona ──

@router.post("/{persona_id}/generate")
async def generate_with_persona(
    persona_id: str,
    request: PersonaGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a long-form video using a saved persona.
    
    The saved identity anchor ensures the video looks and sounds
    exactly like the persona — every time, guaranteed.
    """
    result = await db.execute(
        select(Persona).where(Persona.id == uuid.UUID(persona_id))
    )
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    script_text = request.script_text

    # If no script, generate from prompt using LLM
    if not script_text and request.prompt:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={
                        "model": settings.DIRECTOR_LLM_MODEL,
                        "prompt": f"Write a {request.target_duration_minutes}-minute video script about: {request.prompt}. Write naturally as if speaking directly to camera. No stage directions.",
                        "stream": False,
                    },
                )
                if resp.status_code == 200:
                    script_text = resp.json().get("response", "")
        except Exception as e:
            logger.warning("persona.script_gen_failed", error=str(e))

    if not script_text:
        raise HTTPException(
            status_code=400,
            detail="Either script_text or prompt must be provided",
        )

    # Create a project for this persona generation
    from ..models.database import VideoProject, ProjectScene

    project_id = uuid.uuid4()
    project = VideoProject(
        id=project_id,
        name=f"{persona.name} — Generated Video",
        full_script=script_text,
        target_duration_minutes=request.target_duration_minutes,
        avatar_photo_path=persona.photo_path,
        avatar_voice_path=persona.voice_path,
        identity_anchor_path=persona.identity_anchor_path,
        status="generating",
        settings_json=json.dumps({
            "persona_id": persona_id,
            "emotion": request.emotion,
            "background": request.background,
        }),
    )

    db.add(project)
    await db.flush()

    # Analyze and create scenes
    try:
        from ..services.identity_anchor import IdentityAnchorService
        from ..services.director_agent import DirectorAgent

        anchor_service = IdentityAnchorService()
        anchor_path = persona.identity_anchor_path

        # Extract anchor_id from path
        import os
        anchor_id = os.path.basename(anchor_path).replace(".pkl", "") if anchor_path else None

        if anchor_path and anchor_id:
            anchor = await anchor_service.load_anchor(
                f"persona_{persona_id}", anchor_id
            )
        else:
            anchor = await anchor_service.create_anchor(
                persona.photo_path, persona.voice_path
            )

        director = DirectorAgent(identity_anchor=anchor)
        scene_specs = await director.analyze_script(
            script_text=script_text,
            target_duration_minutes=request.target_duration_minutes,
            default_emotion=request.emotion,
            default_background=request.background,
        )

        project.total_scenes = len(scene_specs)

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

    except Exception as e:
        logger.error("persona.scene_analysis_failed", error=str(e))
        project.total_scenes = 0

    await db.commit()

    # Start generation in background
    from .project import _run_project_generation

    background_tasks.add_task(
        _run_project_generation,
        str(project_id),
        persona.identity_anchor_path,
        anchor_id,
        persona.photo_path,
        persona.voice_path,
    )

    # Increment persona counter
    persona.videos_generated = (persona.videos_generated or 0) + 1
    await db.commit()

    return {
        "status": "generating",
        "persona_id": persona_id,
        "project_id": str(project_id),
        "scenes": len(scene_specs) if 'scene_specs' in dir() else 0,
        "message": "Video generation started with persona identity lock",
    }


# ── Delete Persona ──

@router.delete("/{persona_id}")
async def delete_persona(
    persona_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a persona."""
    result = await db.execute(
        select(Persona).where(Persona.id == uuid.UUID(persona_id))
    )
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    persona.is_active = False
    await db.commit()

    return {"status": "deleted", "persona_id": persona_id}
