"""Voice Studio API routes."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
from shared.auth import get_current_user
from ..engines import text_to_speech, clone_voice, dub_audio, list_voices, get_voice_styles, get_supported_languages

router = APIRouter()


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    voice_id: str = "aria"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)


class CloneRequest(BaseModel):
    voice_name: str = Field(min_length=1, max_length=100)
    audio_urls: list[str] = Field(min_length=1, max_length=20)


class DubRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    target_language: str = Field(min_length=2, max_length=5)
    voice_id: str = "aria"


@router.post("/tts")
async def generate_speech(req: TTSRequest, user: dict = Depends(get_current_user)):
    result = text_to_speech(req.text, req.voice_id, req.speed, req.pitch)
    return {"success": True, "credits_used": 1, "data": result}


@router.post("/clone")
async def clone_voice_endpoint(req: CloneRequest, user: dict = Depends(get_current_user)):
    result = clone_voice(req.audio_urls, req.voice_name)
    return {"success": True, "credits_used": 5, "data": result}


@router.post("/dub")
async def dub_endpoint(req: DubRequest, user: dict = Depends(get_current_user)):
    result = dub_audio(req.text, req.target_language, req.voice_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "credits_used": 10, "data": result}


@router.get("/voices")
async def get_voices():
    return {"voices": list_voices()}


@router.get("/styles")
async def get_styles():
    return {"styles": get_voice_styles()}


@router.get("/languages")
async def get_languages():
    return {"languages": get_supported_languages()}
