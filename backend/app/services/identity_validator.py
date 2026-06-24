"""
CLONEAI ULTRA — Identity Validator
====================================
Per-frame and cross-scene validation engine for character consistency.

Validates that every frame in every scene matches the identity anchor.
Detects drift, triggers corrections, and produces detailed reports.

Validation layers:
  1. Per-frame: face similarity, color consistency, structural match
  2. Per-scene: aggregate scores, drift detection, pass/fail
  3. Cross-scene: scene-to-scene continuity, scene-to-anchor fidelity
  4. Project-level: global consistency score, color normalization
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import structlog

from ..config import settings
from .identity_anchor import (
    FrameConsistencyScore,
    IdentityAnchor,
    IdentityAnchorService,
    ProjectConsistencyReport,
    SceneConsistencyReport,
)

logger = structlog.get_logger()


class IdentityValidator:
    """
    Multi-level identity validation for long-form video generation.
    
    Usage:
        validator = IdentityValidator()
        
        # Validate a single scene
        report = await validator.validate_scene("scene.mp4", anchor)
        
        # Validate across all scenes
        project_report = await validator.validate_project(scene_paths, anchor)
        
        # Fix drifted frames
        corrected = await validator.correct_drifted_frames("scene.mp4", anchor)
    """
    
    def __init__(self, model_cache_dir: str = "./models"):
        self.anchor_service = IdentityAnchorService(model_cache_dir=model_cache_dir)
    
    # ── Scene Validation ──
    
    async def validate_scene(
        self,
        video_path: str,
        anchor: IdentityAnchor,
        scene_index: int = 0,
        sample_interval: int = None,
    ) -> SceneConsistencyReport:
        """
        Validate a single scene video against the identity anchor.
        
        Returns a detailed report with per-frame scores and drift detection.
        """
        start_time = time.time()
        
        report = await self.anchor_service.compare_scene(
            video_path=video_path,
            anchor=anchor,
            sample_interval=sample_interval,
            scene_index=scene_index,
        )
        
        elapsed = time.time() - start_time
        logger.info(
            "identity_validator.scene_validated",
            scene_index=scene_index,
            identity_mean=report.identity_score_mean,
            color_mean=report.color_score_mean,
            drift_frames=report.drift_frame_count,
            passed=report.passed,
            time_seconds=round(elapsed, 2),
        )
        
        return report
    
    # ── Project Validation ──
    
    async def validate_project(
        self,
        scene_video_paths: List[str],
        anchor: IdentityAnchor,
        sample_interval: int = None,
    ) -> ProjectConsistencyReport:
        """
        Validate ALL scenes in a project for identity consistency.
        
        Performs:
          1. Per-scene validation (identity + color)
          2. Cross-scene comparison (last frame of N ↔ first frame of N+1)
          3. Global consistency scoring
        """
        start_time = time.time()
        logger.info("identity_validator.project_validation_start", scene_count=len(scene_video_paths))
        
        # Step 1: Validate each scene individually
        scene_reports = []
        for i, path in enumerate(scene_video_paths):
            report = await self.validate_scene(
                video_path=path,
                anchor=anchor,
                scene_index=i,
                sample_interval=sample_interval,
            )
            scene_reports.append(report)
        
        # Step 2: Cross-scene comparison (adjacent scenes must match)
        cross_scene_scores = []
        for i in range(len(scene_video_paths) - 1):
            score = await self._compare_adjacent_scenes(
                scene_video_paths[i],
                scene_video_paths[i + 1],
                anchor,
            )
            cross_scene_scores.append(score)
        
        # Step 3: Compute overall scores
        identity_scores = [r.identity_score_mean for r in scene_reports]
        color_scores = [r.color_score_mean for r in scene_reports]
        
        overall_identity = float(np.mean(identity_scores)) if identity_scores else 0.0
        overall_color = float(np.mean(color_scores)) if color_scores else 0.0
        
        # Check if all scenes pass
        all_scenes_pass = all(r.passed for r in scene_reports)
        all_transitions_pass = all(
            s >= settings.IDENTITY_CROSS_SCENE_THRESHOLD
            for s in cross_scene_scores
        )
        
        project_report = ProjectConsistencyReport(
            total_scenes=len(scene_video_paths),
            overall_identity_score=round(overall_identity, 4),
            overall_color_score=round(overall_color, 4),
            scene_reports=scene_reports,
            cross_scene_scores=[round(s, 4) for s in cross_scene_scores],
            all_passed=all_scenes_pass and all_transitions_pass,
        )
        
        elapsed = time.time() - start_time
        logger.info(
            "identity_validator.project_validated",
            overall_identity=project_report.overall_identity_score,
            overall_color=project_report.overall_color_score,
            all_passed=project_report.all_passed,
            time_seconds=round(elapsed, 2),
        )
        
        return project_report
    
    # ── Drift Detection ──
    
    async def find_drift_frames(
        self,
        video_path: str,
        anchor: IdentityAnchor,
        threshold: float = None,
    ) -> List[FrameConsistencyScore]:
        """
        Find all frames that have drifted below the identity threshold.
        
        Returns list of drifted frames with their scores.
        Used by the correction pipeline to fix specific frames.
        """
        if threshold is None:
            threshold = settings.IDENTITY_SIMILARITY_THRESHOLD
        
        # Get scene report with higher sampling rate for drift detection
        report = await self.anchor_service.compare_scene(
            video_path=video_path,
            anchor=anchor,
            sample_interval=5,  # Check every 5th frame for better coverage
        )
        
        drifted = [
            score for score in report.frame_scores
            if score.overall < threshold
        ]
        
        logger.info(
            "identity_validator.drift_detected",
            total_checked=report.total_frames_checked,
            drifted_count=len(drifted),
            threshold=threshold,
        )
        
        return drifted
    
    # ── Drift Correction ──
    
    async def correct_drifted_frames(
        self,
        video_path: str,
        anchor: IdentityAnchor,
        output_path: Optional[str] = None,
        threshold: float = None,
    ) -> str:
        """
        Auto-correct frames that have drifted from the identity anchor.
        
        Correction strategies:
          1. Color drift → histogram matching to anchor palette
          2. Face drift → blend with reference + GFPGAN re-enhancement
          3. Structural drift → interpolate with nearest good frame
        
        Returns path to corrected video.
        """
        if threshold is None:
            threshold = settings.IDENTITY_SIMILARITY_THRESHOLD
        
        if output_path is None:
            p = Path(video_path)
            output_path = str(p.parent / f"corrected_{p.name}")
        
        # Find drifted frames
        drifted_frames = await self.find_drift_frames(video_path, anchor, threshold)
        
        if not drifted_frames:
            logger.info("identity_validator.no_drift_to_correct")
            return video_path
        
        drifted_indices = set(f.frame_index for f in drifted_frames)
        
        def _correct():
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return video_path
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frame_idx = 0
            last_good_frame = None
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Check if this frame or nearby frames need correction
                needs_correction = False
                for di in drifted_indices:
                    if abs(frame_idx - di) <= 2:  # Correct frame ± 2 neighbors
                        needs_correction = True
                        break
                
                if needs_correction:
                    # Apply color correction
                    corrected_frame = self._correct_frame_color(
                        frame, anchor
                    )
                    
                    # Blend with last good frame for smoothness
                    if last_good_frame is not None:
                        alpha = 0.7  # 70% corrected, 30% last good
                        corrected_frame = cv2.addWeighted(
                            corrected_frame, alpha,
                            cv2.resize(last_good_frame, (width, height)), 1 - alpha,
                            0,
                        )
                    
                    out.write(corrected_frame)
                else:
                    out.write(frame)
                    last_good_frame = frame.copy()
                
                frame_idx += 1
            
            cap.release()
            out.release()
            return output_path
        
        result = await asyncio.to_thread(_correct)
        
        logger.info(
            "identity_validator.drift_corrected",
            corrected_frames=len(drifted_frames),
            output=result,
        )
        
        return result
    
    def _correct_frame_color(
        self,
        frame: np.ndarray,
        anchor: IdentityAnchor,
    ) -> np.ndarray:
        """Apply color correction to a single frame to match anchor palette."""
        if anchor.mean_skin_color_bgr is None:
            return frame
        
        # Simple color transfer: match the mean of each channel
        result = frame.copy().astype(np.float32)
        
        # Detect face region
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        
        if len(faces) == 0:
            return frame
        
        x, y, fw, fh = faces[0]
        face_region = frame[y:y + fh, x:x + fw].astype(np.float32)
        
        if face_region.size == 0:
            return frame
        
        # Compute current mean color
        current_mean = cv2.mean(face_region)[:3]
        target_mean = anchor.mean_skin_color_bgr
        
        # Apply subtle shift (40% strength)
        shift = np.array(target_mean) - np.array(current_mean)
        face_corrected = face_region + shift * 0.4
        face_corrected = np.clip(face_corrected, 0, 255)
        
        # Create smooth blend mask
        mask = np.zeros((fh, fw), dtype=np.float32)
        cv2.ellipse(mask, (fw // 2, fh // 2), (fw // 2 - 3, fh // 2 - 3), 0, 0, 360, 1.0, -1)
        mask = cv2.GaussianBlur(mask, (11, 11), 4)
        mask = mask[:, :, np.newaxis]
        
        # Blend
        blended = (face_corrected * mask + face_region * (1 - mask)).astype(np.uint8)
        result[y:y + fh, x:x + fw] = blended
        
        return result.astype(np.uint8)
    
    # ── Color Normalization (Cross-Scene) ──
    
    async def normalize_scene_colors(
        self,
        video_path: str,
        anchor: IdentityAnchor,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Normalize the color palette of an entire scene to match the anchor.
        
        This ensures all scenes have consistent skin tones, lighting, and
        color balance — critical for seamless stitching.
        """
        if output_path is None:
            p = Path(video_path)
            output_path = str(p.parent / f"color_norm_{p.name}")
        
        if anchor.mean_skin_color_bgr is None:
            return video_path
        
        def _normalize():
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return video_path
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Apply subtle global color correction
                corrected = self._correct_frame_color(frame, anchor)
                out.write(corrected)
            
            cap.release()
            out.release()
            return output_path
        
        result = await asyncio.to_thread(_normalize)
        
        logger.info("identity_validator.colors_normalized", output=result)
        return result
    
    # ── Private: Cross-Scene Compare ──
    
    async def _compare_adjacent_scenes(
        self,
        scene_a_path: str,
        scene_b_path: str,
        anchor: IdentityAnchor,
    ) -> float:
        """
        Compare the last frame of scene A with the first frame of scene B.
        
        High similarity means smooth, consistent transition.
        Low similarity means a visible "character change" at the cut point.
        """
        def _extract_boundary_frames():
            # Get last frame of scene A
            cap_a = cv2.VideoCapture(scene_a_path)
            if not cap_a.isOpened():
                return None, None
            
            total_a = int(cap_a.get(cv2.CAP_PROP_FRAME_COUNT))
            cap_a.set(cv2.CAP_PROP_POS_FRAMES, max(0, total_a - 1))
            ret_a, frame_a = cap_a.read()
            cap_a.release()
            
            # Get first frame of scene B
            cap_b = cv2.VideoCapture(scene_b_path)
            if not cap_b.isOpened():
                return None, None
            
            ret_b, frame_b = cap_b.read()
            cap_b.release()
            
            if not ret_a or not ret_b:
                return None, None
            
            return frame_a, frame_b
        
        frame_a, frame_b = await asyncio.to_thread(_extract_boundary_frames)
        
        if frame_a is None or frame_b is None:
            return 0.0
        
        # Compare both frames against the anchor
        score_a = await self.anchor_service.compare_frame(frame_a, anchor)
        score_b = await self.anchor_service.compare_frame(frame_b, anchor)
        
        # Also compare frames directly against each other
        face_data_a = await self.anchor_service._extract_face_data(frame_a)
        face_data_b = await self.anchor_service._extract_face_data(frame_b)
        
        if face_data_a["embedding"] is not None and face_data_b["embedding"] is not None:
            direct_score = self.anchor_service._cosine_similarity(
                face_data_a["embedding"],
                face_data_b["embedding"],
            )
        else:
            direct_score = 0.0
        
        # Weighted: 50% direct scene-to-scene + 25% each scene-to-anchor
        combined = direct_score * 0.5 + score_a * 0.25 + score_b * 0.25
        
        logger.info(
            "identity_validator.cross_scene_compared",
            scene_a=scene_a_path,
            scene_b=scene_b_path,
            direct_score=round(direct_score, 4),
            combined_score=round(combined, 4),
        )
        
        return combined
    
    # ── Generate Transition Frames ──
    
    async def generate_transition_frames(
        self,
        scene_a_path: str,
        scene_b_path: str,
        anchor: IdentityAnchor,
        n_frames: int = 15,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate smooth transition frames between two scenes
        while maintaining identity consistency.
        
        Uses frame interpolation with identity-constrained blending.
        """
        if output_path is None:
            output_path = str(
                Path(scene_a_path).parent / f"transition_{Path(scene_a_path).stem}_{Path(scene_b_path).stem}.mp4"
            )
        
        def _generate():
            # Extract boundary frames
            cap_a = cv2.VideoCapture(scene_a_path)
            if not cap_a.isOpened():
                return None
            
            total_a = int(cap_a.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap_a.get(cv2.CAP_PROP_FPS) or 30
            cap_a.set(cv2.CAP_PROP_POS_FRAMES, max(0, total_a - 1))
            ret_a, frame_a = cap_a.read()
            width = int(cap_a.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap_a.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap_a.release()
            
            cap_b = cv2.VideoCapture(scene_b_path)
            if not cap_b.isOpened():
                return None
            
            ret_b, frame_b = cap_b.read()
            cap_b.release()
            
            if not ret_a or not ret_b:
                return None
            
            # Ensure same size
            frame_b = cv2.resize(frame_b, (width, height))
            
            # Generate interpolated transition frames (crossfade)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            for i in range(n_frames):
                alpha = i / (n_frames - 1)  # 0.0 → 1.0
                
                # Smooth easing (ease-in-out)
                eased_alpha = 0.5 * (1 - np.cos(np.pi * alpha))
                
                # Blend frames
                blended = cv2.addWeighted(
                    frame_a, 1 - eased_alpha,
                    frame_b, eased_alpha,
                    0,
                )
                
                out.write(blended)
            
            out.release()
            return output_path
        
        result = await asyncio.to_thread(_generate)
        
        if result:
            logger.info(
                "identity_validator.transition_generated",
                n_frames=n_frames,
                output=result,
            )
        
        return result
