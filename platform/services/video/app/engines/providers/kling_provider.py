"""Ominou Flow Engine — Extremely realistic motion & physics."""
import asyncio
import os
import uuid

import aiofiles
import httpx

from .base import VideoProvider, ProviderResult

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "storage", "videos")
KLING_API_BASE = "https://api.klingai.com/v1"


class KlingProvider(VideoProvider):
    display_name = "Ominou Flow"
    company = "Ominou Studio"
    strengths = ["motion realism", "natural physics", "character animation", "realistic people"]
    max_duration = 10
    supports_audio = False
    env_key = "KLING_API_KEY"

    async def generate(
        self,
        prompt: str,
        duration_seconds: int = 5,
        resolution: str = "1080p",
        style: str = "cinematic",
        max_retries: int = 3,
        **kwargs,
    ) -> ProviderResult:
        api_key = os.getenv("KLING_API_KEY")
        if not api_key:
            return ProviderResult(status="failed", error="KLING_API_KEY not set", provider="kling")

        os.makedirs(STORAGE_DIR, exist_ok=True)

        quality = kwargs.get("quality", "high")
        if quality == "ultra":
            enhanced = (
                f"Ultra-realistic {style} footage, photorealistic human actors with natural micro-expressions, "
                f"realistic blinking, breathing, skin texture, practical lighting, "
                f"full-frame cinema camera with 35mm lens, shallow depth of field, "
                f"subtle handheld stabilization, natural motion blur, slight film grain: {prompt}"
            )
            mode = "high_quality"
        elif quality == "high" or resolution in ("1440p", "4K"):
            enhanced = f"{style} style, ultra-realistic: {prompt}"
            mode = "high_quality"
        else:
            enhanced = f"{style} style: {prompt}"
            mode = "standard"
        dur = "10" if duration_seconds > 5 else "5"
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    # Submit generation task
                    resp = await client.post(
                        f"{KLING_API_BASE}/videos/text2video",
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={
                            "prompt": enhanced,
                            "model_name": "kling-v2",
                            "mode": mode,
                            "duration": dur,
                            "aspect_ratio": "16:9",
                        },
                    )
                    if resp.status_code != 200:
                        last_error = f"Kling API error {resp.status_code}: {resp.text[:200]}"
                        continue

                    task_data = resp.json().get("data", {})
                    task_id = task_data.get("task_id")
                    if not task_id:
                        last_error = "No task_id returned from Kling"
                        continue

                    # Poll for completion
                    for _ in range(60):
                        await asyncio.sleep(5)
                        status_resp = await client.get(
                            f"{KLING_API_BASE}/videos/text2video/{task_id}",
                            headers={"Authorization": f"Bearer {api_key}"},
                        )
                        if status_resp.status_code != 200:
                            continue
                        status_data = status_resp.json().get("data", {})
                        task_status = status_data.get("task_status")

                        if task_status == "succeed":
                            videos = status_data.get("task_result", {}).get("videos", [])
                            if videos:
                                video_url = videos[0].get("url")
                                dl_resp = await client.get(video_url)
                                if dl_resp.status_code == 200:
                                    file_id = str(uuid.uuid4())[:12]
                                    filename = f"kling_{file_id}.mp4"
                                    filepath = os.path.join(STORAGE_DIR, filename)
                                    async with aiofiles.open(filepath, "wb") as f:
                                        await f.write(dl_resp.content)
                                    return ProviderResult(
                                        status="completed",
                                        scene_file=filepath,
                                        file_url=f"/storage/videos/{filename}",
                                        duration_seconds=duration_seconds,
                                        resolution=resolution,
                                        provider="kling",
                                        attempt=attempt,
                                    )
                            break
                        elif task_status == "failed":
                            last_error = f"Kling task failed: {status_data.get('task_status_msg', '')}"
                            break

            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    await asyncio.sleep(3 * attempt)

        return ProviderResult(
            status="failed",
            error=f"Kling failed after {max_retries} attempts: {last_error}",
            provider="kling",
        )
