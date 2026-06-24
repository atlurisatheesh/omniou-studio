"""Lip Sync Engine — Aligns character lip movements with narration audio.

Supports: Sync Labs, HeyGen, SadTalker APIs.
This is a critical step for dialogue-driven videos where characters speak.
"""
import asyncio
import os
import uuid

import aiofiles
import httpx

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "videos")


async def _ensure_storage():
    os.makedirs(STORAGE_DIR, exist_ok=True)


async def lip_sync_video(
    video_file: str,
    audio_file: str,
    provider: str = "auto",
) -> dict:
    """Synchronize lip movements in video with audio narration.

    Providers:
    - sync_labs: Sync Labs API (highest quality)
    - heygen: HeyGen API (simple, good for avatars)
    - auto: tries sync_labs first, then heygen
    """
    await _ensure_storage()

    if provider == "auto":
        for p in ["sync_labs", "heygen"]:
            result = await _try_provider(p, video_file, audio_file)
            if result.get("status") == "completed":
                return result
        return {"status": "failed", "error": "No lip sync provider available. Set SYNCLABS_API_KEY or HEYGEN_API_KEY."}

    return await _try_provider(provider, video_file, audio_file)


async def _try_provider(provider: str, video_file: str, audio_file: str) -> dict:
    if provider == "sync_labs":
        return await _sync_labs(video_file, audio_file)
    elif provider == "heygen":
        return await _heygen(video_file, audio_file)
    return {"status": "failed", "error": f"Unknown lip sync provider: {provider}"}


async def _sync_labs(video_file: str, audio_file: str) -> dict:
    """Sync Labs — highest quality lip sync."""
    api_key = os.getenv("SYNCLABS_API_KEY")
    if not api_key:
        return {"status": "unavailable", "error": "SYNCLABS_API_KEY not set"}

    file_id = str(uuid.uuid4())[:12]

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            # Upload video
            with open(video_file, "rb") as vf:
                video_bytes = vf.read()
            with open(audio_file, "rb") as af:
                audio_bytes = af.read()

            resp = await client.post(
                "https://api.synclabs.so/v2/generate",
                headers={"x-api-key": api_key},
                files={
                    "video": ("video.mp4", video_bytes, "video/mp4"),
                    "audio": ("audio.mp3", audio_bytes, "audio/mpeg"),
                },
                data={"model": "sync-2.0", "synergize": "true"},
            )

            if resp.status_code not in (200, 201):
                return {"status": "failed", "error": f"Sync Labs error: {resp.status_code}"}

            data = resp.json()
            job_id = data.get("id")
            if not job_id:
                return {"status": "failed", "error": "No job ID from Sync Labs"}

            # Poll for completion
            for _ in range(120):
                await asyncio.sleep(5)
                poll = await client.get(
                    f"https://api.synclabs.so/v2/generate/{job_id}",
                    headers={"x-api-key": api_key},
                )
                if poll.status_code != 200:
                    continue
                result = poll.json()

                if result.get("status") == "COMPLETED":
                    video_url = result.get("videoUrl")
                    if video_url:
                        dl = await client.get(video_url)
                        if dl.status_code == 200:
                            filename = f"lipsync_{file_id}.mp4"
                            filepath = os.path.join(STORAGE_DIR, filename)
                            async with aiofiles.open(filepath, "wb") as f:
                                await f.write(dl.content)
                            return {
                                "status": "completed",
                                "synced_file": filepath,
                                "file_url": f"/storage/videos/{filename}",
                                "provider": "sync_labs",
                            }
                    break
                elif result.get("status") == "FAILED":
                    return {"status": "failed", "error": "Sync Labs processing failed"}

    except Exception as e:
        return {"status": "failed", "error": f"Sync Labs error: {e}"}

    return {"status": "failed", "error": "Sync Labs processing timed out"}


async def _heygen(video_file: str, audio_file: str) -> dict:
    """HeyGen — good for avatar-based lip sync."""
    api_key = os.getenv("HEYGEN_API_KEY")
    if not api_key:
        return {"status": "unavailable", "error": "HEYGEN_API_KEY not set"}

    file_id = str(uuid.uuid4())[:12]

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            with open(video_file, "rb") as vf:
                video_bytes = vf.read()
            with open(audio_file, "rb") as af:
                audio_bytes = af.read()

            # Upload video asset
            upload_resp = await client.post(
                "https://api.heygen.com/v2/video_translate",
                headers={"X-Api-Key": api_key},
                files={
                    "video": ("video.mp4", video_bytes, "video/mp4"),
                    "audio": ("audio.mp3", audio_bytes, "audio/mpeg"),
                },
            )

            if upload_resp.status_code not in (200, 201):
                return {"status": "failed", "error": f"HeyGen error: {upload_resp.status_code}"}

            data = upload_resp.json().get("data", {})
            task_id = data.get("video_translate_id")
            if not task_id:
                return {"status": "failed", "error": "No task ID from HeyGen"}

            # Poll
            for _ in range(120):
                await asyncio.sleep(5)
                poll = await client.get(
                    f"https://api.heygen.com/v1/video_translate.get?video_translate_id={task_id}",
                    headers={"X-Api-Key": api_key},
                )
                if poll.status_code != 200:
                    continue
                result = poll.json().get("data", {})

                if result.get("status") == "completed":
                    video_url = result.get("url")
                    if video_url:
                        dl = await client.get(video_url)
                        if dl.status_code == 200:
                            filename = f"lipsync_{file_id}.mp4"
                            filepath = os.path.join(STORAGE_DIR, filename)
                            async with aiofiles.open(filepath, "wb") as f:
                                await f.write(dl.content)
                            return {
                                "status": "completed",
                                "synced_file": filepath,
                                "file_url": f"/storage/videos/{filename}",
                                "provider": "heygen",
                            }
                    break
                elif result.get("status") == "failed":
                    return {"status": "failed", "error": "HeyGen processing failed"}

    except Exception as e:
        return {"status": "failed", "error": f"HeyGen error: {e}"}

    return {"status": "failed", "error": "HeyGen processing timed out"}


async def batch_lip_sync(
    scene_videos: list[str],
    narration_files: list[str],
    provider: str = "auto",
) -> list[dict]:
    """Lip sync all scenes with their narration in parallel."""
    tasks = []
    for video, audio in zip(scene_videos, narration_files):
        if video and audio and os.path.exists(video) and os.path.exists(audio):
            tasks.append(lip_sync_video(video, audio, provider))
        else:
            tasks.append(asyncio.coroutine(lambda: {"status": "skipped"})())

    return list(await asyncio.gather(*tasks, return_exceptions=True))
