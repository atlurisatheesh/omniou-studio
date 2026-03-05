"""
CLONEAI PRO — Face Enhancement Service (GFPGAN)
================================================
Automatic face restoration and enhancement for generated video frames.
Uses GFPGAN v1.4 for 2x/4x face sharpening.
"""

import asyncio
import time
import uuid
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import structlog

logger = structlog.get_logger()

OUTPUT_DIR = Path("outputs")


class EnhanceService:
    """
    Face enhancement service using GFPGAN v1.4.
    
    Enhances generated face frames to improve:
    - Face sharpness and detail
    - Skin texture
    - Eye and teeth clarity
    - Overall photorealism
    """

    def __init__(self, device: str = "cuda", model_cache_dir: str = "./models"):
        self.device = device
        self.model_cache_dir = model_cache_dir
        self.enhancer = None

    async def _ensure_model_loaded(self):
        """Load GFPGAN model if not loaded."""
        if self.enhancer is not None:
            return self.enhancer

        def _load():
            logger.info("enhance.loading_model", model="gfpgan_v1.4")
            try:
                from gfpgan import GFPGANer
                import torch

                model_path = Path(self.model_cache_dir) / "gfpgan" / "GFPGANv1.4.pth"
                
                if not model_path.exists():
                    logger.warning("enhance.model_not_found", path=str(model_path))
                    # Try auto-download
                    model_path = "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth"

                enhancer = GFPGANer(
                    model_path=str(model_path),
                    upscale=2,
                    arch="clean",
                    channel_multiplier=2,
                    bg_upsampler=None,
                    device=torch.device(self.device if torch.cuda.is_available() else "cpu"),
                )
                logger.info("enhance.model_loaded")
                return enhancer
            except ImportError:
                logger.warning("enhance.gfpgan_not_installed", msg="GFPGAN not installed, using fallback")
                return None

        self.enhancer = await asyncio.to_thread(_load)
        return self.enhancer

    async def enhance_frame(self, frame: np.ndarray) -> np.ndarray:
        """Enhance a single frame using GFPGAN."""
        enhancer = await self._ensure_model_loaded()
        if enhancer is None:
            return self._fallback_enhance(frame)

        def _enhance():
            try:
                _, _, output = enhancer.enhance(
                    frame,
                    has_aligned=False,
                    only_center_face=True,
                    paste_back=True,
                )
                return output
            except Exception as e:
                logger.error("enhance.frame_failed", error=str(e))
                return frame

        return await asyncio.to_thread(_enhance)

    async def enhance_video(
        self,
        video_path: str,
        output_dir: Optional[str] = None,
        skip_frames: int = 0,
    ) -> Path:
        """
        Enhance all face frames in a video.
        
        Args:
            video_path: Input video path
            output_dir: Output directory
            skip_frames: Skip enhancement every N frames (for speed)
            
        Returns:
            Path to enhanced video
        """
        start_time = time.time()
        logger.info("enhance.video_start", input=video_path)

        enhancer = await self._ensure_model_loaded()
        out_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        def _enhance_all():
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video: {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # For GFPGAN with upscale=2, output will be 2x
            out_w, out_h = w * 2, h * 2
            if enhancer is None:
                out_w, out_h = w, h

            output_path = out_dir / "enhanced_video.mp4"
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(output_path), fourcc, fps, (out_w, out_h))

            frame_idx = 0
            last_enhanced = None

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if enhancer and (skip_frames == 0 or frame_idx % (skip_frames + 1) == 0):
                    try:
                        _, _, enhanced = enhancer.enhance(
                            frame, has_aligned=False, only_center_face=True, paste_back=True
                        )
                        last_enhanced = enhanced
                    except Exception:
                        enhanced = cv2.resize(frame, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
                        last_enhanced = enhanced
                elif last_enhanced is not None:
                    enhanced = last_enhanced  # Reuse last enhanced frame for skipped frames
                else:
                    enhanced = cv2.resize(frame, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)

                writer.write(enhanced)
                frame_idx += 1

                if frame_idx % 50 == 0:
                    logger.info("enhance.progress", frame=frame_idx, total=total_frames)

            cap.release()
            writer.release()
            return output_path

        result = await asyncio.to_thread(_enhance_all)

        elapsed = time.time() - start_time
        logger.info("enhance.video_complete", output=str(result), time_seconds=round(elapsed, 2))

        return result

    def _fallback_enhance(self, frame: np.ndarray) -> np.ndarray:
        """Simple fallback enhancement without GFPGAN (sharpening + contrast)."""
        # Unsharp mask
        blurred = cv2.GaussianBlur(frame, (0, 0), 3)
        sharpened = cv2.addWeighted(frame, 1.5, blurred, -0.5, 0)

        # Slight contrast boost via CLAHE
        lab = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        return enhanced
