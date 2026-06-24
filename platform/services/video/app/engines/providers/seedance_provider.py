"""Ominou Motion Engine — Ultra-cinematic, Hollywood-quality video generation."""
import asyncio
import os
import uuid

import aiofiles
import httpx

from .base import VideoProvider, ProviderResult

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "storage", "videos")
SEEDANCE_API_BASE = "https://api.seedance.ai/v1"


class SeedanceProvider(VideoProvider):
    display_name = "Ominou Motion"
    company = "Ominou Studio"
    strengths = ["cinematic realism", "multi-modal generation", "Hollywood quality", "scene composition"]
    max_duration = 16
    supports_audio = False
    env_key = "SEEDANCE_API_KEY"

    async def generate(
        self,
        prompt: str,
        duration_seconds: int = 5,
        resolution: str = "1080p",
        style: str = "cinematic",
        max_retries: int = 3,
        **kwargs,
    ) -> ProviderResult:
        api_key = os.getenv("SEEDANCE_API_KEY")
        if not api_key:
            return ProviderResult(status="failed", error="SEEDANCE_API_KEY not set", provider="seedance")

        os.makedirs(STORAGE_DIR, exist_ok=True)

        quality = kwargs.get("quality", "high")
        if quality == "ultra":
            enhanced = (
                f"Ultra-realistic {style} shot, indistinguishable from real camera footage, "
                f"full-frame cinema camera, 35mm lens, shallow DOF, natural micro-expressions, "
                f"realistic skin texture and lighting, practical household lights, "
                f"subtle film grain, lens breathing, natural motion blur: {prompt}"
            )
        else:
            enhanced = f"Cinematic {style} shot, Hollywood production quality: {prompt}"
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=180) as client:
                    resp = await client.post(
                        f"{SEEDANCE_API_BASE}/generate",
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={
                            "prompt": enhanced,
                            "model": "seedance-2.0",
                            "duration": min(duration_seconds, self.max_duration),
                            "resolution": resolution,
                            "style": style,
                            "aspect_ratio": "16:9",
                        },
                    )

                    if resp.status_code != 200:
                        last_error = f"Seedance API error {resp.status_code}: {resp.text[:200]}"
                        continue

                    data = resp.json()
                    task_id = data.get("task_id")
                    if not task_id:
                        last_error = "No task_id from Seedance"
                        continue

                    # Poll for result
                    for _ in range(90):
                        await asyncio.sleep(4)
                        poll = await client.get(
                            f"{SEEDANCE_API_BASE}/tasks/{task_id}",
                            headers={"Authorization": f"Bearer {api_key}"},
                        )
                        if poll.status_code != 200:
                            continue
                        result = poll.json()

                        if result.get("status") == "completed":
                            video_url = result.get("video_url")
                            if video_url:
                                dl = await client.get(video_url)
                                if dl.status_code == 200:
                                    file_id = str(uuid.uuid4())[:12]
                                    filename = f"seedance_{file_id}.mp4"
                                    filepath = os.path.join(STORAGE_DIR, filename)
                                    async with aiofiles.open(filepath, "wb") as f:
                                        await f.write(dl.content)
                                    return ProviderResult(
                                        status="completed",
                                        scene_file=filepath,
                                        file_url=f"/storage/videos/{filename}",
                                        duration_seconds=duration_seconds,
                                        resolution=resolution,
                                        provider="seedance",
                                        attempt=attempt,
                                    )
                            break
                        elif result.get("status") == "failed":
                            last_error = result.get("error", "Seedance generation failed")
                            break

            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    await asyncio.sleep(3 * attempt)

        return ProviderResult(
            status="failed",
            error=f"Seedance failed after {max_retries} attempts: {last_error}",
            provider="seedance",
        )
