"""Auto-Publishing Engine — Automated distribution to social media platforms.

Publishes generated videos to YouTube, Instagram, TikTok, and more.
Supports Zapier/Make.com webhooks or direct API integration.
"""
import os
import uuid
from datetime import datetime, timezone

import httpx


PLATFORMS = {
    "youtube": {
        "name": "YouTube",
        "formats": ["Shorts", "Standard", "Long-form"],
        "max_duration": 43200,  # 12 hours
        "aspect_ratios": ["16:9", "9:16"],
    },
    "instagram": {
        "name": "Instagram Reels",
        "formats": ["Reels", "Stories", "Feed"],
        "max_duration": 90,
        "aspect_ratios": ["9:16", "1:1", "4:5"],
    },
    "tiktok": {
        "name": "TikTok",
        "formats": ["Standard", "Duet", "Stitch"],
        "max_duration": 600,
        "aspect_ratios": ["9:16"],
    },
    "x": {
        "name": "X (Twitter)",
        "formats": ["Standard"],
        "max_duration": 140,
        "aspect_ratios": ["16:9", "1:1"],
    },
    "linkedin": {
        "name": "LinkedIn",
        "formats": ["Standard"],
        "max_duration": 600,
        "aspect_ratios": ["16:9", "1:1"],
    },
}


async def publish_video(
    video_file: str,
    platform: str,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    schedule_time: str | None = None,
    webhook_url: str | None = None,
) -> dict:
    """Publish a video to a social media platform.

    Methods (in priority order):
    1. Direct platform API (if platform API key available)
    2. Zapier/Make.com webhook (if webhook_url provided)
    3. Returns download link for manual upload
    """
    if platform not in PLATFORMS:
        return {"status": "failed", "error": f"Unknown platform: {platform}", "available": list(PLATFORMS.keys())}

    publish_id = str(uuid.uuid4())[:8]
    platform_info = PLATFORMS[platform]

    # Try direct API
    direct_result = await _try_direct_api(platform, video_file, title, description, tags, schedule_time)
    if direct_result and direct_result.get("status") == "published":
        return {**direct_result, "publish_id": publish_id}

    # Try webhook
    if webhook_url:
        webhook_result = await _send_webhook(webhook_url, platform, video_file, title, description, tags, schedule_time)
        if webhook_result.get("status") == "sent":
            return {
                "publish_id": publish_id,
                "platform": platform,
                "platform_name": platform_info["name"],
                "method": "webhook",
                "title": title,
                "status": "queued",
                "message": f"Sent to automation webhook for {platform_info['name']}",
                "scheduled": schedule_time,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

    # Fallback: manual
    return {
        "publish_id": publish_id,
        "platform": platform,
        "platform_name": platform_info["name"],
        "method": "manual",
        "title": title,
        "video_file": video_file,
        "status": "ready_for_download",
        "message": f"Video ready for manual upload to {platform_info['name']}. Configure {platform.upper()}_API_KEY or provide webhook_url for auto-publishing.",
        "suggested_tags": tags or [],
        "formats": platform_info["formats"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


async def _try_direct_api(
    platform: str,
    video_file: str,
    title: str,
    description: str,
    tags: list[str] | None,
    schedule_time: str | None,
) -> dict | None:
    """Try direct platform API upload."""
    if platform == "youtube":
        return await _youtube_upload(video_file, title, description, tags, schedule_time)
    elif platform == "tiktok":
        return await _tiktok_upload(video_file, title, tags)
    return None


async def _youtube_upload(
    video_file: str, title: str, description: str,
    tags: list[str] | None, schedule_time: str | None,
) -> dict | None:
    """Upload to YouTube via YouTube Data API v3."""
    api_key = os.getenv("YOUTUBE_API_KEY")
    oauth_token = os.getenv("YOUTUBE_OAUTH_TOKEN")
    if not oauth_token:
        return None

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            with open(video_file, "rb") as f:
                video_bytes = f.read()

            metadata = {
                "snippet": {
                    "title": title,
                    "description": description or "",
                    "tags": tags or [],
                    "categoryId": "22",
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False,
                },
            }

            if schedule_time:
                metadata["status"]["privacyStatus"] = "private"
                metadata["status"]["publishAt"] = schedule_time

            resp = await client.post(
                "https://www.googleapis.com/upload/youtube/v3/videos",
                params={"uploadType": "multipart", "part": "snippet,status"},
                headers={"Authorization": f"Bearer {oauth_token}"},
                files={
                    "metadata": ("metadata.json", str(metadata).encode(), "application/json"),
                    "video": ("video.mp4", video_bytes, "video/mp4"),
                },
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    "status": "published",
                    "platform": "youtube",
                    "video_id": data.get("id"),
                    "url": f"https://youtube.com/watch?v={data.get('id')}",
                    "method": "direct_api",
                }
    except Exception:
        pass
    return None


async def _tiktok_upload(
    video_file: str, title: str, tags: list[str] | None,
) -> dict | None:
    """Upload to TikTok via TikTok Content Posting API."""
    access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
    if not access_token:
        return None

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            with open(video_file, "rb") as f:
                video_bytes = f.read()

            # Init upload
            init_resp = await client.post(
                "https://open.tiktokapis.com/v2/post/publish/video/init/",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json={
                    "post_info": {
                        "title": title[:150],
                        "privacy_level": "PUBLIC_TO_EVERYONE",
                    },
                    "source_info": {
                        "source": "FILE_UPLOAD",
                        "video_size": len(video_bytes),
                    },
                },
            )

            if init_resp.status_code in (200, 201):
                data = init_resp.json().get("data", {})
                upload_url = data.get("upload_url")
                if upload_url:
                    upload_resp = await client.put(
                        upload_url,
                        content=video_bytes,
                        headers={"Content-Type": "video/mp4"},
                    )
                    if upload_resp.status_code in (200, 201):
                        return {
                            "status": "published",
                            "platform": "tiktok",
                            "publish_id": data.get("publish_id"),
                            "method": "direct_api",
                        }
    except Exception:
        pass
    return None


async def _send_webhook(
    webhook_url: str,
    platform: str,
    video_file: str,
    title: str,
    description: str,
    tags: list[str] | None,
    schedule_time: str | None,
) -> dict:
    """Send video info to Zapier/Make.com webhook for automated publishing."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                webhook_url,
                json={
                    "platform": platform,
                    "title": title,
                    "description": description or "",
                    "tags": tags or [],
                    "video_file": video_file,
                    "schedule_time": schedule_time,
                    "source": "ominou_studio",
                },
            )
            if resp.status_code in (200, 201):
                return {"status": "sent"}
    except Exception:
        pass
    return {"status": "failed"}


async def batch_publish(
    video_file: str,
    platforms: list[str],
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    webhook_url: str | None = None,
) -> list[dict]:
    """Publish to multiple platforms at once."""
    results = []
    for platform in platforms:
        result = await publish_video(video_file, platform, title, description, tags, webhook_url=webhook_url)
        results.append(result)
    return results


def list_platforms() -> list[dict]:
    """Return all supported publishing platforms."""
    return [{"id": pid, **pdata} for pid, pdata in PLATFORMS.items()]
