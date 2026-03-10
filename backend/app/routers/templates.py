"""
routers/templates.py — Video template presets (Phase 12).

GET  /templates           → list all templates
GET  /templates/{id}      → single template
POST /templates           → create custom template (auth required)
DELETE /templates/{id}    → delete custom template
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.utils.security import get_current_user, get_current_user_optional

router = APIRouter(prefix="/templates", tags=["templates"])


# ── Schemas ──
class TemplateResponse(BaseModel):
    id: str
    name: str
    category: str
    description: str
    default_emotion: str
    default_background: str
    default_language: str
    script_template: str
    thumbnail_emoji: str
    is_builtin: bool
    created_at: Optional[str]


class TemplateCreate(BaseModel):
    name: str
    category: str = "custom"
    description: str = ""
    default_emotion: str = "neutral"
    default_background: str = "original"
    default_language: str = "en"
    script_template: str = ""
    thumbnail_emoji: str = "🎬"


# ── Built-in templates ──
BUILTIN_TEMPLATES = [
    {
        "id": "tpl_product_demo",
        "name": "Product Demo",
        "category": "Marketing",
        "description": "Showcase a product with professional enthusiasm",
        "default_emotion": "excited",
        "default_background": "studio",
        "default_language": "en",
        "thumbnail_emoji": "🛍️",
        "script_template": (
            "Hi! I'm thrilled to introduce {product_name}. "
            "It solves {problem} by {solution}. "
            "Here's what makes it special: {key_feature}. "
            "Try it today at {call_to_action}."
        ),
        "is_builtin": True,
    },
    {
        "id": "tpl_course_intro",
        "name": "Course Introduction",
        "category": "Education",
        "description": "Welcome students to your course with warmth",
        "default_emotion": "happy",
        "default_background": "office",
        "default_language": "en",
        "thumbnail_emoji": "🎓",
        "script_template": (
            "Welcome to {course_name}! I'm {instructor_name}. "
            "In this course you'll learn {learning_outcomes}. "
            "By the end, you'll be able to {skill_gained}. "
            "Let's get started!"
        ),
        "is_builtin": True,
    },
    {
        "id": "tpl_linkedin_post",
        "name": "LinkedIn Video Post",
        "category": "Social Media",
        "description": "Professional LinkedIn-style talking-head video",
        "default_emotion": "neutral",
        "default_background": "office",
        "default_language": "en",
        "thumbnail_emoji": "💼",
        "script_template": (
            "I've been thinking about {topic}. "
            "Here's what most people get wrong: {insight}. "
            "The solution I've found is {solution}. "
            "What's your take? Drop a comment below."
        ),
        "is_builtin": True,
    },
    {
        "id": "tpl_youtube_intro",
        "name": "YouTube Channel Intro",
        "category": "Content Creation",
        "description": "Energetic intro for YouTube videos",
        "default_emotion": "excited",
        "default_background": "gradient",
        "default_language": "en",
        "thumbnail_emoji": "▶️",
        "script_template": (
            "What's up everyone, welcome back to {channel_name}! "
            "In today's video, we're covering {topic}. "
            "This is going to be {value_prop}. "
            "Smash that subscribe button and let's dive in!"
        ),
        "is_builtin": True,
    },
    {
        "id": "tpl_cold_outreach",
        "name": "Cold Outreach",
        "category": "Sales",
        "description": "Personal video message for sales prospecting",
        "default_emotion": "neutral",
        "default_background": "blur",
        "default_language": "en",
        "thumbnail_emoji": "📧",
        "script_template": (
            "Hi {first_name}, I'm {your_name} from {company}. "
            "I noticed {personalized_observation} and thought we could help. "
            "We've helped companies like {social_proof} achieve {result}. "
            "Worth a quick 15-minute call? Book here: {calendar_link}."
        ),
        "is_builtin": True,
    },
    {
        "id": "tpl_team_announcement",
        "name": "Team Announcement",
        "category": "Internal",
        "description": "Company or team announcement video",
        "default_emotion": "happy",
        "default_background": "office",
        "default_language": "en",
        "thumbnail_emoji": "📣",
        "script_template": (
            "Hey team, exciting news! {announcement}. "
            "This means {implication_for_team}. "
            "Starting {date}, {action_required}. "
            "Questions? Reach out to {contact}."
        ),
        "is_builtin": True,
    },
    {
        "id": "tpl_news_update",
        "name": "News Update",
        "category": "Media",
        "description": "Journalist-style news delivery",
        "default_emotion": "neutral",
        "default_background": "studio",
        "default_language": "en",
        "thumbnail_emoji": "📰",
        "script_template": (
            "Breaking news from {location}. {headline}. "
            "Here's what we know so far: {details}. "
            "Experts say {expert_opinion}. "
            "Stay tuned for updates."
        ),
        "is_builtin": True,
    },
    {
        "id": "tpl_tutorial",
        "name": "Tutorial / How-To",
        "category": "Education",
        "description": "Step-by-step tutorial narration",
        "default_emotion": "neutral",
        "default_background": "original",
        "default_language": "en",
        "thumbnail_emoji": "🛠️",
        "script_template": (
            "Today I'll show you how to {task}. "
            "You'll need: {prerequisites}. "
            "Step one: {step_1}. "
            "Step two: {step_2}. "
            "And that's it! You've successfully {outcome}."
        ),
        "is_builtin": True,
    },
]

BUILTIN_MAP = {t["id"]: t for t in BUILTIN_TEMPLATES}


# ── Endpoints ──
@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    templates = list(BUILTIN_TEMPLATES)
    try:
        result = await db.execute(text("SELECT * FROM video_templates ORDER BY created_at DESC"))
        for row in result.fetchall():
            d = dict(row._mapping)
            d["is_builtin"] = False
            templates.append(d)
    except Exception:
        pass
    if category:
        templates = [t for t in templates if t["category"].lower() == category.lower()]
    return templates


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str, db: AsyncSession = Depends(get_db)):
    if template_id in BUILTIN_MAP:
        return {**BUILTIN_MAP[template_id], "created_at": None}
    result = await db.execute(
        text("SELECT * FROM video_templates WHERE id = :id"), {"id": template_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")
    return {**dict(row._mapping), "is_builtin": False}


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(
    body: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tpl_id = f"tpl_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    try:
        await db.execute(
            text("""
                INSERT INTO video_templates
                    (id, name, category, description, default_emotion, default_background,
                     default_language, script_template, thumbnail_emoji, user_id, created_at)
                VALUES
                    (:id,:name,:category,:description,:default_emotion,:default_background,
                     :default_language,:script_template,:thumbnail_emoji,:user_id,:created_at)
            """),
            {
                "id": tpl_id, "name": body.name, "category": body.category,
                "description": body.description, "default_emotion": body.default_emotion,
                "default_background": body.default_background,
                "default_language": body.default_language,
                "script_template": body.script_template,
                "thumbnail_emoji": body.thumbnail_emoji,
                "user_id": str(current_user.id),
                "created_at": now,
            },
        )
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create template: {e}")
    return {**body.dict(), "id": tpl_id, "is_builtin": False, "created_at": now}


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if template_id in BUILTIN_MAP:
        raise HTTPException(status_code=403, detail="Cannot delete built-in templates")
    await db.execute(
        text("DELETE FROM video_templates WHERE id = :id AND user_id = :uid"),
        {"id": template_id, "uid": str(current_user.id)},
    )
    await db.commit()
