"""Ominou Vision Engine — Video generation with synchronized audio."""
import asyncio
import os
import uuid

import aiofiles
import httpx

from .base import VideoProvider, ProviderResult

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "storage", "videos")
VEO_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


class VeoProvider(VideoProvider):
    display_name = "Ominou Vision"
    company = "Ominou Studio"
    strengths = ["audio + video together", "sound effects", "dialogue generation", "music sync"]
    max_duration = 8
    supports_audio = True
    env_key = "GOOGLE_AI_API_KEY"

    async def generate(
        self,
        prompt: str,
        duration_seconds: int = 5,
        resolution: str = "1080p",
        style: str = "cinematic",
        max_retries: int = 3,
        **kwargs,
    ) -> ProviderResult:
        api_key = os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            return ProviderResult(status="failed", error="GOOGLE_AI_API_KEY not set", provider="veo")

        os.makedirs(STORAGE_DIR, exist_ok=True)

        quality = kwargs.get("quality", "high")
        if quality == "ultra":
            enhanced = (
                f"Ultra-realistic {style} footage with synchronized natural audio, "
                f"full-frame cinema camera, 35mm lens, shallow depth of field, "
                f"photorealistic human actors with micro-expressions, natural blinking and breathing, "
                f"practical lighting, room ambience, natural reverb, "
                f"subtle film grain and lens imperfections: {prompt}"
            )
        else:
            enhanced = f"{style} style: {prompt}"
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=180) as client:
                    resp = await client.post(
                        f"{VEO_API_BASE}/models/veo-3:generateVideo",
                        params={"key": api_key},
                        headers={"Content-Type": "application/json"},
                        json={
                            "instances": [{"prompt": enhanced}],
                            "parameters": {
                                "aspectRatio": "16:9",
                                "personGeneration": "allow_adult",
                                "duration": f"{min(duration_seconds, self.max_duration)}s",
                                "generateAudio": True,
                            },
                        },
                    )

                    if resp.status_code != 200:
                        last_error = f"Veo API error {resp.status_code}: {resp.text[:200]}"
                        continue

                    data = resp.json()
                    operation_name = data.get("name")
                    if not operation_name:
                        last_error = "No operation returned from Veo"
                        continue

                    # Poll for completion
                    for _ in range(90):
                        await asyncio.sleep(4)
                        poll = await client.get(
                            f"{VEO_API_BASE}/{operation_name}",
                            params={"key": api_key},
                        )
                        if poll.status_code != 200:
                            continue
                        result = poll.json()

                        if result.get("done"):
                            videos = (result.get("response", {})
                                      .get("generatedVideos", []))
                            if videos:
                                video_data = videos[0].get("video", {})
                                video_uri = video_data.get("uri")
                                if video_uri:
                                    dl = await client.get(video_uri)
                                    if dl.status_code == 200:
                                        file_id = str(uuid.uuid4())[:12]
                                        filename = f"veo_{file_id}.mp4"
                                        filepath = os.path.join(STORAGE_DIR, filename)
                                        async with aiofiles.open(filepath, "wb") as f:
                                            await f.write(dl.content)
                                        return ProviderResult(
                                            status="completed",
                                            scene_file=filepath,
                                            file_url=f"/storage/videos/{filename}",
                                            duration_seconds=duration_seconds,
                                            resolution=resolution,
                                            has_audio=True,
                                            provider="veo",
                                            attempt=attempt,
                                        )
                            break

                        if result.get("error"):
                            last_error = result["error"].get("message", "Veo generation failed")
                            break

            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    await asyncio.sleep(3 * attempt)

        return ProviderResult(
            status="failed",
            error=f"Veo failed after {max_retries} attempts: {last_error}",
            provider="veo",
        )

    async def generate_with_audio(
        self,
        prompt: str,
        duration_seconds: int = 5,
        resolution: str = "1080p",
        **kwargs,
    ) -> ProviderResult:
        """Veo 3 natively generates video WITH audio — dialogue, SFX, music."""
        return await self.generate(
            prompt, duration_seconds, resolution,
            style=kwargs.get("style", "cinematic"),
        )
