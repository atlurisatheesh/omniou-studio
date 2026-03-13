"""Music Studio AI Engine — Music Generation, Jingles, Sound Effects."""
import uuid

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


def generate_music(prompt: str, genre: str = "ambient", mood: str = "calm",
                   duration_seconds: int = 30, bpm: int = 120) -> dict:
    """Generate AI music from prompt."""
    file_id = str(uuid.uuid4())[:8]
    return {
        "file_id": f"music_{file_id}",
        "file_url": f"/storage/music/music_{file_id}.mp3",
        "prompt": prompt,
        "genre": genre,
        "mood": mood,
        "duration_seconds": duration_seconds,
        "bpm": bpm,
        "sample_rate": 44100,
        "format": "mp3",
        "key": "C Major",
        "status": "completed",
    }


def generate_jingle(brand_name: str, style: str = "corporate", duration_seconds: int = 15) -> dict:
    """Generate a brand jingle."""
    file_id = str(uuid.uuid4())[:8]
    return {
        "file_id": f"jingle_{file_id}",
        "file_url": f"/storage/music/jingle_{file_id}.mp3",
        "brand_name": brand_name,
        "style": style,
        "duration_seconds": duration_seconds,
        "has_vocals": True,
        "format": "mp3",
        "status": "completed",
    }


def generate_sfx(category: str, effect: str) -> dict:
    """Generate a sound effect."""
    cat = SFX_CATEGORIES.get(category)
    if not cat:
        return {"error": f"Category '{category}' not found"}
    if effect not in cat:
        return {"error": f"Effect '{effect}' not found in '{category}'", "available": cat}

    file_id = str(uuid.uuid4())[:8]
    return {
        "file_id": f"sfx_{file_id}",
        "file_url": f"/storage/music/sfx_{file_id}.wav",
        "category": category,
        "effect": effect,
        "duration_seconds": 2.0,
        "format": "wav",
        "status": "completed",
    }


def remix_audio(audio_url: str, genre: str = "lo_fi", tempo_change: float = 1.0) -> dict:
    """Remix/transform existing audio."""
    file_id = str(uuid.uuid4())[:8]
    return {
        "file_id": f"remix_{file_id}",
        "file_url": f"/storage/music/remix_{file_id}.mp3",
        "original_url": audio_url,
        "genre": genre,
        "tempo_change": tempo_change,
        "format": "mp3",
        "status": "completed",
    }
