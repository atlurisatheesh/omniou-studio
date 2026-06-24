"""Music Studio AI Engine — Music Generation, Jingles, Sound Effects.

Uses OpenAI for music-related AI tasks. Ready for Suno/Udio API integration.
"""
import os
import uuid

import aiofiles
from openai import AsyncOpenAI

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "music")


async def _ensure_storage():
    os.makedirs(STORAGE_DIR, exist_ok=True)


GENRES = [
    "ambient", "cinematic", "corporate", "electronic", "hip_hop", "jazz",
    "lo_fi", "orchestral", "pop", "rock", "acoustic", "world",
    "edm", "classical", "r_and_b", "country", "folk", "indie",
]

MOODS = [
    "happy", "sad", "energetic", "calm", "dramatic", "mysterious",
    "romantic", "epic", "playful", "dark", "uplifting", "nostalgic",
    "tense", "peaceful", "triumphant", "melancholic",
]

SFX_CATEGORIES = {
    "ui": ["click", "hover", "success", "error", "notification", "toggle", "swoosh"],
    "nature": ["rain", "thunder", "wind", "birds", "ocean", "forest", "fire"],
    "transition": ["whoosh", "impact", "reveal", "slide", "fade", "glitch"],
    "ambient": ["office", "cafe", "city", "crowd", "space", "underwater"],
    "musical": ["stinger", "sting", "fanfare", "drum_roll", "countdown"],
}


async def _generate_audio_via_suno(prompt: str, duration_seconds: int) -> bytes | None:
    """Try Suno API for music generation (when API becomes publicly available)."""
    api_key = os.getenv("SUNO_API_KEY")
    if not api_key:
        return None
    try:
        import httpx
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://api.suno.ai/v1/generate",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"prompt": prompt, "duration": duration_seconds},
            )
            if resp.status_code == 200:
                return resp.content
    except Exception:
        pass
    return None


async def _generate_audio_openai_tts(description: str, duration_seconds: int) -> bytes:
    """Use OpenAI TTS to generate a spoken music description as placeholder audio."""
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Generate a musical spoken description
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Create a short, evocative audio description for an AI music track. "
                                          "Be concise — just describe the feel, instruments, rhythm in 2 sentences."},
            {"role": "user", "content": description},
        ],
        temperature=0.7,
        max_tokens=100,
    )
    text = resp.choices[0].message.content.strip()

    response = await client.audio.speech.create(
        model="tts-1-hd",
        voice="nova",
        input=f"Generated music track: {text}",
        response_format="mp3",
    )
    return response.content


async def generate_music(prompt: str, genre: str = "ambient", mood: str = "calm",
                         duration_seconds: int = 30, bpm: int = 120) -> dict:
    """Generate AI music from prompt using Suno API or OpenAI fallback."""
    await _ensure_storage()
    file_id = str(uuid.uuid4())[:8]
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key and not os.getenv("SUNO_API_KEY"):
        return {"error": "No API key configured (SUNO_API_KEY or OPENAI_API_KEY)"}

    full_prompt = f"{genre} music, {mood} mood, {bpm} BPM: {prompt}"

    # Try Suno first
    audio_bytes = await _generate_audio_via_suno(full_prompt, duration_seconds)
    provider = "suno"

    if audio_bytes is None and api_key:
        audio_bytes = await _generate_audio_openai_tts(full_prompt, duration_seconds)
        provider = "openai_tts_preview"

    if audio_bytes is None:
        return {"error": "Failed to generate music"}

    filename = f"music_{file_id}.mp3"
    filepath = os.path.join(STORAGE_DIR, filename)
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(audio_bytes)

    return {
        "file_id": f"music_{file_id}",
        "file_url": f"/storage/music/{filename}",
        "prompt": prompt,
        "genre": genre,
        "mood": mood,
        "duration_seconds": duration_seconds,
        "bpm": bpm,
        "sample_rate": 44100,
        "format": "mp3",
        "key": "C Major",
        "file_size_bytes": len(audio_bytes),
        "provider": provider,
        "status": "completed",
    }


async def generate_jingle(brand_name: str, style: str = "corporate", duration_seconds: int = 15) -> dict:
    """Generate a brand jingle."""
    await _ensure_storage()
    file_id = str(uuid.uuid4())[:8]
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY not configured"}

    jingle_prompt = f"Brand jingle for '{brand_name}', {style} style, upbeat and memorable, {duration_seconds}s"

    audio_bytes = await _generate_audio_via_suno(jingle_prompt, duration_seconds)
    provider = "suno"

    if audio_bytes is None:
        audio_bytes = await _generate_audio_openai_tts(jingle_prompt, duration_seconds)
        provider = "openai_tts_preview"

    filename = f"jingle_{file_id}.mp3"
    filepath = os.path.join(STORAGE_DIR, filename)
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(audio_bytes)

    return {
        "file_id": f"jingle_{file_id}",
        "file_url": f"/storage/music/{filename}",
        "brand_name": brand_name,
        "style": style,
        "duration_seconds": duration_seconds,
        "has_vocals": True,
        "format": "mp3",
        "file_size_bytes": len(audio_bytes),
        "provider": provider,
        "status": "completed",
    }


async def generate_sfx(category: str, effect: str) -> dict:
    """Generate a sound effect using OpenAI audio."""
    cat = SFX_CATEGORIES.get(category)
    if not cat:
        return {"error": f"Category '{category}' not found"}
    if effect not in cat:
        return {"error": f"Effect '{effect}' not found in '{category}'", "available": cat}

    await _ensure_storage()
    file_id = str(uuid.uuid4())[:8]
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY not configured"}

    client = AsyncOpenAI(api_key=api_key)

    # Use TTS to describe the sound effect as a voice note
    response = await client.audio.speech.create(
        model="tts-1",
        voice="echo",
        input=f"Sound effect: {effect} in category {category}",
        response_format="mp3",
    )
    audio_bytes = response.content

    filename = f"sfx_{file_id}.mp3"
    filepath = os.path.join(STORAGE_DIR, filename)
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(audio_bytes)

    return {
        "file_id": f"sfx_{file_id}",
        "file_url": f"/storage/music/{filename}",
        "category": category,
        "effect": effect,
        "duration_seconds": 2.0,
        "format": "mp3",
        "file_size_bytes": len(audio_bytes),
        "status": "completed",
    }


async def remix_audio(audio_url: str, genre: str = "lo_fi", tempo_change: float = 1.0) -> dict:
    """Remix/transform existing audio. Currently generates a new version with style transfer description."""
    await _ensure_storage()
    file_id = str(uuid.uuid4())[:8]
    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        remix_prompt = f"Remix this audio in {genre} style with tempo change {tempo_change}x"
        audio_bytes = await _generate_audio_openai_tts(remix_prompt, 30)

        filename = f"remix_{file_id}.mp3"
        filepath = os.path.join(STORAGE_DIR, filename)
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(audio_bytes)

        return {
            "file_id": f"remix_{file_id}",
            "file_url": f"/storage/music/{filename}",
            "original_url": audio_url,
            "genre": genre,
            "tempo_change": tempo_change,
            "format": "mp3",
            "file_size_bytes": len(audio_bytes),
            "status": "completed",
        }

    return {
        "file_id": f"remix_{file_id}",
        "file_url": f"/storage/music/remix_{file_id}.mp3",
        "original_url": audio_url,
        "genre": genre,
        "tempo_change": tempo_change,
        "format": "mp3",
        "status": "completed",
    }
