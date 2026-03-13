"""AI Writer API routes."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
from shared.auth import get_current_user
from ..engines import generate_content, rewrite_content, generate_seo, CONTENT_TYPES, TONES

router = APIRouter()


class ContentRequest(BaseModel):
    content_type: str
    topic: str = Field(min_length=1, max_length=500)
    tone: str = "professional"
    keywords: list[str] = []
    target_audience: str = ""
    word_count: int = Field(default=500, ge=50, le=5000)


class RewriteRequest(BaseModel):
    content: str = Field(min_length=1, max_length=50000)
    tone: str = "professional"
    instructions: str = ""


class SEORequest(BaseModel):
    url: str = ""
    topic: str = Field(min_length=1, max_length=500)
    keywords: list[str] = []


@router.post("/generate")
async def generate(req: ContentRequest, user: dict = Depends(get_current_user)):
    result = generate_content(req.content_type, req.topic, req.tone, req.keywords, req.target_audience, req.word_count)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    credits = CONTENT_TYPES.get(req.content_type, {}).get("credits", 1)
    return {"success": True, "credits_used": credits, "data": result}


@router.post("/rewrite")
async def rewrite(req: RewriteRequest, user: dict = Depends(get_current_user)):
    result = rewrite_content(req.content, req.tone, req.instructions)
    return {"success": True, "credits_used": 2, "data": result}


@router.post("/seo")
async def seo(req: SEORequest, user: dict = Depends(get_current_user)):
    result = generate_seo(req.url, req.topic, req.keywords)
    return {"success": True, "credits_used": 2, "data": result}


@router.get("/content-types")
async def get_content_types():
    return {"content_types": CONTENT_TYPES}


@router.get("/tones")
async def get_tones():
    return {"tones": TONES}
