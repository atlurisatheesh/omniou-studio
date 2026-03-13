from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.engines.video_engine import (
    generate_video, face_swap, edit_video, upscale_video,
    STYLES, RESOLUTIONS, SUPPORTED_FORMATS,
)

router = APIRouter()


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    duration: int = Field(15, ge=5, le=120)
    style: str = "cinematic"
    resolution: str = "1080p"


class FaceSwapRequest(BaseModel):
    source_video_url: str
    target_face_url: str
    enhance: bool = True


class EditRequest(BaseModel):
    video_url: str
    operations: list[dict] = Field(..., min_length=1)


class UpscaleRequest(BaseModel):
    video_url: str
    target_resolution: str = "4K"


@router.post("/generate")
async def api_generate(req: GenerateRequest):
    if req.style not in STYLES:
        raise HTTPException(400, f"Invalid style. Choose from: {STYLES}")
    if req.resolution not in RESOLUTIONS:
        raise HTTPException(400, f"Invalid resolution. Choose from: {RESOLUTIONS}")
    return await generate_video(req.prompt, req.duration, req.style, req.resolution)


@router.post("/face-swap")
async def api_face_swap(req: FaceSwapRequest):
    return await face_swap(req.source_video_url, req.target_face_url, req.enhance)


@router.post("/edit")
async def api_edit(req: EditRequest):
    return await edit_video(req.video_url, req.operations)


@router.post("/upscale")
async def api_upscale(req: UpscaleRequest):
    if req.target_resolution not in RESOLUTIONS:
        raise HTTPException(400, f"Invalid resolution. Choose from: {RESOLUTIONS}")
    return await upscale_video(req.video_url, req.target_resolution)


@router.get("/styles")
async def get_styles():
    return {"styles": STYLES}


@router.get("/resolutions")
async def get_resolutions():
    return {"resolutions": RESOLUTIONS}


@router.get("/formats")
async def get_formats():
    return {"formats": SUPPORTED_FORMATS}
