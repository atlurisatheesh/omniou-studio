"""Video Stitcher — Combines scene clips, narration, and music into a final video using FFmpeg.

Fault-tolerant: checks FFmpeg availability, handles missing files gracefully,
provides clear error messages for each failure mode.
"""
import asyncio
import os
import uuid
import json
import shutil
import logging
import tempfile
from typing import Optional

logger = logging.getLogger("ominou.stitcher")

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "videos")
FINAL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "final")

# Quality tier presets: (CRF, preset, audio bitrate)
QUALITY_PRESETS = {
    "standard": (23, "fast", "128k"),
    "high": (18, "medium", "192k"),
    "ultra": (12, "slow", "320k"),
}

RESOLUTION_MAP = {
    "720p": "1280:720",
    "1080p": "1920:1080",
    "1440p": "2560:1440",
    "4K": "3840:2160",
}


async def _ensure_dirs():
    os.makedirs(STORAGE_DIR, exist_ok=True)
    os.makedirs(FINAL_DIR, exist_ok=True)


async def _run_ffmpeg(cmd: list[str]) -> tuple[int, str, str]:
    """Run an FFmpeg command asynchronously."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return process.returncode, stdout.decode(), stderr.decode()


async def stitch_scenes(
    scene_files: list[str],
    transitions: list[str],
    narration_files: Optional[list[Optional[str]]] = None,
    music_file: Optional[str] = None,
    output_resolution: str = "1920x1080",
    output_fps: int = 24,
    quality: str = "high",
) -> dict:
    """Stitch multiple scene video clips into a single cohesive video.
    
    1. Verify FFmpeg is available
    2. Concatenate scene clips with transitions
    3. Overlay narration audio (per-scene timing)
    4. Mix in background music at lower volume
    5. Output final polished video
    """
    if not shutil.which("ffmpeg"):
        return {"status": "failed", "error": "FFmpeg is not installed. Install from https://ffmpeg.org/download.html"}

    await _ensure_dirs()

    # Filter out failed scenes
    valid_scenes = [f for f in scene_files if f and os.path.exists(f)]
    if not valid_scenes:
        return {"status": "failed", "error": "No valid scene files to stitch"}

    file_id = str(uuid.uuid4())[:12]
    final_filename = f"final_{file_id}.mp4"
    final_path = os.path.join(FINAL_DIR, final_filename)

    # Step 1: Create concat file for FFmpeg
    concat_path = os.path.join(STORAGE_DIR, f"concat_{file_id}.txt")
    with open(concat_path, "w") as f:
        for scene_file in valid_scenes:
            escaped = scene_file.replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")

    # Step 2: Concatenate scenes with quality-tier encoding
    concat_output = os.path.join(STORAGE_DIR, f"concat_{file_id}.mp4")
    crf, preset, audio_bitrate = QUALITY_PRESETS.get(quality, QUALITY_PRESETS["high"])

    # Map output_resolution (e.g. "1080p" or "1920x1080") to FFmpeg scale
    scale_value = RESOLUTION_MAP.get(output_resolution)
    if not scale_value and "x" in output_resolution:
        scale_value = output_resolution.replace("x", ":")

    # Build video filter chain
    vf_filters = []
    if scale_value:
        vf_filters.append(f"scale={scale_value}:force_original_aspect_ratio=decrease,pad={scale_value}:(ow-iw)/2:(oh-ih)/2")

    # Ultra quality: add cinematic post-processing (subtle film grain + vignette)
    if quality == "ultra":
        # Subtle film grain via noise filter (strength 4, temporal flagged for natural look)
        vf_filters.append("noise=c0s=4:c0f=t")
        # Subtle lens vignette effect
        vf_filters.append("vignette=PI/5")

    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_path,
        "-c:v", "libx264", "-preset", preset,
        "-crf", str(crf),
        "-r", str(output_fps),
        "-pix_fmt", "yuv420p",
    ]
    if vf_filters:
        concat_cmd.extend(["-vf", ",".join(vf_filters)])
    concat_cmd.append(concat_output)
    rc, _, stderr = await _run_ffmpeg(concat_cmd)
    if rc != 0:
        return {"status": "failed", "error": f"Concatenation failed: {stderr[:500]}"}

    # Step 3: Mix audio tracks
    final_video = concat_output
    
    if narration_files or music_file:
        audio_inputs = []
        filter_parts = []
        audio_idx = 1  # 0 is video

        cmd = ["ffmpeg", "-y", "-i", concat_output]

        # Add narration files and concatenate them
        valid_narrations = [n for n in (narration_files or []) if n and os.path.exists(n)]
        if valid_narrations:
            # Concatenate narration files first
            narr_concat = os.path.join(STORAGE_DIR, f"narr_{file_id}.txt")
            with open(narr_concat, "w") as f:
                for nf in valid_narrations:
                    escaped = nf.replace("'", "'\\''")
                    f.write(f"file '{escaped}'\n")

            narr_combined = os.path.join(STORAGE_DIR, f"narr_{file_id}.mp3")
            narr_cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", narr_concat, "-c:a", "libmp3lame", narr_combined,
            ]
            await _run_ffmpeg(narr_cmd)

            if os.path.exists(narr_combined):
                cmd.extend(["-i", narr_combined])
                filter_parts.append(f"[{audio_idx}:a]volume=1.0[narr]")
                audio_idx += 1

        if music_file and os.path.exists(music_file):
            cmd.extend(["-i", music_file])
            filter_parts.append(f"[{audio_idx}:a]volume=0.3[bgm]")  # Music at 30% volume
            audio_idx += 1

        if filter_parts:
            # Build audio mix filter
            mix_inputs = ""
            if "[narr]" in " ".join(filter_parts):
                mix_inputs += "[narr]"
            if "[bgm]" in " ".join(filter_parts):
                mix_inputs += "[bgm]"

            n_audio = mix_inputs.count("[")
            if n_audio > 1:
                filter_complex = ";".join(filter_parts) + f";{mix_inputs}amix=inputs={n_audio}:duration=longest[aout]"
                cmd.extend(["-filter_complex", filter_complex, "-map", "0:v", "-map", "[aout]"])
            elif n_audio == 1:
                out_label = "narr" if "[narr]" in mix_inputs else "bgm"
                filter_complex = ";".join(filter_parts)
                cmd.extend(["-filter_complex", filter_complex, "-map", "0:v", "-map", f"[{out_label}]"])
            
            cmd.extend([
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", audio_bitrate,
                "-shortest",
                final_path,
            ])
            
            rc, _, stderr = await _run_ffmpeg(cmd)
            if rc == 0:
                final_video = final_path
        else:
            # No audio to mix, just use concat output
            os.rename(concat_output, final_path)
            final_video = final_path
    else:
        os.rename(concat_output, final_path)
        final_video = final_path

    # Get file info
    file_size = os.path.getsize(final_video) if os.path.exists(final_video) else 0

    # Clean up temp files
    for temp in [concat_path]:
        if os.path.exists(temp):
            os.remove(temp)

    return {
        "video_file": final_video,
        "file_url": f"/storage/final/{final_filename}",
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "scenes_stitched": len(valid_scenes),
        "has_narration": bool(narration_files),
        "has_music": bool(music_file),
        "quality": quality,
        "resolution": output_resolution,
        "status": "completed",
    }


async def get_video_duration(filepath: str) -> float:
    """Get the duration of a video file using FFprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", filepath,
    ]
    rc, stdout, _ = await _run_ffmpeg(cmd)
    if rc == 0:
        info = json.loads(stdout)
        return float(info.get("format", {}).get("duration", 0))
    return 0.0
