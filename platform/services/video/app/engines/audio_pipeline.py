"""Audio Pipeline — Generates narration and music for video scenes.

Fault-tolerant fallback chain: ElevenLabs → OpenAI TTS → Edge TTS (free).
Edge TTS requires no API keys and produces high-quality Microsoft voices.
Graceful skip for scenes without narration text.
"""
import asyncio
import os
import uuid
import logging
import aiofiles
from openai import AsyncOpenAI

logger = logging.getLogger("ominou.audio")

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "audio")
MAX_RETRIES = 3

# Edge TTS voice mapping — high-quality Microsoft voices
_EDGE_VOICE_MAP = {
    "onyx": "en-US-GuyNeural",
    "alloy": "en-US-JennyNeural",
    "echo": "en-US-EricNeural",
    "fable": "en-GB-RyanNeural",
    "nova": "en-US-AriaNeural",
    "shimmer": "en-US-SaraNeural",
    "aria": "en-US-AriaNeural",
    "marcus": "en-US-GuyNeural",
    "priya": "en-IN-NeerjaNeural",
    "chen": "zh-CN-YunxiNeural",
    "sofia": "es-ES-ElviraNeural",
    "kai": "en-AU-WilliamNeural",
    "luna": "en-US-JennyNeural",
    "ravi": "en-IN-PrabhatNeural",
}

# Language-specific Edge TTS voices (male, female)
_EDGE_LANG_VOICES = {
    "telugu": ("te-IN-MohanNeural", "te-IN-ShrutiNeural"),
    "hindi": ("hi-IN-MadhurNeural", "hi-IN-SwaraNeural"),
    "tamil": ("ta-IN-ValluvarNeural", "ta-IN-PallaviNeural"),
    "kannada": ("kn-IN-GaganNeural", "kn-IN-SapnaNeural"),
    "malayalam": ("ml-IN-MidhunNeural", "ml-IN-SobhanaNeural"),
    "bengali": ("bn-IN-BashkarNeural", "bn-IN-TanishaaNeural"),
    "marathi": ("mr-IN-ManoharNeural", "mr-IN-AarohiNeural"),
    "gujarati": ("gu-IN-NiranjanNeural", "gu-IN-DhwaniNeural"),
    "english": ("en-US-GuyNeural", "en-US-AriaNeural"),
    "spanish": ("es-ES-AlvaroNeural", "es-ES-ElviraNeural"),
    "french": ("fr-FR-HenriNeural", "fr-FR-DeniseNeural"),
    "german": ("de-DE-ConradNeural", "de-DE-KatjaNeural"),
    "japanese": ("ja-JP-KeitaNeural", "ja-JP-NanamiNeural"),
    "korean": ("ko-KR-InJoonNeural", "ko-KR-SunHiNeural"),
    "chinese": ("zh-CN-YunxiNeural", "zh-CN-XiaoxiaoNeural"),
    "arabic": ("ar-SA-HamedNeural", "ar-SA-ZariyahNeural"),
    "portuguese": ("pt-BR-AntonioNeural", "pt-BR-FranciscaNeural"),
}

# Unicode ranges for language detection
_LANG_DETECT_RANGES = [
    ("telugu", r'[\u0C00-\u0C7F]'),
    ("hindi", r'[\u0900-\u097F]'),
    ("tamil", r'[\u0B80-\u0BFF]'),
    ("kannada", r'[\u0C80-\u0CFF]'),
    ("malayalam", r'[\u0D00-\u0D7F]'),
    ("bengali", r'[\u0980-\u09FF]'),
    ("gujarati", r'[\u0A80-\u0AFF]'),
    ("marathi", r'[\u0900-\u097F]'),  # Same as Hindi (Devanagari)
    ("japanese", r'[\u3040-\u309F\u30A0-\u30FF]'),
    ("korean", r'[\uAC00-\uD7AF]'),
    ("chinese", r'[\u4E00-\u9FFF]'),
    ("arabic", r'[\u0600-\u06FF]'),
]


def _detect_language(text: str) -> str:
    """Detect language from text based on Unicode character ranges."""
    import re as _re
    for lang, pattern in _LANG_DETECT_RANGES:
        if _re.search(pattern, text):
            return lang
    return "english"


def _select_edge_voice(voice: str, language: str = "", voice_type: str = "") -> str:
    """Select the best Edge TTS voice based on language and voice type.

    Priority:
    1. Language-specific voice (male/female based on voice_type)
    2. Named voice from _EDGE_VOICE_MAP
    3. Default English male voice
    """
    lang = language.lower().strip() if language else ""

    if lang in _EDGE_LANG_VOICES:
        male, female = _EDGE_LANG_VOICES[lang]
        vtype = voice_type.lower() if voice_type else ""
        if "female" in vtype or "woman" in vtype:
            return female
        return male  # Default to male

    # Fall back to named voice map
    if voice in _EDGE_VOICE_MAP:
        return _EDGE_VOICE_MAP[voice]

    return "en-US-GuyNeural"


async def _ensure_storage():
    os.makedirs(STORAGE_DIR, exist_ok=True)


async def generate_narration(
    text: str,
    voice: str = "onyx",
    speed: float = 1.0,
    quality: str = "high",
    language: str = "",
    voice_type: str = "",
) -> dict:
    """Generate narration audio. Fallback: ElevenLabs → OpenAI TTS → Edge TTS (free).

    Edge TTS always works without API keys as the final fallback.
    Auto-detects language from text to select the right voice.
    """
    await _ensure_storage()

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Try ElevenLabs first (highest quality)
            elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
            if elevenlabs_key:
                try:
                    return await _elevenlabs_tts(text, voice, speed, elevenlabs_key)
                except Exception as e:
                    logger.warning("ElevenLabs failed (attempt %d): %s", attempt, e)

            # Try OpenAI TTS (high quality)
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                try:
                    return await _openai_tts(text, voice, speed, openai_key)
                except Exception as e:
                    logger.warning("OpenAI TTS failed (attempt %d): %s", attempt, e)

            # Edge TTS — always available, no API key needed
            return await _edge_tts(text, voice, speed, language=language, voice_type=voice_type)

        except Exception as e:
            last_error = str(e)
            logger.warning("Narration attempt %d failed: %s", attempt, e)
            if attempt < MAX_RETRIES:
                await asyncio.sleep(1.5 * attempt)

    return {"status": "failed", "error": f"Narration failed after {MAX_RETRIES} attempts: {last_error}"}


async def _openai_tts(text: str, voice: str, speed: float, api_key: str) -> dict:
    """Generate speech using OpenAI TTS."""
    client = AsyncOpenAI(api_key=api_key)

    voice_map = {
        "aria": "nova", "marcus": "onyx", "priya": "shimmer",
        "chen": "echo", "sofia": "alloy", "kai": "fable",
        "luna": "nova", "ravi": "onyx",
    }
    tts_voice = voice_map.get(voice, voice if voice in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"] else "onyx")

    tts_model = "tts-1-hd"  # Always use HD model for best quality
    response = await client.audio.speech.create(
        model=tts_model,
        voice=tts_voice,
        input=text,
        speed=speed,
    )

    file_id = str(uuid.uuid4())[:12]
    filename = f"narration_{file_id}.mp3"
    filepath = os.path.join(STORAGE_DIR, filename)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(response.content)

    word_count = len(text.split())
    return {
        "audio_file": filepath,
        "file_url": f"/storage/audio/{filename}",
        "duration_seconds": round(word_count / 2.5 / speed, 1),
        "voice": tts_voice,
        "provider": "openai",
        "status": "completed",
    }


async def _edge_tts(text: str, voice: str, speed: float, language: str = "", voice_type: str = "") -> dict:
    """Generate speech using Microsoft Edge TTS — free, no API key required.

    Auto-detects language from text to select the right voice.
    Supports Telugu, Hindi, Tamil, and 15+ other languages.
    """
    import edge_tts

    # Auto-detect language from text content if not specified
    detected_lang = language or _detect_language(text)
    edge_voice = _select_edge_voice(voice, detected_lang, voice_type)

    logger.info("Edge TTS: voice=%s, detected_lang=%s, text_len=%d", edge_voice, detected_lang, len(text))

    # Edge TTS speed: "+0%" is normal, "-10%" is 0.9x
    speed_pct = int((speed - 1.0) * 100)
    rate_str = f"{speed_pct:+d}%"

    file_id = str(uuid.uuid4())[:12]
    filename = f"narration_{file_id}.mp3"
    filepath = os.path.join(STORAGE_DIR, filename)

    communicate = edge_tts.Communicate(text, edge_voice, rate=rate_str)
    await communicate.save(filepath)

    if not os.path.exists(filepath) or os.path.getsize(filepath) < 100:
        raise RuntimeError(f"Edge TTS produced empty file for voice {edge_voice}")

    word_count = len(text.split())
    return {
        "audio_file": filepath,
        "file_url": f"/storage/audio/{filename}",
        "duration_seconds": round(word_count / 2.5 / speed, 1),
        "voice": edge_voice,
        "language": detected_lang,
        "provider": "edge_tts",
        "status": "completed",
    }


async def _elevenlabs_tts(text: str, voice: str, speed: float, api_key: str) -> dict:
    """Generate speech using ElevenLabs (premium quality)."""
    from elevenlabs import AsyncElevenLabs

    client = AsyncElevenLabs(api_key=api_key)

    # Use a default high-quality voice if custom voice not found
    voice_id = voice  # ElevenLabs uses voice IDs

    audio_generator = await client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_192",  # Higher bitrate for better quality
    )

    file_id = str(uuid.uuid4())[:12]
    filename = f"narration_{file_id}.mp3"
    filepath = os.path.join(STORAGE_DIR, filename)

    async with aiofiles.open(filepath, "wb") as f:
        async for chunk in audio_generator:
            await f.write(chunk)

    word_count = len(text.split())
    return {
        "audio_file": filepath,
        "file_url": f"/storage/audio/{filename}",
        "duration_seconds": round(word_count / 2.5 / speed, 1),
        "voice": voice_id,
        "provider": "elevenlabs",
        "status": "completed",
    }


async def _noop_narration() -> dict:
    """Return a skip result for scenes with no narration text."""
    return {"status": "skipped", "audio_file": None}


async def generate_scene_narrations(
    scenes: list[dict],
    voice: str = "onyx",
    quality: str = "high",
    language: str = "",
    voice_type: str = "",
    speed: float = 1.0,
) -> list[dict]:
    """Generate narration audio for all scenes in parallel.
    
    Handles exceptions per-scene so one failure doesn't kill all narrations.
    Supports multilingual: auto-detects language from text or uses specified language.
    """
    tasks = []
    for scene in scenes:
        narration_text = scene.get("narration", "")
        if narration_text and narration_text.strip():
            tasks.append(generate_narration(
                narration_text,
                voice=voice,
                quality=quality,
                language=language,
                voice_type=voice_type,
                speed=speed,
            ))
        else:
            tasks.append(_noop_narration())

    results = await asyncio.gather(*tasks, return_exceptions=True)

    narrations = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            narrations.append({"status": "failed", "error": str(result), "scene": i + 1})
        else:
            narrations.append(result)

    return narrations


async def generate_background_music(
    genre: str = "cinematic",
    mood: str = "epic",
    duration_seconds: int = 60,
    tempo: str = "medium",
) -> dict:
    """Generate background music. Uses Suno API if available, otherwise OpenAI for description.

    Returns audio_file path if music was generated, or None with metadata if only description.
    """
    await _ensure_storage()

    # Try Suno API first (real music generation)
    suno_key = os.getenv("SUNO_API_KEY")
    if suno_key:
        try:
            return await _suno_music(genre, mood, duration_seconds, tempo, suno_key)
        except Exception as e:
            logger.warning("Suno music generation failed: %s — falling back", e)

    # FFmpeg ambient music generation — no API key required
    try:
        return await _ffmpeg_ambient_music(genre, mood, duration_seconds, tempo)
    except Exception as e:
        logger.warning("FFmpeg ambient music failed: %s — falling back to metadata", e)

    # Fallback: metadata only
    return {
        "audio_file": None,
        "status": "skipped",
        "description": f"{genre} {mood} music at {tempo} tempo",
    }


async def _ffmpeg_ambient_music(
    genre: str, mood: str, duration_seconds: int, tempo: str
) -> dict:
    """Generate ambient background music using FFmpeg audio synthesis.

    Creates layered sine/triangle waves with slow modulation for a cinematic pad feel.
    No external API required.
    """
    import shutil

    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg not available")

    # Mood → frequency/character mapping
    mood_freqs = {
        "epic": (65.41, 82.41, 130.81),      # C2, E2, C3 — powerful low tones
        "calm": (130.81, 164.81, 196.00),     # C3, E3, G3 — gentle major
        "dark": (61.74, 77.78, 92.50),        # B1, Eb2, Gb2 — minor/diminished
        "uplifting": (130.81, 164.81, 196.0), # C3, E3, G3
        "tense": (61.74, 73.42, 87.31),       # B1, D2, F2
        "romantic": (110.0, 138.59, 164.81),  # A2, C#3, E3
    }
    f1, f2, f3 = mood_freqs.get(mood, mood_freqs["epic"])

    # Tempo → modulation speed (tremolo f must be >= 0.1)
    mod_speed = {"slow": 0.5, "medium": 1.0, "fast": 2.0}.get(tempo, 1.0)

    # Build layered ambient pad with FFmpeg audio filters
    # Use separate lavfi inputs and filter_complex for mixing
    fade_out_start = max(0, duration_seconds - 4)

    file_id = str(uuid.uuid4())[:12]
    filename = f"bgm_{file_id}.mp3"
    filepath = os.path.join(STORAGE_DIR, filename)

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=f={f1}:d={duration_seconds}",
        "-f", "lavfi", "-i", f"sine=f={f2}:d={duration_seconds}",
        "-f", "lavfi", "-i", f"sine=f={f3}:d={duration_seconds}",
        "-filter_complex",
        (
            f"[0:a]volume=0.15,tremolo=f={mod_speed}:d=0.4[a1];"
            f"[1:a]volume=0.12,tremolo=f={mod_speed * 0.7:.4f}:d=0.3[a2];"
            f"[2:a]volume=0.10,tremolo=f={mod_speed * 1.3:.4f}:d=0.5[a3];"
            f"[a1][a2][a3]amix=inputs=3:duration=first,"
            f"lowpass=f=800,highpass=f=40,"
            f"afade=t=in:st=0:d=3,afade=t=out:st={fade_out_start}:d=4[out]"
        ),
        "-map", "[out]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        "-t", str(duration_seconds),
        filepath,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0 or not os.path.exists(filepath):
        raise RuntimeError(f"FFmpeg music gen failed: {stderr.decode()[-300:]}")

    return {
        "audio_file": filepath,
        "file_url": f"/storage/audio/{filename}",
        "genre": genre,
        "mood": mood,
        "duration_seconds": duration_seconds,
        "provider": "ominou_synth",
        "status": "completed",
    }


async def _suno_music(genre: str, mood: str, duration_seconds: int, tempo: str, api_key: str) -> dict:
    """Generate music via Suno API."""
    import httpx

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            "https://api.suno.ai/v1/generation",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "prompt": f"{genre} {mood} background music, {tempo} tempo, "
                          f"{duration_seconds} seconds, instrumental, professional quality",
                "duration": min(duration_seconds, 240),
                "instrumental": True,
            },
        )
        response.raise_for_status()
        data = response.json()

    audio_url = data.get("audio_url", "")
    if not audio_url:
        return {"audio_file": None, "status": "failed", "error": "No audio URL in Suno response"}

    # Download audio file
    file_id = str(uuid.uuid4())[:12]
    filename = f"bgm_{file_id}.mp3"
    filepath = os.path.join(STORAGE_DIR, filename)

    async with httpx.AsyncClient(timeout=60) as client:
        audio_resp = await client.get(audio_url)
        audio_resp.raise_for_status()

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(audio_resp.content)

    return {
        "audio_file": filepath,
        "file_url": f"/storage/audio/{filename}",
        "genre": genre,
        "mood": mood,
        "duration_seconds": duration_seconds,
        "provider": "suno",
        "status": "completed",
    }
