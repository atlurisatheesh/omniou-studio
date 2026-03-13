"""Workflow Engine API routes — Create, manage, run multi-step pipelines."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
from shared.auth import get_current_user

router = APIRouter()

# In-memory workflow storage (use DB in production)
workflows_db: dict[str, dict] = {}

AVAILABLE_STEPS = {
    "writer.generate": {"service": "writer", "action": "generate", "credits": 3, "description": "Generate written content"},
    "voice.tts": {"service": "voice", "action": "tts", "credits": 1, "description": "Convert text to speech"},
    "voice.dub": {"service": "voice", "action": "dub", "credits": 10, "description": "Translate and dub audio"},
    "design.generate": {"service": "design", "action": "generate", "credits": 3, "description": "Generate AI image"},
    "design.remove_bg": {"service": "design", "action": "remove-background", "credits": 2, "description": "Remove image background"},
    "code.generate": {"service": "code", "action": "generate", "credits": 2, "description": "Generate code"},
    "music.generate": {"service": "music", "action": "generate", "credits": 5, "description": "Generate music track"},
    "video.generate": {"service": "video", "action": "generate", "credits": 15, "description": "Generate video"},
}

WORKFLOW_TEMPLATES = {
    "content_campaign": {
        "name": "Content Campaign",
        "description": "Write blog → Generate cover image → Create social posts → Generate voiceover",
        "steps": [
            {"id": "step_1", "type": "writer.generate", "config": {"content_type": "blog_post"}},
            {"id": "step_2", "type": "design.generate", "config": {"style": "digital_art"}, "depends_on": "step_1"},
            {"id": "step_3", "type": "writer.generate", "config": {"content_type": "social_post"}, "depends_on": "step_1"},
            {"id": "step_4", "type": "voice.tts", "config": {"voice_id": "aria"}, "depends_on": "step_1"},
        ],
    },
    "video_production": {
        "name": "Video Production",
        "description": "Write script → Generate voiceover → Create thumbnail → Produce video",
        "steps": [
            {"id": "step_1", "type": "writer.generate", "config": {"content_type": "script"}},
            {"id": "step_2", "type": "voice.tts", "config": {"voice_id": "marcus"}, "depends_on": "step_1"},
            {"id": "step_3", "type": "design.generate", "config": {"style": "photorealistic"}, "depends_on": "step_1"},
            {"id": "step_4", "type": "music.generate", "config": {"genre": "cinematic"}, "depends_on": "step_1"},
        ],
    },
    "brand_kit": {
        "name": "Brand Kit Generator",
        "description": "Generate logo → Create brand colors → Design social templates",
        "steps": [
            {"id": "step_1", "type": "design.generate", "config": {"style": "minimalist"}},
            {"id": "step_2", "type": "design.generate", "config": {"style": "digital_art"}, "depends_on": "step_1"},
            {"id": "step_3", "type": "writer.generate", "config": {"content_type": "landing_page"}, "depends_on": "step_1"},
        ],
    },
    "podcast_pipeline": {
        "name": "Podcast Pipeline",
        "description": "Write script → Generate voices → Add music → Create artwork",
        "steps": [
            {"id": "step_1", "type": "writer.generate", "config": {"content_type": "script"}},
            {"id": "step_2", "type": "voice.tts", "config": {"voice_id": "priya"}, "depends_on": "step_1"},
            {"id": "step_3", "type": "music.generate", "config": {"genre": "lo_fi", "mood": "calm"}, "depends_on": "step_1"},
            {"id": "step_4", "type": "design.generate", "config": {"style": "digital_art"}, "depends_on": "step_1"},
        ],
    },
}


class WorkflowStep(BaseModel):
    id: str
    type: str
    config: dict = {}
    depends_on: Optional[str] = None


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    steps: list[WorkflowStep] = Field(min_length=1, max_length=20)


class WorkflowFromTemplate(BaseModel):
    template: str
    name: Optional[str] = None
    overrides: dict = {}


@router.post("/create")
async def create_workflow(req: WorkflowCreate, user: dict = Depends(get_current_user)):
    # Validate step types
    for step in req.steps:
        if step.type not in AVAILABLE_STEPS:
            raise HTTPException(status_code=400, detail=f"Unknown step type: {step.type}")

    wf_id = f"wf_{uuid.uuid4().hex[:8]}"
    total_credits = sum(AVAILABLE_STEPS[s.type]["credits"] for s in req.steps)

    workflow = {
        "id": wf_id,
        "name": req.name,
        "description": req.description,
        "steps": [s.model_dump() for s in req.steps],
        "total_credits": total_credits,
        "user_id": user["id"],
        "status": "created",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    workflows_db[wf_id] = workflow
    return {"success": True, "data": workflow}


@router.post("/from-template")
async def from_template(req: WorkflowFromTemplate, user: dict = Depends(get_current_user)):
    template = WORKFLOW_TEMPLATES.get(req.template)
    if not template:
        raise HTTPException(status_code=400, detail=f"Template '{req.template}' not found")

    wf_id = f"wf_{uuid.uuid4().hex[:8]}"
    total_credits = sum(AVAILABLE_STEPS.get(s["type"], {}).get("credits", 0) for s in template["steps"])

    workflow = {
        "id": wf_id,
        "name": req.name or template["name"],
        "description": template["description"],
        "steps": template["steps"],
        "total_credits": total_credits,
        "user_id": user["id"],
        "status": "created",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    workflows_db[wf_id] = workflow
    return {"success": True, "data": workflow}


@router.post("/run/{workflow_id}")
async def run_workflow(workflow_id: str, user: dict = Depends(get_current_user)):
    workflow = workflows_db.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Simulate running each step
    results = []
    for step in workflow["steps"]:
        step_info = AVAILABLE_STEPS.get(step["type"], {})
        results.append({
            "step_id": step["id"],
            "type": step["type"],
            "status": "completed",
            "credits_used": step_info.get("credits", 0),
            "output": {"file_id": f"out_{uuid.uuid4().hex[:6]}", "message": f"Step {step['id']} completed"},
        })

    workflow["status"] = "completed"
    workflow["results"] = results
    workflow["completed_at"] = datetime.now(timezone.utc).isoformat()

    return {
        "success": True,
        "credits_used": workflow["total_credits"],
        "data": {"workflow_id": workflow_id, "status": "completed", "results": results},
    }


@router.get("/list")
async def list_workflows(user: dict = Depends(get_current_user)):
    user_workflows = [wf for wf in workflows_db.values() if wf["user_id"] == user["id"]]
    return {"workflows": user_workflows}


@router.get("/templates")
async def get_templates():
    return {"templates": WORKFLOW_TEMPLATES}


@router.get("/steps")
async def get_available_steps():
    return {"steps": AVAILABLE_STEPS}


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str, user: dict = Depends(get_current_user)):
    workflow = workflows_db.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return {"data": workflow}


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str, user: dict = Depends(get_current_user)):
    workflow = workflows_db.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    del workflows_db[workflow_id]
    return {"message": "Workflow deleted"}
