"""Screenplay Engine — Uses GPT-4o to decompose a video prompt into a detailed multi-scene screenplay.

Fault-tolerant: retries up to 3 times, recovers from malformed JSON, 
falls back to simple scene split if API is completely unavailable.
"""
import asyncio
import json
import logging
import os
import re
from openai import AsyncOpenAI

logger = logging.getLogger("ominou.screenplay")

MAX_RETRIES = 3

# Keywords that indicate the user provided technical cinematography directives
_DIRECTIVE_KEYWORDS = [
    "camera", "lens", "depth of field", "shallow", "handheld", "stabilization",
    "motion blur", "sensor", "grain", "film grain", "lighting", "practical light",
    "realism", "realistic", "ultra-realistic", "micro-expression", "blinking",
    "breathing", "lip sync", "mouth movement", "phoneme", "reverb", "ambience",
    "ambient", "over-the-shoulder", "close-up", "medium shot", "wide shot",
    "dolly", "crane", "tracking", "imperfection", "vignette", "bokeh",
    "full-frame", "35mm", "anamorphic", "ARRI", "skin texture", "eye focus",
]


def _extract_technical_directives(prompt: str) -> str:
    """Extract technical cinematography directives from the user prompt.
    
    If the user provided detailed instructions about camera, lighting, realism,
    acting style, etc., we preserve those as rules for GPT to embed in every scene.
    """
    prompt_lower = prompt.lower()
    has_directives = sum(1 for kw in _DIRECTIVE_KEYWORDS if kw in prompt_lower)

    if has_directives < 3:
        return ""  # Not enough technical detail to extract

    # The prompt itself contains rich directives — tell GPT to embed them
    return (
        f"\nCRITICAL — USER TECHNICAL DIRECTIVES (embed into EVERY scene visual_prompt):\n"
        f"The user provided specific technical/cinematography requirements. You MUST incorporate "
        f"these directives into each scene's visual_prompt so AI video generators follow them:\n"
        f"---\n{prompt[:2000]}\n---\n"
        f"Distill the above into each scene: camera type/lens, lighting style, human realism details, "
        f"visual imperfections, and camera movement constraints. Do NOT ignore any directive."
    )


def _extract_json(text: str) -> dict | None:
    """Try to extract valid JSON from a response that may contain markdown fences or extra text."""
    # Try direct parse first
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # Try extracting from markdown code fences
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding the first { ... } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _enforce_duration(screenplay: dict, target_duration: int) -> dict:
    """Adjust scene durations so they sum EXACTLY to target_duration."""
    scenes = screenplay.get("scenes", [])
    if not scenes:
        return screenplay

    # Ensure every scene has a numeric duration
    for s in scenes:
        if not isinstance(s.get("duration_seconds"), (int, float)) or s["duration_seconds"] < 1:
            s["duration_seconds"] = max(1, target_duration // len(scenes))

    total = sum(s["duration_seconds"] for s in scenes)
    diff = target_duration - total

    if diff != 0:
        # Distribute difference across scenes (1 second at a time)
        step = 1 if diff > 0 else -1
        idx = 0
        while diff != 0:
            scenes[idx % len(scenes)]["duration_seconds"] += step
            # Don't let any scene go below 1 second
            if scenes[idx % len(scenes)]["duration_seconds"] < 1:
                scenes[idx % len(scenes)]["duration_seconds"] = 1
            else:
                diff -= step
            idx += 1
            if idx > len(scenes) * 20:
                break  # safety valve

    screenplay["total_duration_seconds"] = target_duration
    return screenplay


def _compute_scene_durations(target_duration: int) -> list[int]:
    """Compute per-scene durations that sum EXACTLY to target_duration.
    
    Strategy: use 4-6 second scenes for short videos, 5-8 second scenes for longer ones.
    Distributes any remainder across scenes so the total is exact.
    """
    if target_duration <= 15:
        ideal = 4
    elif target_duration <= 60:
        ideal = 5
    elif target_duration <= 180:
        ideal = 6
    else:
        ideal = 7

    scene_count = max(3, target_duration // ideal)
    base = target_duration // scene_count
    remainder = target_duration - base * scene_count
    durations = [base] * scene_count
    for i in range(remainder):
        durations[i] += 1
    return durations


def _fallback_screenplay(prompt: str, target_duration: int, style: str) -> dict:
    """Generate a structured screenplay without any API call — used as last resort.

    Splits the prompt into meaningful chunks and generates narration per scene.
    """
    durations = _compute_scene_durations(target_duration)
    n = len(durations)

    # Split prompt into sentences for distributing across scenes
    sentences = re.split(r'(?<=[.!?])\s+', prompt.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    # If prompt is a single long sentence, split by commas/semicolons too
    if len(sentences) < n:
        expanded = []
        for s in sentences:
            parts = re.split(r'[,;]\s*', s)
            expanded.extend(p.strip() for p in parts if p.strip())
        if len(expanded) > len(sentences):
            sentences = expanded

    # Distribute sentences across scenes
    scene_texts = [""] * n
    if sentences:
        per_scene = max(1, len(sentences) // n)
        for i in range(n):
            start = i * per_scene
            end = start + per_scene if i < n - 1 else len(sentences)
            scene_texts[i] = ". ".join(sentences[start:end])
        # Ensure all scenes have text
        for i in range(n):
            if not scene_texts[i]:
                scene_texts[i] = scene_texts[max(0, i - 1)]
    else:
        for i in range(n):
            scene_texts[i] = prompt

    # Camera variations for visual interest
    cameras = [
        "establishing wide shot", "slow dolly in", "close-up shot",
        "tracking shot", "aerial view", "medium shot",
        "over-the-shoulder", "panoramic sweep",
    ]
    lightings = [
        "golden hour lighting", "soft ambient lighting", "dramatic side lighting",
        "natural daylight", "warm interior lighting", "cool blue tones",
        "studio lighting", "backlit silhouette",
    ]
    transitions = ["dissolve", "fade", "cross dissolve", "smooth cut"]

    scenes = []
    for i, dur in enumerate(durations):
        narration = scene_texts[i]
        # Create a clean visual description (not the raw prompt)
        visual = f"{style.capitalize()} scene: {narration[:150]}"

        scenes.append({
            "scene_number": i + 1,
            "duration_seconds": dur,
            "visual_prompt": visual,
            "camera": cameras[i % len(cameras)],
            "lighting": lightings[i % len(lightings)],
            "narration": narration,
            "transition_to_next": transitions[i % len(transitions)] if i < n - 1 else "fade to black",
        })
    return {
        "title": prompt[:80],
        "total_duration_seconds": target_duration,
        "style": style,
        "music": {"genre": "cinematic", "mood": "epic", "tempo": "medium"},
        "scenes": scenes,
        "scene_count": n,
        "fallback": True,
    }


# ═══ SCRIPT PARSING ═══════════════════════════════════════════════════


def _parse_json_script(script: str, target_duration: int, style: str) -> dict | None:
    """Parse a JSON-formatted script into structured scenes.

    Handles the structured JSON format with scenes containing:
    - visual, camera, bgm, narration, dialogue, sfx fields
    - Top-level title, language, voice, duration_sec, subtitle settings
    Returns None if the script is not valid JSON or doesn't have a scenes array.
    """
    data = _extract_json(script)
    if not data or not isinstance(data.get("scenes"), list):
        return None

    json_scenes = data["scenes"]
    if not json_scenes:
        return None

    title = data.get("title", "Video")
    language = data.get("language", "english")
    voice_meta = data.get("voice", {})

    # Use JSON-specified duration if available, otherwise use target
    total_duration = data.get("duration_sec", target_duration) or target_duration

    n = len(json_scenes)
    # Distribute duration across scenes
    base_dur = max(2, total_duration // n)
    remainder = total_duration - base_dur * n
    durations = [base_dur] * n
    for i in range(abs(remainder)):
        durations[i % n] += 1 if remainder > 0 else -1
        if durations[i % n] < 2:
            durations[i % n] = 2

    # Determine music from scene BGM descriptions
    bgm_descriptions = [s.get("bgm", "") for s in json_scenes if s.get("bgm")]
    overall_bgm = bgm_descriptions[0] if bgm_descriptions else "cinematic"

    # Guess mood from bgm text
    bgm_text = " ".join(bgm_descriptions).lower()
    if any(w in bgm_text for w in ["epic", "rising", "powerful"]):
        mood = "epic"
    elif any(w in bgm_text for w in ["sad", "low", "slow"]):
        mood = "dark"
    elif any(w in bgm_text for w in ["soft", "flute", "gentle", "calm"]):
        mood = "calm"
    elif any(w in bgm_text for w in ["divine", "choir", "devotional"]):
        mood = "uplifting"
    else:
        mood = "epic"

    scenes = []
    for i, js in enumerate(json_scenes):
        # Narration: prefer 'narration' field, then 'dialogue'
        narration = js.get("narration", "")
        dialogue = js.get("dialogue", "")

        # Build the spoken text: combine narration and dialogue
        spoken_text = narration
        if dialogue and not narration:
            spoken_text = dialogue
        elif dialogue and narration:
            spoken_text = f"{narration} {dialogue}"

        # Visual prompt: use the 'visual' field for AI video generators
        visual = js.get("visual", spoken_text[:150] if spoken_text else f"Scene {i+1}")
        camera = js.get("camera", "cinematic shot")
        bgm = js.get("bgm", "")
        sfx = js.get("sfx", "")

        scenes.append({
            "scene_number": i + 1,
            "duration_seconds": durations[i],
            "visual_prompt": f"{style.capitalize()} {visual}",
            "camera": camera,
            "lighting": "cinematic lighting",
            "narration": spoken_text,
            "dialogue": dialogue,
            "bgm": bgm,
            "sfx": sfx,
            "transition_to_next": "dissolve" if i < n - 1 else "fade to black",
        })

    return {
        "title": title,
        "total_duration_seconds": total_duration,
        "style": style,
        "language": language,
        "voice": voice_meta,
        "music": {"genre": overall_bgm, "mood": mood, "tempo": "medium"},
        "scenes": scenes,
        "scene_count": n,
        "from_json_script": True,
    }


# Detect scene delimiters in raw scripts: "SCENE 1:", "INT.", "EXT.", "---", "###", etc.
_SCENE_SPLIT_RE = re.compile(
    r"(?:^|\n)(?="
    r"(?:SCENE\s*\d+)|"
    r"(?:INT\.\s)|"
    r"(?:EXT\.\s)|"
    r"(?:---+)|"
    r"(?:###\s)|"
    r"(?:ACT\s+\w+)|"
    r"(?:CHAPTER\s+\d+)"
    r")",
    re.IGNORECASE,
)


def _parse_script_to_scenes(script: str, target_duration: int, style: str) -> dict:
    """Parse a raw script/screenplay into structured scenes without an API call.

    Detects JSON format first, then scene breaks from common delimiters (SCENE, INT./EXT., ---, ###).
    Falls back to splitting by double-newline paragraphs if no markers found.
    """
    script = script.strip()
    if not script:
        return _fallback_screenplay("No script provided", target_duration, style)

    # Try JSON format first (structured scripts with scenes array)
    json_result = _parse_json_script(script, target_duration, style)
    if json_result:
        logger.info("Parsed JSON script: %d scenes, language=%s", json_result["scene_count"], json_result.get("language", "?"))
        return json_result

    # Try splitting by scene markers
    chunks = [c.strip() for c in _SCENE_SPLIT_RE.split(script) if c.strip()]

    # Fallback: split by double newlines (paragraphs)
    if len(chunks) <= 1:
        chunks = [c.strip() for c in re.split(r"\n\s*\n", script) if c.strip()]

    # Fallback: split by single newlines if still just one chunk
    if len(chunks) <= 1 and len(script) > 200:
        chunks = [c.strip() for c in script.split("\n") if c.strip()]

    # Merge very short chunks into their neighbors
    merged: list[str] = []
    for chunk in chunks:
        if merged and len(merged[-1]) < 60:
            merged[-1] = merged[-1] + " " + chunk
        else:
            merged.append(chunk)
    chunks = merged if merged else chunks

    # Compute durations to match target
    durations = _compute_scene_durations(target_duration)

    # Align chunks to duration count: merge or split
    while len(chunks) > len(durations) and len(chunks) > 1:
        # Merge the two shortest adjacent chunks
        min_idx = min(range(len(chunks) - 1), key=lambda i: len(chunks[i]) + len(chunks[i + 1]))
        chunks[min_idx] = chunks[min_idx] + " " + chunks[min_idx + 1]
        chunks.pop(min_idx + 1)

    while len(chunks) < len(durations):
        # Duplicate the longest chunk
        longest_idx = max(range(len(chunks)), key=lambda i: len(chunks[i]))
        chunks.append(chunks[longest_idx])

    chunks = chunks[: len(durations)]

    # Extract characters for consistency
    characters = _extract_characters(script)

    # Camera variations
    cameras = [
        "establishing wide shot", "slow dolly in", "close-up shot",
        "tracking shot", "aerial view", "medium shot",
        "over-the-shoulder", "panoramic sweep",
    ]
    lightings = [
        "golden hour lighting", "soft ambient lighting", "dramatic side lighting",
        "natural daylight", "warm interior lighting", "cool blue tones",
    ]

    scenes = []
    for i, (chunk, dur) in enumerate(zip(chunks, durations)):
        # Separate narration (dialogue lines) from visual description
        narration = ""
        visual_parts = []

        # Lines in ALL CAPS followed by a colon are character dialogue
        dialogue_lines = re.findall(r"(?:^|\n)([A-Z][A-Z\s]+):\s*(.+)", chunk)
        if dialogue_lines:
            narration = " ".join(line.strip() for _, line in dialogue_lines)
            # Remove dialogue from visual description
            clean_visual = re.sub(r"(?:^|\n)[A-Z][A-Z\s]+:\s*.+", "", chunk).strip()
            visual_parts.append(clean_visual if clean_visual else chunk[:150])
        else:
            # Use the chunk text as narration
            narration = chunk.strip()
            visual_parts.append(chunk[:150])

        # Build clean visual prompt
        visual_desc = " ".join(visual_parts).strip()
        # Remove raw scene markers from visual
        visual_desc = re.sub(r"(?i)^(SCENE\s*\d+[:\s]*|INT\.\s*|EXT\.\s*|---+|###\s*)", "", visual_desc).strip()

        scenes.append({
            "scene_number": i + 1,
            "duration_seconds": dur,
            "visual_prompt": f"{style.capitalize()} scene: {visual_desc[:200]}",
            "camera": cameras[i % len(cameras)],
            "lighting": lightings[i % len(lightings)],
            "narration": narration,
            "transition_to_next": "dissolve" if i < len(durations) - 1 else "fade to black",
        })

    return {
        "title": chunks[0][:80] if chunks else "Script Video",
        "total_duration_seconds": target_duration,
        "style": style,
        "music": {"genre": "cinematic", "mood": "epic", "tempo": "medium"},
        "scenes": scenes,
        "scene_count": len(scenes),
        "characters": characters,
        "from_script": True,
    }


def _extract_characters(text: str) -> list[str]:
    """Extract character names from a script for visual consistency across scenes.

    Looks for screenplay-format names (ALL CAPS before colons), quoted names,
    and frequently capitalized proper nouns.
    """
    characters: list[str] = []
    seen_lower: set[str] = set()

    # Screenplay format: CHARACTER NAME:
    for match in re.finditer(r"(?:^|\n)([A-Z][A-Z\s]{1,30}):", text):
        name = match.group(1).strip().title()
        if name.lower() not in seen_lower and len(name) > 1:
            characters.append(name)
            seen_lower.add(name.lower())

    # Explicit character markers: "Character: Name" or "CHARACTERS: ..."
    for match in re.finditer(r"(?i)characters?\s*[:=]\s*([^\n]+)", text):
        for part in re.split(r"[,;&]", match.group(1)):
            name = part.strip().strip('"').strip("'")
            if name and name.lower() not in seen_lower and len(name) > 1:
                characters.append(name)
                seen_lower.add(name.lower())

    return characters[:10]  # Cap at 10 characters


async def decompose_prompt_to_screenplay(
    prompt: str,
    target_duration: int,
    style: str = "cinematic",
    include_narration: bool = True,
    include_music: bool = True,
    script: str | None = None,
) -> dict:
    """Break a user's video prompt into a detailed multi-scene screenplay.
    
    If a raw script is provided, it is parsed into scenes (with GPT enhancement
    if an API key is available, or locally as a fallback).
    
    Retries up to 3 times on API failure with exponential backoff.
    Recovers from malformed JSON responses.
    Falls back to simple scene generation if all retries fail.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    # If a raw script is provided, try JSON parsing first (no API needed)
    if script:
        json_result = _parse_json_script(script, target_duration, style)
        if json_result:
            logger.info("Parsed structured JSON script: %d scenes", json_result["scene_count"])
            return json_result

    # If a raw script is provided and no API key, parse locally
    if script and not api_key:
        logger.info("Script provided without OPENAI_API_KEY — parsing locally")
        return _parse_script_to_scenes(script, target_duration, style)

    if not api_key:
        logger.warning("OPENAI_API_KEY not set — using fallback screenplay")
        return _fallback_screenplay(prompt, target_duration, style)

    client = AsyncOpenAI(api_key=api_key)

    durations = _compute_scene_durations(target_duration)
    scene_count = len(durations)
    duration_guide = ", ".join(str(d) for d in durations)

    # Scale max_tokens for longer videos (more scenes = more JSON)
    max_tokens = min(16384, 4096 + scene_count * 80)

    narration_rule = "- Write a narration line for each scene (1-2 sentences spoken by a narrator)" if include_narration else ""
    music_rule = "- Suggest a music mood/genre for the overall video" if include_music else ""
    music_json = '"music": {"genre": "...", "mood": "...", "tempo": "slow/medium/fast"},' if include_music else ""
    narration_json = '"narration": "What the narrator says during this scene",' if include_narration else ""

    # Extract technical directives from user prompt to propagate into every scene
    technical_directives = _extract_technical_directives(prompt)

    # Character consistency: extract names from prompt/script and inject rules
    source_text = script or prompt
    characters = _extract_characters(source_text)
    character_rules = ""
    if characters:
        char_list = ", ".join(characters[:8])
        character_rules = (
            f"\nCHARACTER CONSISTENCY (CRITICAL):\n"
            f"Characters identified: {char_list}\n"
            f"- Every time a character appears, describe them with IDENTICAL physical traits "
            f"(hair color/style, skin tone, clothing, age, build, distinguishing features).\n"
            f"- Use the character's full name or consistent reference in every scene's visual_prompt.\n"
            f"- NEVER change a character's appearance between scenes unless the story requires it.\n"
            f"- Include a 'characters' key in the JSON with a list of character description objects.\n"
        )

    # If a raw script was provided, adapt the system prompt
    script_section = ""
    if script:
        script_section = (
            f"\n\nRAW SCRIPT PROVIDED — adapt this into your screenplay format:\n"
            f"---\n{script[:8000]}\n---\n"
            f"Parse the above script into {scene_count} scenes. Preserve the dialogue, "
            f"characters, and story beats. Enhance each scene with detailed visual descriptions "
            f"suitable for AI video generation. Keep narration from the script when available.\n"
        )

    system_prompt = (
        f"You are a world-class cinematographer and screenwriter. "
        f"Your job is to take a user's video concept and produce a detailed scene-by-scene screenplay "
        f"optimized for AI video generation.\n\n"
        f"RULES:\n"
        f"- Break the video into exactly {scene_count} scenes\n"
        f"- Scene durations MUST be exactly [{duration_guide}] seconds (in order). Total MUST equal {target_duration}s.\n"
        f"- Write each scene's visual description as a single detailed paragraph (80-150 words)\n"
        f"- Include: camera angle, lens, movement, lighting, colors, subject details, atmosphere, textures\n"
        f"- Scenes must flow naturally from one to the next — maintain visual continuity\n"
        f'- Use cinematic language: "dolly in", "crane shot", "golden hour", "shallow depth of field"\n'
        f"- Style: {style}\n"
        f"{narration_rule}\n"
        f"{music_rule}\n"
        f"{character_rules}\n"
        f"{technical_directives}\n"
        f"{script_section}\n\n"
        f"OUTPUT FORMAT (strict JSON):\n"
        f'{{\n'
        f'  "title": "Video title",\n'
        f'  "total_duration_seconds": {target_duration},\n'
        f'  "style": "{style}",\n'
        f'  {music_json}\n'
        f'  "scenes": [\n'
        f'    {{\n'
        f'      "scene_number": 1,\n'
        f'      "duration_seconds": {durations[0]},\n'
        f'      "visual_prompt": "Detailed visual description for AI video generation...",\n'
        f'      "camera": "Camera movement and lens description",\n'
        f'      "lighting": "Lighting description",\n'
        f'      {narration_json}\n'
        f'      "transition_to_next": "cut/dissolve/fade/wipe"\n'
        f'    }}\n'
        f'  ]\n'
        f'}}'
    )

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": (
                        f"Create a {target_duration}-second {style} video about: {prompt}"
                        + (f"\n\nBased on this script:\n{script[:4000]}" if script else "")
                    )},
                ],
                response_format={"type": "json_object"},
                temperature=0.8,
                max_tokens=max_tokens,
            )

            raw = response.choices[0].message.content
            screenplay = _extract_json(raw)

            if screenplay and isinstance(screenplay.get("scenes"), list) and len(screenplay["scenes"]) > 0:
                screenplay["scene_count"] = len(screenplay["scenes"])
                # Enforce precise duration: correct scene durations to sum exactly to target
                screenplay = _enforce_duration(screenplay, target_duration)
                return screenplay

            last_error = "Response had no valid scenes"
            logger.warning("Screenplay attempt %d: %s", attempt, last_error)

        except Exception as e:
            last_error = str(e)
            logger.warning("Screenplay attempt %d failed: %s", attempt, e)

        if attempt < MAX_RETRIES:
            await asyncio.sleep(2 * attempt)

    # All retries exhausted — use fallback
    logger.error("Screenplay generation failed after %d attempts: %s — using fallback", MAX_RETRIES, last_error)
    if script:
        return _parse_script_to_scenes(script, target_duration, style)
    return _fallback_screenplay(prompt, target_duration, style)
