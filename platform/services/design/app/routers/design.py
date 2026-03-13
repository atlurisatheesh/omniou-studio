"""Design Studio API routes."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
from shared.auth import get_current_user
from ..engines import (
    generate_image, remove_background, upscale_image, create_from_template,
    list_templates, list_styles, list_filters,
)

router = APIRouter()


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    style: str = "photorealistic"
    width: int = Field(default=1024, ge=256, le=4096)
    height: int = Field(default=1024, ge=256, le=4096)
    negative_prompt: str = ""


class RemoveBgRequest(BaseModel):
    image_url: str


class UpscaleRequest(BaseModel):
    image_url: str
    scale: int = Field(default=2, ge=2, le=4)


class TemplateRequest(BaseModel):
    template_id: str
    category: str
    customizations: dict = {}


@router.post("/generate")
async def generate(req: GenerateRequest, user: dict = Depends(get_current_user)):
    result = generate_image(req.prompt, req.style, req.width, req.height, req.negative_prompt)
    return {"success": True, "credits_used": 3, "data": result}


@router.post("/remove-background")
async def remove_bg(req: RemoveBgRequest, user: dict = Depends(get_current_user)):
    result = remove_background(req.image_url)
    return {"success": True, "credits_used": 2, "data": result}


@router.post("/upscale")
async def upscale(req: UpscaleRequest, user: dict = Depends(get_current_user)):
    result = upscale_image(req.image_url, req.scale)
    return {"success": True, "credits_used": 2, "data": result}


@router.post("/from-template")
async def from_template(req: TemplateRequest, user: dict = Depends(get_current_user)):
    result = create_from_template(req.template_id, req.category, req.customizations)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "credits_used": 1, "data": result}


@router.get("/templates")
async def get_templates():
    return {"templates": list_templates()}


@router.get("/styles")
async def get_styles():
    return {"styles": list_styles()}


@router.get("/filters")
async def get_filters():
    return {"filters": list_filters()}
