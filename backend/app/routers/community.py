"""
AGRISENSE — Community Router
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import CommunityPost, CommunityReply, User, get_db

router = APIRouter(prefix="/community", tags=["Community"])

UPLOAD_DIR = Path("uploads/community")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/posts")
async def list_posts(
    category: str | None = None,
    crop: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List community posts with optional filters."""
    stmt = select(CommunityPost).order_by(CommunityPost.created_at.desc())

    if category:
        stmt = stmt.where(CommunityPost.category == category)
    if crop:
        stmt = stmt.where(CommunityPost.crop == crop)

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    posts = result.scalars().all()

    return {
        "posts": [
            {
                "id": str(p.id),
                "user_name": "Farmer",  # In production: join with users
                "title": p.title,
                "body": p.body,
                "image_path": p.image_path,
                "category": p.category,
                "crop": p.crop,
                "region": p.region,
                "upvotes": p.upvotes,
                "replies_count": p.replies_count,
                "is_answered": p.is_answered,
                "created_at": p.created_at,
            }
            for p in posts
        ]
    }


@router.post("/posts")
async def create_post(
    title: str = Form(...),
    body: str = Form(default=""),
    category: str = Form(default="general"),
    crop: str = Form(default=None),
    region: str = Form(default=None),
    image: UploadFile = File(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Create a community post."""
    image_path = None
    if image and image.content_type in ("image/jpeg", "image/png", "image/webp"):
        ext = image.filename.split(".")[-1] if image.filename else "jpg"
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = UPLOAD_DIR / filename
        content = await image.read()
        if len(content) <= 10 * 1024 * 1024:
            with open(filepath, "wb") as f:
                f.write(content)
            image_path = str(filepath)

    post = CommunityPost(
        title=title,
        body=body,
        category=category,
        crop=crop,
        region=region,
        image_path=image_path,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    return {"id": str(post.id), "message": "Post created successfully"}


@router.get("/posts/{post_id}")
async def get_post(post_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single post with replies."""
    result = await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Get replies
    replies_result = await db.execute(
        select(CommunityReply)
        .where(CommunityReply.post_id == post_id)
        .order_by(CommunityReply.created_at)
    )
    replies = replies_result.scalars().all()

    return {
        "post": {
            "id": str(post.id),
            "title": post.title,
            "body": post.body,
            "image_path": post.image_path,
            "category": post.category,
            "crop": post.crop,
            "upvotes": post.upvotes,
            "is_answered": post.is_answered,
            "created_at": post.created_at,
        },
        "replies": [
            {
                "id": str(r.id),
                "user_name": "Expert" if r.is_expert else "Farmer",
                "body": r.body,
                "is_expert": r.is_expert,
                "upvotes": r.upvotes,
                "created_at": r.created_at,
            }
            for r in replies
        ],
    }


@router.post("/posts/{post_id}/reply")
async def reply_to_post(
    post_id: str,
    body: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Reply to a community post."""
    result = await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    reply = CommunityReply(
        post_id=post_id,
        body=body,
    )
    db.add(reply)
    post.replies_count += 1
    await db.commit()

    return {"message": "Reply posted"}


@router.post("/posts/{post_id}/upvote")
async def upvote_post(post_id: str, db: AsyncSession = Depends(get_db)):
    """Upvote a post."""
    result = await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.upvotes += 1
    await db.commit()
    return {"upvotes": post.upvotes}
