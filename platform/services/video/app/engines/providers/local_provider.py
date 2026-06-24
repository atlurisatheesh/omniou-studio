"""Ominou Local Engine — Generates cinematic video scenes locally using FFmpeg.

No external API keys required. Creates visually rich animated scenes with:
- Animated color gradient backgrounds with smooth transitions
- Ken Burns zoom/pan effect for cinematic feel
- Scene title cards with elegant typography
- Narration text as clean lower-third overlay
- Subtle particle/noise effects for depth
- Animated watermark
"""
import asyncio
import os
import uuid
import textwrap
import logging
import re

from .base import VideoProvider, ProviderResult

logger = logging.getLogger("ominou.provider.local")

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "storage", "videos")

# Resolution presets
_RES = {
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "2K": (2560, 1440),
    "4K": (3840, 2160),
}

# Color palettes per style — (bg1, bg2, accent, text_color)
_PALETTES = {
    "cinematic": [
        ("#0a0a1a", "#1a0a2e", "#6c5ce7", "#ffffff"),
        ("#1a0a2e", "#0a1a2e", "#a29bfe", "#f0f0f0"),
        ("#0d0d1a", "#1a1a3e", "#fd79a8", "#ffffff"),
    ],
    "3d": [
        ("#0f0c29", "#302b63", "#00cec9", "#ffffff"),
        ("#141e30", "#243b55", "#55efc4", "#f0f0f0"),
    ],
    "2d_animation": [
        ("#2d1b69", "#6c5ce7", "#ffeaa7", "#ffffff"),
        ("#e17055", "#fab1a0", "#fdcb6e", "#2d3436"),
    ],
    "normal": [
        ("#1a1a2e", "#16213e", "#74b9ff", "#ffffff"),
        ("#2c3e50", "#34495e", "#81ecec", "#f0f0f0"),
    ],
    "documentary": [
        ("#2c3e50", "#3d566e", "#dfe6e9", "#ffffff"),
        ("#1a1a2e", "#252545", "#b2bec3", "#f0f0f0"),
    ],
    "slow_motion": [
        ("#0a192f", "#172a45", "#00b894", "#ffffff"),
        ("#0d1b2a", "#1b2838", "#55efc4", "#f0f0f0"),
    ],
    "time_lapse": [
        ("#ff7e5f", "#feb47b", "#ffffff", "#2d3436"),
        ("#4facfe", "#00f2fe", "#ffffff", "#2d3436"),
    ],
    "vlog": [
        ("#667eea", "#764ba2", "#fd79a8", "#ffffff"),
        ("#a18cd1", "#fbc2eb", "#6c5ce7", "#2d3436"),
    ],
    "commercial": [
        ("#00b4db", "#0083b0", "#ffeaa7", "#ffffff"),
        ("#ee0979", "#ff6a00", "#ffffff", "#2d3436"),
    ],
    "music_video": [
        ("#8e2de2", "#4a00e0", "#fd79a8", "#ffffff"),
        ("#fc466b", "#3f5efb", "#ffeaa7", "#ffffff"),
    ],
}


def _get_palette(style: str, scene_idx: int = 0):
    palettes = _PALETTES.get(style, _PALETTES["cinematic"])
    p = palettes[scene_idx % len(palettes)]
    return p[0], p[1], p[2], p[3]


def _clean_text_for_ffmpeg(text: str) -> str:
    """Clean text for FFmpeg drawtext rendering.
    
    If text contains non-Latin scripts (Telugu, Hindi, etc.), use only the
    Latin-script portions or produce a transliterated summary since default
    FFmpeg fonts don't support these scripts.
    """
    import re as _re

    # Check if text has non-ASCII characters (Indic scripts, CJK, Arabic, etc.)
    non_ascii_ratio = sum(1 for c in text if ord(c) > 127) / max(len(text), 1)

    if non_ascii_ratio > 0.3:
        # Text is mostly non-Latin — extract any English/Latin portions
        latin_parts = _re.findall(r'[A-Za-z][A-Za-z\s,.\'-]{3,}', text)
        if latin_parts:
            cleaned = " | ".join(latin_parts[:5])
            return cleaned[:200]
        # No Latin text found — return a generic scene description
        return ""

    # Mostly ASCII — clean normally
    cleaned = _re.sub(r'[^\x20-\x7E]', ' ', text)
    cleaned = _re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def _extract_narration_for_display(prompt: str) -> str:
    """Extract clean narration text from a scene prompt.
    
    The prompt may contain raw visual_prompt data meant for AI generators.
    Extract just the human-readable narration portion.
    """
    # Remove style prefixes like "Cinematic scene: " 
    cleaned = re.sub(r'^[A-Za-z_\s]+scene:\s*', '', prompt, flags=re.IGNORECASE)
    # Remove JSON-like content
    cleaned = re.sub(r'\{[^}]*\}', '', cleaned)
    cleaned = re.sub(r'"[a-z_]+":\s*', '', cleaned)
    # Remove technical directives
    cleaned = re.sub(r'(?i)(camera|lens|depth of field|close-up|wide shot|dolly|tracking|pan)[^.]*\.?', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned[:200] if cleaned else prompt[:200]


class LocalProvider(VideoProvider):
    display_name = "Ominou Local"
    company = "Ominou Studio"
    strengths = ["no API keys needed", "offline generation", "fast rendering", "unlimited usage"]
    max_duration = 600
    supports_audio = False
    env_key = ""  # No key needed

    def is_available(self) -> bool:
        """Available if FFmpeg is installed."""
        import shutil
        return shutil.which("ffmpeg") is not None

    async def generate(
        self,
        prompt: str,
        duration_seconds: int = 5,
        resolution: str = "1080p",
        style: str = "cinematic",
        quality: str = "high",
        **kwargs,
    ) -> ProviderResult:
        storage = os.path.abspath(STORAGE_DIR)
        os.makedirs(storage, exist_ok=True)
        file_id = str(uuid.uuid4())[:8]
        filename = f"ominou_{file_id}.mp4"
        output_path = os.path.join(storage, filename)

        w, h = _RES.get(resolution, (1920, 1080))
        fps = 30 if quality == "ultra" else 24

        # Get palette
        scene_idx = kwargs.get("scene_number", 0)
        bg1, bg2, accent, text_color = _get_palette(style, scene_idx)

        # Extract clean display text from the prompt
        display_text = _extract_narration_for_display(prompt)
        display_text = _clean_text_for_ffmpeg(display_text)

        # If no displayable text (e.g., non-Latin script), use the raw visual prompt
        if not display_text or len(display_text) < 5:
            # Try the prompt directly (visual descriptions are often in English)
            display_text = _clean_text_for_ffmpeg(prompt)
        if not display_text or len(display_text) < 5:
            display_text = f"Scene {kwargs.get('scene_number', 1)}"

        # Scene number from kwargs or extract from prompt
        scene_num = kwargs.get("scene_number", 1)

        # Prepare text files for FFmpeg (avoids escaping issues)
        # Title: short scene label
        title_text = f"Scene {scene_num}"
        title_file = os.path.join(storage, f"title_{file_id}.txt")
        with open(title_file, "w", encoding="ascii", errors="replace") as f:
            f.write(title_text)

        # Narration display: wrapped cleanly
        narration_wrapped = textwrap.fill(display_text, width=50)
        narr_file = os.path.join(storage, f"narr_{file_id}.txt")
        with open(narr_file, "w", encoding="ascii", errors="replace") as f:
            f.write(narration_wrapped)

        # Watermark
        wm_file = os.path.join(storage, f"wm_{file_id}.txt")
        with open(wm_file, "w", encoding="ascii") as f:
            f.write("OMINOU STUDIO")

        # Use relative filenames (cwd set to storage to avoid Windows colon issues)
        tf = f"title_{file_id}.txt"
        nf = f"narr_{file_id}.txt"
        wf = f"wm_{file_id}.txt"

        # Font sizes scaled to resolution
        title_size = min(w // 18, 64)
        narr_size = min(w // 35, 36)
        wm_size = min(w // 55, 24)

        # ── Build FFmpeg filter for cinematic animated scene ──
        # 1. Animated gradient background (two color sources blended)
        # 2. Subtle noise overlay for film grain texture
        # 3. Ken Burns slow zoom effect
        # 4. Scene title at top
        # 5. Narration text as lower-third with background box
        # 6. Watermark
        # 7. Vignette + fade in/out

        dur = max(duration_seconds, 2)

        # Use -filter_complex with multiple color inputs for gradient blend
        filter_complex = (
            # Gradient background: blend two colors over time
            f"color=c='{bg1}':s={w}x{h}:d={dur}:r={fps}[bg1];"
            f"color=c='{bg2}':s={w}x{h}:d={dur}:r={fps}[bg2];"
            f"[bg1][bg2]blend=all_expr='A*(1-T/{dur})+B*(T/{dur})'[bg];"
            # Film grain
            f"[bg]noise=c0s=8:c0f=t:allf=t[textured];"
            # Ken Burns zoom
            f"[textured]zoompan=z='1+0.04*on/{dur * fps}'"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={dur * fps}:s={w}x{h}:fps={fps}[zoomed];"
            # Scene title at top center
            f"[zoomed]drawtext=textfile='{tf}':"
            f"fontsize={title_size}:"
            f"fontcolor={text_color}:"
            f"x=(w-text_w)/2:y=h*0.12:"
            f"shadowcolor=black@0.7:shadowx=3:shadowy=3[titled];"
            # Narration lower-third with dark box
            f"[titled]drawtext=textfile='{nf}':"
            f"fontsize={narr_size}:"
            f"fontcolor={text_color}:"
            f"x=(w-text_w)/2:y=h*0.62:"
            f"box=1:boxcolor=black@0.6:boxborderw=20:"
            f"shadowcolor=black@0.5:shadowx=2:shadowy=2:"
            f"line_spacing=12[narrated];"
            # Watermark
            f"[narrated]drawtext=textfile='{wf}':"
            f"fontsize={wm_size}:"
            f"fontcolor=white@0.3:"
            f"x=(w-text_w)/2:y=h-40[wm];"
            # Vignette
            f"[wm]vignette=PI/4[vig];"
            # Fade in/out
            f"[vig]fade=t=in:st=0:d=1,fade=t=out:st={max(0, dur - 1)}:d=1[out]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:v", "libx264",
            "-preset", "fast" if quality == "standard" else "medium",
            "-crf", "23" if quality == "standard" else "18" if quality == "ultra" else "20",
            "-pix_fmt", "yuv420p",
            "-t", str(dur),
            filename,
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=storage,
            )
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=180)

            # Clean up temp text files
            for tmp in (title_file, narr_file, wm_file):
                try:
                    os.remove(tmp)
                except OSError:
                    pass

            if proc.returncode != 0:
                err_msg = stderr.decode()[-500:] if stderr else "Unknown FFmpeg error"
                logger.error("FFmpeg failed: %s", err_msg)
                # Fall back to simple generation if complex filter fails
                return await self._generate_simple(
                    prompt, duration_seconds, resolution, style, quality,
                    storage, file_id, filename, output_path, w, h, fps,
                    bg1, display_text, text_color,
                )

            file_url = f"/storage/videos/{filename}"
            return ProviderResult(
                status="completed",
                scene_file=output_path,
                file_url=file_url,
                duration_seconds=duration_seconds,
                resolution=resolution,
                has_audio=False,
                provider="ominou_local",
            )

        except asyncio.TimeoutError:
            return ProviderResult(
                status="failed",
                error="Local generation timed out (180s limit)",
                provider="ominou_local",
            )
        except Exception as e:
            logger.error("Local generation error: %s", e)
            return await self._generate_simple(
                prompt, duration_seconds, resolution, style, quality,
                storage, file_id, filename, output_path, w, h, fps,
                bg1, display_text, text_color,
            )

    async def _generate_simple(
        self,
        prompt: str,
        duration_seconds: int,
        resolution: str,
        style: str,
        quality: str,
        storage: str,
        file_id: str,
        filename: str,
        output_path: str,
        w: int,
        h: int,
        fps: int,
        bg_color: str,
        display_text: str,
        text_color: str,
    ) -> ProviderResult:
        """Simple fallback: gradient bg + centered narration text + fade."""
        logger.info("Using simple fallback generator")

        narr_wrapped = textwrap.fill(display_text, width=45)
        text_file = os.path.join(storage, f"simple_{file_id}.txt")
        with open(text_file, "w", encoding="ascii", errors="replace") as f:
            f.write(narr_wrapped)

        wm_file = os.path.join(storage, f"swm_{file_id}.txt")
        with open(wm_file, "w", encoding="ascii") as f:
            f.write("OMINOU STUDIO") 

        tf_rel = f"simple_{file_id}.txt"
        wf_rel = f"swm_{file_id}.txt"

        font_size = min(w // 30, 42)
        wm_size = min(w // 55, 22)

        vf = (
            f"drawtext=textfile='{tf_rel}':"
            f"fontsize={font_size}:"
            f"fontcolor={text_color}:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"box=1:boxcolor=black@0.5:boxborderw=16:"
            f"shadowcolor=black@0.6:shadowx=2:shadowy=2:"
            f"line_spacing=10,"
            f"drawtext=textfile='{wf_rel}':"
            f"fontsize={wm_size}:"
            f"fontcolor=white@0.3:"
            f"x=(w-text_w)/2:y=h-50,"
            f"fade=t=in:st=0:d=1,fade=t=out:st={max(0, duration_seconds - 1)}:d=1"
        )

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c={bg_color}:s={w}x{h}:d={duration_seconds}:r={fps}",
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-t", str(duration_seconds),
            filename,
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=storage,
            )
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

            for tmp in (text_file, wm_file):
                try:
                    os.remove(tmp)
                except OSError:
                    pass

            if proc.returncode != 0:
                err_msg = stderr.decode()[-300:] if stderr else "Unknown"
                return ProviderResult(
                    status="failed",
                    error=f"Simple generation failed: {err_msg}",
                    provider="ominou_local",
                )

            return ProviderResult(
                status="completed",
                scene_file=output_path,
                file_url=f"/storage/videos/{filename}",
                duration_seconds=duration_seconds,
                resolution=resolution,
                has_audio=False,
                provider="ominou_local",
            )
        except Exception as e:
            return ProviderResult(
                status="failed",
                error=f"Simple generation error: {e}",
                provider="ominou_local",
            )
