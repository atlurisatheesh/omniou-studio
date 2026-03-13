"""Code Studio API routes."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
from shared.auth import get_current_user
from ..engines import generate_code, explain_code, refactor_code, create_project, deploy_project, SUPPORTED_LANGUAGES, PROJECT_TEMPLATES

router = APIRouter()


class GenerateCodeRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=5000)
    language: str = "python"
    context: str = ""


class ExplainRequest(BaseModel):
    code: str = Field(min_length=1, max_length=50000)
    language: str = "python"


class RefactorRequest(BaseModel):
    code: str = Field(min_length=1, max_length=50000)
    language: str = "python"
    instructions: str = ""


class ProjectRequest(BaseModel):
    template: str
    name: str = Field(min_length=1, max_length=100)


class DeployRequest(BaseModel):
    project_id: str


@router.post("/generate")
async def generate(req: GenerateCodeRequest, user: dict = Depends(get_current_user)):
    if req.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Language '{req.language}' not supported")
    result = generate_code(req.prompt, req.language, req.context)
    return {"success": True, "credits_used": 2, "data": result}


@router.post("/explain")
async def explain(req: ExplainRequest, user: dict = Depends(get_current_user)):
    result = explain_code(req.code, req.language)
    return {"success": True, "credits_used": 1, "data": result}


@router.post("/refactor")
async def refactor(req: RefactorRequest, user: dict = Depends(get_current_user)):
    result = refactor_code(req.code, req.language, req.instructions)
    return {"success": True, "credits_used": 2, "data": result}


@router.post("/project")
async def new_project(req: ProjectRequest, user: dict = Depends(get_current_user)):
    result = create_project(req.template, req.name)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "credits_used": 0, "data": result}


@router.post("/deploy")
async def deploy(req: DeployRequest, user: dict = Depends(get_current_user)):
    result = deploy_project(req.project_id)
    return {"success": True, "credits_used": 5, "data": result}


@router.get("/languages")
async def get_languages():
    return {"languages": SUPPORTED_LANGUAGES}


@router.get("/templates")
async def get_templates():
    return {"templates": PROJECT_TEMPLATES}
