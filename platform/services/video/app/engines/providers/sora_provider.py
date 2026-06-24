"""Ominou Prime Engine — Advanced physics & storytelling video generation."""
import asyncio
import os
import uuid

import aiofiles
from openai import AsyncOpenAI

from .base import VideoProvider, ProviderResult

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "storage", "videos")


class SoraProvider(VideoProvider):
    display_name = "Ominou Prime"
    company = "Ominou Studio"
    strengths = ["storytelling", "physics simulation", "cinematic scenes", "consistent characters"]
    max_duration = 20
    supports_audio = False
    env_key = "OPENAI_API_KEY"

    async def generate(
        self,
        prompt: str,
        duration_seconds: int = 5,
        resolution: str = "1080p",
        style: str = "cinematic",
        max_retries: int = 3,
        **kwargs,
    ) -> ProviderResult:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return ProviderResult(status="failed", error="OPENAI_API_KEY not set", provider="sora")

        os.makedirs(STORAGE_DIR, exist_ok=True)
        client = AsyncOpenAI(api_key=api_key)

        # Sora supports 480p, 720p, 1080p natively
        res_map = {"720p": "720p", "1080p": "1080p", "1440p": "1080p", "4K": "1080p"}
        target_res = res_map.get(resolution, "1080p")
        quality = kwargs.get("quality", "high")
        if quality == "ultra":
            enhanced = (
                f"Ultra-high fidelity {style} footage, shot on ARRI Alexa 65 with Cooke S7/i 35mm lens, "
                f"shallow depth of field, natural focus breathing, subtle handheld stabilization, "
                f"realistic motion blur, practical lighting with soft shadows, "
                f"human subjects with realistic micro-expressions, natural blinking, subtle breathing, "
                f"natural eye focus changes, realistic skin texture and pores, "
                f"slight sensor grain, lens vignette, depth of field falloff. "
                f"{prompt}"
            )
        else:
            enhanced = (
                f"Ultra-realistic {style} footage, shot on ARRI Alexa Mini LF, "
                f"cinematic color grading, professional lighting. {prompt}"
            )
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                response = await client.responses.create(
                    model="sora",
                    input=enhanced,
                    tools=[{
                        "type": "video_generation",
                        "resolution": target_res,
                        "duration": min(duration_seconds, self.max_duration),
                        "n_videos": 1,
                    }],
                )

                video_output = None
                for output in response.output:
                    if hasattr(output, "type") and output.type == "video_generation_call":
                        video_output = output
                        break

                if video_output is None:
                    last_error = "No video output in Sora response"
                    continue

                video_bytes = await client.files.content(video_output.video_file_id)
                file_id = str(uuid.uuid4())[:12]
                filename = f"sora_{file_id}.mp4"
                filepath = os.path.join(STORAGE_DIR, filename)

                async with aiofiles.open(filepath, "wb") as f:
                    await f.write(video_bytes.content)

                return ProviderResult(
                    status="completed",
                    scene_file=filepath,
                    file_url=f"/storage/videos/{filename}",
                    duration_seconds=duration_seconds,
                    resolution=target_res,
                    provider="sora",
                    attempt=attempt,
                )

            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    await asyncio.sleep(2 * attempt)

        return ProviderResult(
            status="failed",
            error=f"Sora failed after {max_retries} attempts: {last_error}",
            provider="sora",
        )
