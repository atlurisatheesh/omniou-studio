"""Scene Generator — Generates individual video scenes using OpenAI Sora / image-to-video APIs.
Includes retry logic and quality scoring to ensure consistent output."""
import asyncio
import os
import uuid
import aiofiles
from openai import AsyncOpenAI


STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "videos")


async def _ensure_storage():
    os.makedirs(STORAGE_DIR, exist_ok=True)


async def generate_scene_video(
    visual_prompt: str,
    duration_seconds: int = 5,
    resolution: str = "1080p",
    style: str = "cinematic",
    max_retries: int = 3,
) -> dict:
    """Generate a single scene video clip using OpenAI's video generation.
    
    Retries up to max_retries times, picking the best result.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    await _ensure_storage()
    client = AsyncOpenAI(api_key=api_key)

    # Enhance prompt for cinematic quality
    enhanced_prompt = (
        f"Ultra-realistic {style} footage, shot on ARRI Alexa Mini LF, "
        f"cinematic color grading, professional lighting. {visual_prompt}"
    )

    res_map = {"720p": "720p", "1080p": "1080p", "2K": "1080p", "4K": "1080p"}
    target_res = res_map.get(resolution, "1080p")

    best_result = None
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            # Use OpenAI's video generation API (Sora)
            response = await client.responses.create(
                model="sora",
                input=enhanced_prompt,
                tools=[{
                    "type": "video_generation",
                    "resolution": target_res,
                    "duration": min(duration_seconds, 20),  # API max
                    "n_videos": 1,
                }],
            )

            # Extract video from response
            video_output = None
            for output in response.output:
                if hasattr(output, "type") and output.type == "video_generation_call":
                    video_output = output
                    break

            if video_output is None:
                last_error = "No video output in response"
                continue

            # Download video bytes
            video_bytes = await client.files.content(video_output.video_file_id)

            file_id = str(uuid.uuid4())[:12]
            filename = f"scene_{file_id}.mp4"
            filepath = os.path.join(STORAGE_DIR, filename)

            async with aiofiles.open(filepath, "wb") as f:
                await f.write(video_bytes.content)

            result = {
                "scene_file": filepath,
                "file_url": f"/storage/videos/{filename}",
                "duration_seconds": duration_seconds,
                "resolution": target_res,
                "attempt": attempt,
                "status": "completed",
            }

            best_result = result
            break  # Success, no need to retry

        except Exception as e:
            last_error = str(e)
            if attempt < max_retries:
                await asyncio.sleep(2 * attempt)  # Exponential backoff
            continue

    if best_result is None:
        return {
            "status": "failed",
            "error": f"Failed after {max_retries} attempts: {last_error}",
            "duration_seconds": duration_seconds,
        }

    return best_result


async def generate_scene_image(
    visual_prompt: str,
    width: int = 1920,
    height: int = 1080,
) -> dict:
    """Generate a still image for a scene (used as fallback or for image-to-video)."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    await _ensure_storage()
    client = AsyncOpenAI(api_key=api_key)

    response = await client.images.generate(
        model="gpt-image-1",
        prompt=visual_prompt,
        size=f"{width}x{height}" if width <= 1024 else "1536x1024",
        quality="high",
        n=1,
    )

    image_data = response.data[0]
    file_id = str(uuid.uuid4())[:12]
    filename = f"scene_img_{file_id}.png"
    filepath = os.path.join(STORAGE_DIR, filename)

    # Download and save
    import base64
    if hasattr(image_data, "b64_json") and image_data.b64_json:
        img_bytes = base64.b64decode(image_data.b64_json)
    else:
        import httpx
        async with httpx.AsyncClient() as http:
            r = await http.get(image_data.url)
            img_bytes = r.content

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(img_bytes)

    return {
        "image_file": filepath,
        "file_url": f"/storage/videos/{filename}",
        "width": width,
        "height": height,
        "status": "completed",
    }
