from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.engines.video_engine import (
    generate_video, face_swap, edit_video, upscale_video,
    STYLES, RESOLUTIONS, ASPECT_RATIOS, SUPPORTED_FORMATS, VIDEO_PROVIDERS,
    get_job_progress,
)
from app.engines.providers import get_available_providers
from app.engines.auto_publish_engine import list_platforms, publish_video

router = APIRouter()


QUALITY_TIERS = ["standard", "high", "ultra"]


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    script: str | None = Field(None, max_length=50000, description="Full screenplay/script text — scenes auto-detected")
    duration: int = Field(15, ge=5, le=600)
    style: str = "cinematic"
    resolution: str = "1080p"
    quality: str = "high"
    aspect_ratio: str = "16:9"
    include_narration: bool = True
    include_music: bool = True
    voice: str = "onyx"
    provider: str = "auto"
    enable_lip_sync: bool = False
    publish_to: list[str] | None = None


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


class PublishRequest(BaseModel):
    video_file: str
    platforms: list[str] = Field(..., min_length=1)
    title: str = ""
    description: str = ""
    tags: list[str] = []


@router.post("/generate")
async def api_generate(req: GenerateRequest):
    if req.style not in STYLES:
        raise HTTPException(400, f"Invalid style. Choose from: {STYLES}")
    if req.resolution not in RESOLUTIONS:
        raise HTTPException(400, f"Invalid resolution. Choose from: {RESOLUTIONS}")
    if req.quality not in QUALITY_TIERS:
        raise HTTPException(400, f"Invalid quality. Choose from: {QUALITY_TIERS}")
    if req.aspect_ratio not in ASPECT_RATIOS:
        raise HTTPException(400, f"Invalid aspect ratio. Choose from: {ASPECT_RATIOS}")
    if req.provider != "auto" and req.provider not in VIDEO_PROVIDERS:
        raise HTTPException(400, f"Invalid provider. Choose from: auto, {', '.join(VIDEO_PROVIDERS)}")
    return await generate_video(
        req.prompt, req.duration, req.style, req.resolution,
        quality=req.quality,
        aspect_ratio=req.aspect_ratio,
        include_narration=req.include_narration,
        include_music=req.include_music,
        voice=req.voice,
        provider=req.provider,
        enable_lip_sync=req.enable_lip_sync,
        publish_to=req.publish_to,
        script=req.script,
    )


@router.get("/progress/{job_id}")
async def api_progress(job_id: str):
    progress = get_job_progress(job_id)
    if progress.get("status") == "not_found":
        raise HTTPException(404, "Job not found")
    return progress


@router.get("/providers")
async def api_providers():
    """List all video generation providers and their availability."""
    return {"providers": get_available_providers()}


@router.post("/publish")
async def api_publish(req: PublishRequest):
    """Publish a video to social media platforms."""
    valid = [p["id"] for p in list_platforms()]
    for p in req.platforms:
        if p not in valid:
            raise HTTPException(400, f"Invalid platform '{p}'. Choose from: {valid}")
    results = []
    for platform in req.platforms:
        result = await publish_video(
            video_file=req.video_file,
            platform=platform,
            title=req.title,
            description=req.description,
            tags=req.tags,
        )
        results.append(result)
    return {"results": results}


@router.get("/platforms")
async def api_platforms():
    """List supported publishing platforms."""
    return {"platforms": list_platforms()}


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
