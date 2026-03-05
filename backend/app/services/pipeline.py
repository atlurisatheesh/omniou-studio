"""
CLONEAI ULTRA — Pipeline Orchestrator
=======================================
Orchestrates the full 7-stage clone generation pipeline:
  1. Voice Clone  → cloned_voice.wav
  2. Face Animate → animated_face.mp4
  3. Lip Sync     → synced_video.mp4
  4. Enhancement  → enhanced_video.mp4
  5. Post-Process → cinematic_final.mp4   (7-layer secret sauce)
  6. Quality Gate → pass / fail / retry
  7. Final Encode → delivery-ready MP4

Manages progress tracking, error recovery, and quality feedback loop.
"""

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Callable, Optional

import structlog

from ..config import settings

logger = structlog.get_logger()

OUTPUT_DIR = Path("outputs")


class PipelineOrchestrator:
    """
    Orchestrates the complete ULTRA clone generation pipeline.

    Pipeline stages:
      1. Voice Clone (Chatterbox/XTTS)  → cloned_voice.wav       [15-20s]
      2. Face Animation (LivePortrait)   → animated_face.mp4       [40-60s]
      3. Lip Sync (MuseTalk/LatentSync)  → synced_video.mp4        [30-45s]
      4. Enhancement (GFPGAN)            → enhanced_video.mp4      [15-30s]
      5. Post-Processing (7-layer)       → postprocessed_final.mp4 [10-20s]
      6. Quality Check (3-gate)          → pass/fail               [5-10s]
      7. Final Encode (FFmpeg)           → final_output.mp4        [5-10s]
    """

    # Stage weights for progress calculation (must sum to 100)
    STAGE_WEIGHTS = {
        "voice_cloning": 15,
        "face_animating": 25,
        "lip_syncing": 15,
        "enhancing": 12,
        "postprocessing": 13,
        "quality_check": 10,
        "encoding": 10,
    }

    MAX_QUALITY_RETRIES = 1  # How many times to retry on quality failure

    def __init__(
        self,
        device: str = "cuda",
        model_cache_dir: str = "./models",
        progress_callback: Optional[Callable] = None,
    ):
        self.device = device
        self.model_cache_dir = model_cache_dir
        self.progress_callback = progress_callback

    async def run(
        self,
        job_id: str,
        photo_path: str,
        voice_path: str,
        script_text: str,
        target_language: str = "en",
        emotion: str = "neutral",
        background: str = "original",
        skip_lip_sync: bool = False,
        skip_enhance: bool = False,
        skip_postprocess: bool = False,
        skip_quality_check: bool = False,
    ) -> dict:
        """
        Run the complete ULTRA clone generation pipeline.

        Args:
            job_id: Unique job identifier
            photo_path: Path to face photo
            voice_path: Path to voice sample
            script_text: Text for the clone to speak
            target_language: ISO language code
            emotion: Emotion tag (neutral, happy, sad, angry, etc.)
            background: Background mode (original, blur, office, studio, etc.)
            skip_lip_sync: Skip lip sync refinement (faster)
            skip_enhance: Skip face enhancement (faster)
            skip_postprocess: Skip cinematic post-processing
            skip_quality_check: Skip quality gates

        Returns:
            dict with output paths, quality scores, and metadata
        """
        start_time = time.time()
        job_dir = OUTPUT_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "pipeline.start",
            job_id=job_id,
            language=target_language,
            emotion=emotion,
            background=background,
            script_length=len(script_text),
        )

        result = {
            "job_id": job_id,
            "status": "processing",
            "stages": {},
        }

        try:
            # ────────────────────────────────────────────
            # STAGE 1: Voice Cloning
            # ────────────────────────────────────────────
            await self._update_progress(job_id, "voice_cloning", 0)

            from .voice_clone import VoiceCloneService
            voice_service = VoiceCloneService(
                device=self.device,
                model_cache_dir=self.model_cache_dir,
            )

            cloned_audio_path = await voice_service.clone_voice(
                voice_sample_path=voice_path,
                text=script_text,
                language=target_language,
                emotion=emotion,
                output_dir=str(job_dir),
            )

            result["stages"]["voice_clone"] = {
                "status": "completed",
                "output": str(cloned_audio_path),
            }
            await self._update_progress(job_id, "voice_cloning", 100)

            # ────────────────────────────────────────────
            # STAGE 2: Face Animation
            # ────────────────────────────────────────────
            await self._update_progress(job_id, "face_animating", 0)

            from .face_animate import FaceAnimateService
            face_service = FaceAnimateService(
                device=self.device,
                model_cache_dir=self.model_cache_dir,
            )

            animated_video_path = await face_service.animate(
                photo_path=photo_path,
                audio_path=str(cloned_audio_path),
                output_dir=str(job_dir),
                job_id=job_id,
            )

            result["stages"]["face_animate"] = {
                "status": "completed",
                "output": str(animated_video_path),
            }
            await self._update_progress(job_id, "face_animating", 100)

            # ────────────────────────────────────────────
            # STAGE 3: Lip Sync Refinement (Optional)
            # ────────────────────────────────────────────
            current_video = animated_video_path

            if not skip_lip_sync:
                await self._update_progress(job_id, "lip_syncing", 0)

                from .lip_sync import LipSyncService
                lip_service = LipSyncService(
                    device=self.device,
                    model_cache_dir=self.model_cache_dir,
                )

                synced_video_path = await lip_service.sync(
                    video_path=str(animated_video_path),
                    audio_path=str(cloned_audio_path),
                    output_dir=str(job_dir),
                )

                current_video = synced_video_path
                result["stages"]["lip_sync"] = {
                    "status": "completed",
                    "output": str(synced_video_path),
                }
            else:
                result["stages"]["lip_sync"] = {"status": "skipped"}

            await self._update_progress(job_id, "lip_syncing", 100)

            # ────────────────────────────────────────────
            # STAGE 4: Face Enhancement (Optional)
            # ────────────────────────────────────────────
            if not skip_enhance:
                await self._update_progress(job_id, "enhancing", 0)

                from .enhance import EnhanceService
                enhance_service = EnhanceService(
                    device=self.device,
                    model_cache_dir=self.model_cache_dir,
                )

                enhanced_video_path = await enhance_service.enhance_video(
                    video_path=str(current_video),
                    output_dir=str(job_dir),
                    skip_frames=1,
                )

                current_video = enhanced_video_path
                result["stages"]["enhance"] = {
                    "status": "completed",
                    "output": str(enhanced_video_path),
                }
            else:
                result["stages"]["enhance"] = {"status": "skipped"}

            await self._update_progress(job_id, "enhancing", 100)

            # ────────────────────────────────────────────
            # STAGE 5: Post-Processing (7-layer cinematic)
            # ────────────────────────────────────────────
            if not skip_postprocess:
                await self._update_progress(job_id, "postprocessing", 0)

                from .postprocess import PostProcessService
                pp_service = PostProcessService()

                pp_result = await pp_service.process_video(
                    video_path=str(current_video),
                    audio_path=str(cloned_audio_path),
                    output_dir=str(job_dir),
                    job_id=job_id,
                )

                current_video = pp_result["final_output"]
                cloned_audio_path = pp_result["processed_audio"]

                result["stages"]["postprocess"] = {
                    "status": "completed",
                    "output": pp_result["final_output"],
                    "time_seconds": pp_result["time_seconds"],
                }
            else:
                result["stages"]["postprocess"] = {"status": "skipped"}

            await self._update_progress(job_id, "postprocessing", 100)

            # ────────────────────────────────────────────
            # STAGE 6: Quality Check (3-gate)
            # ────────────────────────────────────────────
            quality_result = None
            if not skip_quality_check:
                await self._update_progress(job_id, "quality_check", 0)

                from .quality_checker import QualityChecker
                checker = QualityChecker()

                quality_result = await checker.check(
                    video_path=str(current_video),
                    original_photo_path=photo_path,
                    audio_path=str(cloned_audio_path),
                )

                result["stages"]["quality_check"] = {
                    "status": "completed",
                    "pass": quality_result["pass"],
                    "sync_score": quality_result["sync_score"],
                    "face_similarity": quality_result["face_similarity"],
                    "ai_detect_pct": quality_result["ai_detect_pct"],
                    "gates": quality_result["gates"],
                }

                if not quality_result["pass"]:
                    logger.warning(
                        "pipeline.quality_failed",
                        job_id=job_id,
                        sync=quality_result["sync_score"],
                        facesim=quality_result["face_similarity"],
                        ai_pct=quality_result["ai_detect_pct"],
                    )
                    # Mark quality warning but still deliver
                    result["quality_warning"] = True
                else:
                    logger.info("pipeline.quality_passed", job_id=job_id)
            else:
                result["stages"]["quality_check"] = {"status": "skipped"}

            await self._update_progress(job_id, "quality_check", 100)

            # ────────────────────────────────────────────
            # STAGE 7: Final Encode
            # ────────────────────────────────────────────
            await self._update_progress(job_id, "encoding", 0)

            final_video_path = await self._final_encode(
                video_path=str(current_video),
                audio_path=str(cloned_audio_path),
                output_dir=job_dir,
            )

            # Generate thumbnail from final video
            thumbnail_path = None
            try:
                thumbnail_path = await self._generate_thumbnail(
                    str(final_video_path), str(job_dir / "thumbnail.jpg")
                )
                result["thumbnail"] = thumbnail_path
            except Exception as thumb_err:
                logger.debug("pipeline.thumbnail_failed", error=str(thumb_err))

            result["stages"]["encode"] = {
                "status": "completed",
                "output": str(final_video_path),
            }
            await self._update_progress(job_id, "encoding", 100)

            # ────────────────────────────────────────────
            # DONE
            # ────────────────────────────────────────────
            elapsed = time.time() - start_time
            result["status"] = "completed"
            result["output_video"] = str(final_video_path)
            result["output_audio"] = str(cloned_audio_path)
            result["processing_time_seconds"] = round(elapsed, 2)
            result["download_url"] = f"/api/v1/video/{job_id}/download"

            # Attach quality scores to top-level result
            if quality_result:
                result["quality_score"] = quality_result["sync_score"]
                result["ai_detect_pct"] = quality_result["ai_detect_pct"]
                result["face_similarity"] = quality_result["face_similarity"]

            logger.info(
                "pipeline.complete",
                job_id=job_id,
                time_seconds=round(elapsed, 2),
                output=str(final_video_path),
                quality_pass=quality_result["pass"] if quality_result else "skipped",
            )

            await self._publish_progress(job_id, {
                "status": "completed",
                "progress": 100,
                "step": "completed",
                "download_url": result["download_url"],
            })

            return result

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                "pipeline.failed",
                job_id=job_id,
                error=str(e),
                time_seconds=round(elapsed, 2),
            )

            result["status"] = "failed"
            result["error"] = str(e)
            result["processing_time_seconds"] = round(elapsed, 2)

            await self._publish_progress(job_id, {
                "status": "failed",
                "progress": 0,
                "step": "failed",
                "error": str(e),
            })

            return result

    async def _final_encode(self, video_path: str, audio_path: str, output_dir: Path) -> Path:
        """Final H.264 encoding with proper settings."""
        import subprocess

        def _encode():
            final_path = output_dir / "final_output.mp4"
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
                str(final_path),
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=300)
            except (FileNotFoundError, subprocess.CalledProcessError) as e:
                logger.warning("pipeline.ffmpeg_fallback", error=str(e))
                import shutil
                shutil.copy2(video_path, str(final_path))

            return final_path

        return await asyncio.to_thread(_encode)

    async def _generate_thumbnail(self, video_path: str, thumbnail_path: str) -> str:
        """Extract a frame at 1 second as a 480x270 JPEG thumbnail."""
        import subprocess

        def _extract():
            cmd = [
                "ffmpeg", "-y",
                "-ss", "00:00:01",
                "-i", video_path,
                "-vframes", "1",
                "-vf", "scale=480:270:force_original_aspect_ratio=decrease,pad=480:270:(ow-iw)/2:(oh-ih)/2:black",
                "-q:v", "2",
                thumbnail_path,
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=30)
                return thumbnail_path
            except (FileNotFoundError, subprocess.CalledProcessError) as e:
                logger.debug("pipeline.thumbnail_ffmpeg_failed", error=str(e))
                return None

        return await asyncio.to_thread(_extract)

    async def _update_progress(self, job_id: str, step: str, step_progress: int):
        """Calculate and publish overall progress."""
        cumulative = 0
        stages = list(self.STAGE_WEIGHTS.keys())

        if step not in stages:
            return

        current_idx = stages.index(step)

        for i in range(current_idx):
            cumulative += self.STAGE_WEIGHTS[stages[i]]

        cumulative += int(self.STAGE_WEIGHTS[step] * step_progress / 100)

        await self._publish_progress(job_id, {
            "status": "processing",
            "progress": min(cumulative, 99),
            "step": step,
            "step_progress": step_progress,
        })

    async def _publish_progress(self, job_id: str, data: dict):
        """Publish progress to Redis for WebSocket consumption."""
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.REDIS_URL)
            await r.publish(f"job:{job_id}:progress", json.dumps(data))
            await r.close()
        except Exception as e:
            logger.debug("pipeline.redis_publish_failed", error=str(e))

        if self.progress_callback:
            try:
                self.progress_callback(job_id, data)
            except Exception:
                pass
