"""Ominou Studio Engine — Filmmaker-grade video generation with camera control."""
import asyncio
import os
import uuid

import aiofiles
import httpx

from .base import VideoProvider, ProviderResult

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "storage", "videos")
RUNWAY_API_BASE = "https://api.dev.runwayml.com/v1"


class RunwayProvider(VideoProvider):
    display_name = "Ominou Studio"
    company = "Ominou Studio"
    strengths = ["camera control", "editing workflow", "filmmaker tools", "motion control"]
    max_duration = 16
    supports_audio = False
    env_key = "RUNWAY_API_KEY"

    async def generate(
        self,
        prompt: str,
        duration_seconds: int = 5,
        resolution: str = "1080p",
        style: str = "cinematic",
        max_retries: int = 3,
        **kwargs,
    ) -> ProviderResult:
        api_key = os.getenv("RUNWAY_API_KEY")
        if not api_key:
            return ProviderResult(status="failed", error="RUNWAY_API_KEY not set", provider="runway")

        os.makedirs(STORAGE_DIR, exist_ok=True)

        quality = kwargs.get("quality", "high")
        if quality == "ultra":
            enhanced = (
                f"Ultra-realistic {style} shot, indistinguishable from real cinema camera footage, "
                f"full-frame 35mm lens, shallow depth of field, natural focus breathing, "
                f"photorealistic skin texture, micro-expressions, practical lighting, "
                f"subtle handheld stabilization, slight sensor grain, motion blur: {prompt}"
            )
        else:
            enhanced = f"Professional {style} shot: {prompt}"
        dur = min(duration_seconds, self.max_duration)
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=180) as client:
                    resp = await client.post(
                        f"{RUNWAY_API_BASE}/text_to_video",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "X-Runway-Version": "2024-11-06",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "gen4",
                            "promptText": enhanced,
                            "duration": dur,
                            "ratio": "1280:768",
                        },
                    )

                    if resp.status_code not in (200, 201):
                        last_error = f"Runway API error {resp.status_code}: {resp.text[:200]}"
                        continue

                    task_id = resp.json().get("id")
                    if not task_id:
                        last_error = "No task id from Runway"
                        continue

                    # Poll for result
                    for _ in range(90):
                        await asyncio.sleep(4)
                        poll = await client.get(
                            f"{RUNWAY_API_BASE}/tasks/{task_id}",
                            headers={"Authorization": f"Bearer {api_key}", "X-Runway-Version": "2024-11-06"},
                        )
                        if poll.status_code != 200:
                            continue
                        result = poll.json()
                        status = result.get("status")

                        if status == "SUCCEEDED":
                            output = result.get("output", [])
                            if output:
                                video_url = output[0] if isinstance(output, list) else output
                                dl = await client.get(video_url)
                                if dl.status_code == 200:
                                    file_id = str(uuid.uuid4())[:12]
                                    filename = f"runway_{file_id}.mp4"
                                    filepath = os.path.join(STORAGE_DIR, filename)
                                    async with aiofiles.open(filepath, "wb") as f:
                                        await f.write(dl.content)
                                    return ProviderResult(
                                        status="completed",
                                        scene_file=filepath,
                                        file_url=f"/storage/videos/{filename}",
                                        duration_seconds=duration_seconds,
                                        resolution=resolution,
                                        provider="runway",
                                        attempt=attempt,
                                    )
                            break
                        elif status == "FAILED":
                            last_error = result.get("failure", "Runway generation failed")
                            break

            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    await asyncio.sleep(3 * attempt)

        return ProviderResult(
            status="failed",
            error=f"Runway failed after {max_retries} attempts: {last_error}",
            provider="runway",
        )
