"""
CLONEAI ULTRA — Script AI Router
==================================
Endpoints for AI-powered script generation via Ollama.
"""

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()
logger = structlog.get_logger()


class ScriptRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500, description="Topic for the video script")
    tone: str = Field(default="professional", description="professional | casual | educational | motivational | funny")
    duration_seconds: int = Field(default=60, ge=10, le=300, description="Target video duration in seconds")
    language: str = Field(default="en", description="ISO language code")


class ScriptResponse(BaseModel):
    script: str
    word_count: int
    estimated_duration: float


@router.post("/script/generate", response_model=ScriptResponse)
async def generate_script(req: ScriptRequest):
    """
    Generate a video script using AI (Ollama LLM).
    
    Falls back to template-based generation when Ollama is unavailable.
    """
    from ..services.script_ai import ScriptAIService

    service = ScriptAIService()

    try:
        result = await service.generate(
            topic=req.topic,
            tone=req.tone,
            duration_seconds=req.duration_seconds,
            language=req.language,
        )
        return ScriptResponse(**result)
    except Exception as e:
        logger.error("script.generate_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")
