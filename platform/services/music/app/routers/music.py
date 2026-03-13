"""Music Studio API routes."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
from shared.auth import get_current_user
from ..engines import generate_music, generate_jingle, generate_sfx, remix_audio, GENRES, MOODS, SFX_CATEGORIES

router = APIRouter()


class MusicRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=1000)
    genre: str = "ambient"
    mood: str = "calm"
    duration_seconds: int = Field(default=30, ge=5, le=300)
    bpm: int = Field(default=120, ge=60, le=200)


class JingleRequest(BaseModel):
    brand_name: str = Field(min_length=1, max_length=100)
    style: str = "corporate"
    duration_seconds: int = Field(default=15, ge=5, le=60)


class SFXRequest(BaseModel):
    category: str
    effect: str


class RemixRequest(BaseModel):
    audio_url: str
    genre: str = "lo_fi"
    tempo_change: float = Field(default=1.0, ge=0.5, le=2.0)


@router.post("/generate")
async def generate(req: MusicRequest, user: dict = Depends(get_current_user)):
    result = generate_music(req.prompt, req.genre, req.mood, req.duration_seconds, req.bpm)
    return {"success": True, "credits_used": 5, "data": result}


@router.post("/jingle")
async def jingle(req: JingleRequest, user: dict = Depends(get_current_user)):
    result = generate_jingle(req.brand_name, req.style, req.duration_seconds)
    return {"success": True, "credits_used": 5, "data": result}


@router.post("/sfx")
async def sfx(req: SFXRequest, user: dict = Depends(get_current_user)):
    result = generate_sfx(req.category, req.effect)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "credits_used": 2, "data": result}


@router.post("/remix")
async def remix(req: RemixRequest, user: dict = Depends(get_current_user)):
    result = remix_audio(req.audio_url, req.genre, req.tempo_change)
    return {"success": True, "credits_used": 3, "data": result}


@router.get("/genres")
async def get_genres():
    return {"genres": GENRES}


@router.get("/moods")
async def get_moods():
    return {"moods": MOODS}


@router.get("/sfx-categories")
async def get_sfx_categories():
    return {"categories": SFX_CATEGORIES}
