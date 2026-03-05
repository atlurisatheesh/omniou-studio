"""
CLONEAI ULTRA — Cinematic Post-Processing Pipeline (Section 5)
===============================================================
7-layer "secret sauce" that makes AI-generated video indistinguishable
from real footage.  Every layer is independently togglable via config.

Layers:
  1. Micro-jitter          — sub-pixel random translation to break grid patterns
  2. Film grain            — organic photon noise overlay
  3. Barrel lens distortion — subtle radial warp mimicking real optics
  4. Depth-of-field blur   — face stays sharp, background gets bokeh
  5. Cinematic color grade  — filmic tone / 3-strip LUT-style color
  6. Audio post-processing — room reverb, breath normalization, EQ
  7. Final mux + encode    — combine processed video + audio via FFmpeg
"""

import asyncio
import math
import subprocess
import time
import uuid
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import structlog

from ..config import settings

logger = structlog.get_logger()

OUTPUT_DIR = Path("outputs")


# ─────────────────────────────────────────────────
# Layer Implementations
# ─────────────────────────────────────────────────

def apply_microjitter(frame: np.ndarray, max_px: float = 2.0, rng: np.random.Generator | None = None) -> np.ndarray:
    """Layer 1: Sub-pixel random translation to destroy AI grid artifacts."""
    if rng is None:
        rng = np.random.default_rng()
    dx = rng.uniform(-max_px, max_px)
    dy = rng.uniform(-max_px, max_px)
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(frame, M, (frame.shape[1], frame.shape[0]),
                          flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)


def apply_film_grain(frame: np.ndarray, intensity: float = 0.08, rng: np.random.Generator | None = None) -> np.ndarray:
    """Layer 2: Organic photon noise overlay (luminance-aware)."""
    if rng is None:
        rng = np.random.default_rng()
    h, w = frame.shape[:2]
    # Generate noise at half-res and upscale for more organic look
    half_h, half_w = max(1, h // 2), max(1, w // 2)
    noise_small = rng.normal(0, 1, (half_h, half_w)).astype(np.float32)
    noise = cv2.resize(noise_small, (w, h), interpolation=cv2.INTER_LINEAR)
    # Scale by luminance — grain is more visible in mid-tones
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    luminance_mask = 4.0 * gray * (1.0 - gray)  # parabola peaking at 0.5
    grain = (noise * luminance_mask * intensity * 255).astype(np.float32)
    result = np.clip(frame.astype(np.float32) + grain[:, :, np.newaxis], 0, 255).astype(np.uint8)
    return result


def apply_barrel_distortion(frame: np.ndarray, strength: float = 0.0003) -> np.ndarray:
    """Layer 3: Subtle barrel lens distortion mimicking a real camera lens."""
    h, w = frame.shape[:2]
    fx = fy = max(w, h)
    cx, cy = w / 2.0, h / 2.0
    camera_matrix = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], dtype=np.float64)
    # Negative k1 → barrel distortion
    dist_coeffs = np.array([-strength, 0, 0, 0, 0], dtype=np.float64)
    new_cam, _ = cv2.getOptimalNewCameraMatrix(camera_matrix, dist_coeffs, (w, h), 0, (w, h))
    map1, map2 = cv2.initUndistortRectifyMap(camera_matrix, dist_coeffs, None, new_cam, (w, h), cv2.CV_32FC1)
    return cv2.remap(frame, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)


def apply_depth_of_field(frame: np.ndarray, face_cascade=None) -> np.ndarray:
    """Layer 4: Depth-of-field — face stays sharp, background gets bokeh."""
    h, w = frame.shape[:2]

    # Detect face region to keep sharp
    if face_cascade is None:
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

    if len(faces) == 0:
        # No face detected — apply very subtle uniform blur
        return cv2.GaussianBlur(frame, (3, 3), 0.5)

    # Create a soft mask: 1.0 for face region, 0.0 for background
    mask = np.zeros((h, w), dtype=np.float32)
    for (x, y, fw, fh) in faces:
        # Expand face region by 30% for natural look
        pad_x = int(fw * 0.3)
        pad_y = int(fh * 0.3)
        x1, y1 = max(0, x - pad_x), max(0, y - pad_y)
        x2, y2 = min(w, x + fw + pad_x), min(h, y + fh + pad_y)
        mask[y1:y2, x1:x2] = 1.0

    # Heavy Gaussian blur on the mask edges for smooth transition
    mask = cv2.GaussianBlur(mask, (0, 0), sigmaX=max(w, h) * 0.04)
    mask = np.clip(mask, 0, 1)

    # Bokeh-like background blur (large kernel)
    ksize = max(15, (min(w, h) // 30) | 1)  # ensure odd
    blurred = cv2.GaussianBlur(frame, (ksize, ksize), 0)

    # Blend: sharp face + blurred background
    mask_3c = mask[:, :, np.newaxis]
    result = (frame.astype(np.float32) * mask_3c + blurred.astype(np.float32) * (1.0 - mask_3c))
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_color_grade(frame: np.ndarray) -> np.ndarray:
    """Layer 5: Cinematic color grading — warm highlights, cool shadows, lifted blacks."""
    # Convert to float
    img = frame.astype(np.float32) / 255.0

    # Split channels
    b, g, r = cv2.split(img)

    # Lift blacks (raise minimum)
    lift = 0.03
    b = np.clip(b + lift, 0, 1)
    g = np.clip(g + lift, 0, 1)
    r = np.clip(r + lift, 0, 1)

    # Warm highlights (boost red/green in bright areas)
    highlights = np.clip((b + g + r) / 3.0 - 0.5, 0, 0.5) * 2.0  # 0 in shadows, 1 in highlights
    r = np.clip(r + highlights * 0.03, 0, 1)
    g = np.clip(g + highlights * 0.01, 0, 1)

    # Cool shadows (boost blue in dark areas)
    shadows = 1.0 - highlights
    b = np.clip(b + shadows * 0.02, 0, 1)

    # Subtle S-curve for contrast (sigmoid approximation)
    merged = cv2.merge([b, g, r])
    # Soft contrast: midtone contrast boost
    merged = np.clip(0.5 + (merged - 0.5) * 1.08, 0, 1)

    # Slight desaturation for filmic look
    gray = np.mean(merged, axis=2, keepdims=True)
    merged = np.clip(merged * 0.92 + gray * 0.08, 0, 1)

    return (merged * 255).astype(np.uint8)


def apply_audio_postprocess(audio_path: str, output_path: str) -> str:
    """
    Layer 6: Audio post-processing via FFmpeg filters.
    
    - Room reverb (subtle)
    - High-pass filter (remove rumble)
    - Breath / volume normalization (loudnorm)
    - Slight EQ for presence
    """
    try:
        # FFmpeg audio filter chain:
        # 1. aecho — subtle room reverb (0.8 gain, 0.7 decay, 40ms delay)
        # 2. highpass — remove sub-60Hz rumble
        # 3. equalizer — boost 2-4kHz for vocal presence
        # 4. loudnorm — EBU R128 loudness normalization
        filter_chain = (
            "highpass=f=60,"
            "aecho=0.8:0.7:40:0.3,"
            "equalizer=f=3000:t=q:w=1.5:g=2,"
            "loudnorm=I=-16:LRA=11:TP=-1.5"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", audio_path,
            "-af", filter_chain,
            "-c:a", "aac",
            "-b:a", "192k",
            output_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        logger.info("postprocess.audio_complete", output=output_path)
        return output_path
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logger.warning("postprocess.audio_fallback", error=str(e))
        # Fallback: just copy original
        import shutil
        shutil.copy2(audio_path, output_path)
        return output_path


# ─────────────────────────────────────────────────
# Main Post-Processing Orchestrator
# ─────────────────────────────────────────────────

class PostProcessService:
    """
    7-layer cinematic post-processing pipeline.

    All layers are independently togglable via config flags.
    """

    def __init__(self):
        self.face_cascade = None
        self._rng = np.random.default_rng(seed=42)

    def _get_face_cascade(self):
        if self.face_cascade is None:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
        return self.face_cascade

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Apply all enabled visual post-processing layers to a single frame."""
        result = frame

        # Layer 1: Micro-jitter
        if settings.ENABLE_MICROJITTER:
            result = apply_microjitter(result, max_px=settings.JITTER_MAX_PX, rng=self._rng)

        # Layer 2: Film grain
        if settings.ENABLE_FILM_GRAIN:
            result = apply_film_grain(result, intensity=settings.GRAIN_INTENSITY, rng=self._rng)

        # Layer 3: Barrel lens distortion
        if settings.ENABLE_LENS_DISTORTION:
            result = apply_barrel_distortion(result, strength=0.0003)

        # Layer 4: Depth of field
        if settings.ENABLE_DOF:
            result = apply_depth_of_field(result, face_cascade=self._get_face_cascade())

        # Layer 5: Cinematic color grade
        if settings.ENABLE_COLOR_GRADE:
            result = apply_color_grade(result)

        return result

    async def process_video(
        self,
        video_path: str,
        audio_path: str,
        output_dir: str,
        job_id: str = "",
    ) -> dict:
        """
        Process an entire video through the 7-layer pipeline.

        Args:
            video_path: Input video (enhanced or raw)
            audio_path: Cloned audio (WAV)
            output_dir: Directory for output files
            job_id: For logging

        Returns:
            dict with processed_video and processed_audio paths
        """
        start_time = time.time()
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "postprocess.start",
            job_id=job_id,
            layers={
                "microjitter": settings.ENABLE_MICROJITTER,
                "film_grain": settings.ENABLE_FILM_GRAIN,
                "lens_distortion": settings.ENABLE_LENS_DISTORTION,
                "dof": settings.ENABLE_DOF,
                "color_grade": settings.ENABLE_COLOR_GRADE,
                "audio_post": settings.ENABLE_AUDIO_POST,
            },
        )

        # ── Visual layers (1-5): process video frames ──
        processed_video = out_dir / "postprocessed_video.mp4"

        any_visual = (
            settings.ENABLE_MICROJITTER
            or settings.ENABLE_FILM_GRAIN
            or settings.ENABLE_LENS_DISTORTION
            or settings.ENABLE_DOF
            or settings.ENABLE_COLOR_GRADE
        )

        if any_visual:
            processed_video = await asyncio.to_thread(
                self._process_video_frames, video_path, str(processed_video), job_id
            )
        else:
            # No visual layers enabled — pass through
            import shutil
            shutil.copy2(video_path, str(processed_video))
            logger.info("postprocess.visual_skip", job_id=job_id, reason="all visual layers disabled")

        # ── Audio layer (6): post-process audio ──
        processed_audio = str(out_dir / "postprocessed_audio.aac")
        if settings.ENABLE_AUDIO_POST:
            processed_audio = await asyncio.to_thread(
                apply_audio_postprocess, audio_path, processed_audio
            )
        else:
            import shutil
            shutil.copy2(audio_path, processed_audio)
            logger.info("postprocess.audio_skip", job_id=job_id)

        # ── Layer 7: Final mux + encode ──
        final_path = str(out_dir / "postprocessed_final.mp4")
        final_path = await asyncio.to_thread(
            self._final_mux, str(processed_video), processed_audio, final_path
        )

        elapsed = time.time() - start_time
        logger.info(
            "postprocess.complete",
            job_id=job_id,
            time_seconds=round(elapsed, 2),
            output=final_path,
        )

        return {
            "processed_video": str(processed_video),
            "processed_audio": processed_audio,
            "final_output": final_path,
            "time_seconds": round(elapsed, 2),
        }

    def _process_video_frames(self, video_path: str, output_path: str, job_id: str = "") -> str:
        """Process all frames through visual layers 1-5."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

        idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            processed = self.process_frame(frame)

            # Ensure output size matches (safety)
            if processed.shape[:2] != (h, w):
                processed = cv2.resize(processed, (w, h), interpolation=cv2.INTER_LANCZOS4)

            writer.write(processed)
            idx += 1

            if idx % 100 == 0:
                logger.info("postprocess.frame_progress", job_id=job_id, frame=idx, total=total_frames)

        cap.release()
        writer.release()

        logger.info("postprocess.frames_done", job_id=job_id, frames_processed=idx)
        return output_path

    def _final_mux(self, video_path: str, audio_path: str, output_path: str) -> str:
        """Layer 7: Mux processed video + audio into final H.264 MP4."""
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "libx264",
                "-preset", "slow",
                "-crf", "18",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_path,
            ]
            subprocess.run(cmd, check=True, capture_output=True, timeout=300)
            logger.info("postprocess.mux_complete", output=output_path)
            return output_path
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            logger.warning("postprocess.mux_fallback", error=str(e))
            import shutil
            shutil.copy2(video_path, output_path)
            return output_path
