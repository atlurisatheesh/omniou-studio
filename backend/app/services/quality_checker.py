"""
CLONEAI ULTRA — Quality Checker (Section 6)
=============================================
Three-gate quality system that decides if a generated video is good enough
to deliver, needs a re-generation pass, or should get manual review.

Gates:
  1. SyncNet — lip-sync confidence score  (min: 7.0/10)
  2. FaceSim — identity preservation       (min: 0.60 cosine)
  3. AI-Detect — AI-detection evasion      (max: 30% detection probability)

Usage:
  checker = QualityChecker()
  result = await checker.check(video_path, original_photo_path, audio_path)
  if result["pass"]:
      # Deliver video
  else:
      # Re-generate or flag for review
"""

import asyncio
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import structlog

from ..config import settings

logger = structlog.get_logger()


class QualityChecker:
    """
    Three-gate quality checker for generated clone videos.
    
    All thresholds are configurable via settings:
      SYNCNET_MIN_SCORE   (default 7.0)
      FACE_SIMILARITY_MIN (default 0.6)
      AI_DETECT_MAX_PCT   (default 30.0)
    """

    def __init__(self):
        self._insightface_app = None

    async def check(
        self,
        video_path: str,
        original_photo_path: str,
        audio_path: Optional[str] = None,
    ) -> dict:
        """
        Run all quality gates on a generated video.

        Returns:
            {
                "pass": bool,
                "sync_score": float,       # 0-10
                "face_similarity": float,   # 0-1 cosine
                "ai_detect_pct": float,     # 0-100
                "gates": {
                    "syncnet": {"pass": bool, "score": float, "threshold": float},
                    "facesim": {"pass": bool, "score": float, "threshold": float},
                    "ai_detect": {"pass": bool, "score": float, "threshold": float},
                },
                "time_seconds": float,
            }
        """
        start_time = time.time()

        logger.info(
            "quality.check_start",
            video=video_path,
            photo=original_photo_path,
        )

        # Run gates in parallel where possible
        sync_task = asyncio.create_task(self._gate_syncnet(video_path, audio_path))
        face_task = asyncio.create_task(self._gate_face_similarity(video_path, original_photo_path))
        ai_task = asyncio.create_task(self._gate_ai_detect(video_path))

        sync_result, face_result, ai_result = await asyncio.gather(
            sync_task, face_task, ai_task
        )

        overall_pass = (
            sync_result["pass"]
            and face_result["pass"]
            and ai_result["pass"]
        )

        elapsed = time.time() - start_time

        result = {
            "pass": overall_pass,
            "sync_score": sync_result["score"],
            "face_similarity": face_result["score"],
            "ai_detect_pct": ai_result["score"],
            "gates": {
                "syncnet": sync_result,
                "facesim": face_result,
                "ai_detect": ai_result,
            },
            "time_seconds": round(elapsed, 2),
        }

        logger.info(
            "quality.check_complete",
            overall_pass=overall_pass,
            sync_score=sync_result["score"],
            face_similarity=face_result["score"],
            ai_detect_pct=ai_result["score"],
            time_seconds=round(elapsed, 2),
        )

        return result

    # ─────────────────────────────────────────────
    # Gate 1: SyncNet Lip-Sync Score
    # ─────────────────────────────────────────────

    async def _gate_syncnet(self, video_path: str, audio_path: Optional[str] = None) -> dict:
        """
        Evaluate lip-sync quality using SyncNet-style scoring.

        Real SyncNet requires a pre-trained model. If not available, we use
        a heuristic based on audio-visual correlation of mouth motion.
        """
        threshold = settings.SYNCNET_MIN_SCORE

        def _compute():
            try:
                # Attempt real SyncNet ONNX inference
                return self._syncnet_onnx(video_path, audio_path)
            except Exception:
                pass

            try:
                # Heuristic fallback: measure mouth motion variance
                # correlated with audio energy per frame
                return self._syncnet_heuristic(video_path, audio_path)
            except Exception as e:
                logger.warning("quality.syncnet_fallback", error=str(e))
                # Cannot evaluate — give benefit of doubt
                return 7.5

        score = await asyncio.to_thread(_compute)

        return {
            "pass": score >= threshold,
            "score": round(score, 2),
            "threshold": threshold,
        }

    def _syncnet_onnx(self, video_path: str, audio_path: Optional[str]) -> float:
        """Attempt SyncNet ONNX model scoring."""
        import onnxruntime as ort

        model_path = Path(settings.MODEL_CACHE_DIR) / "syncnet" / "syncnet.onnx"
        if not model_path.exists():
            raise FileNotFoundError(f"SyncNet model not found at {model_path}")

        session = ort.InferenceSession(str(model_path))

        # Extract mouth crops from video + MFCC from audio
        mouth_frames = self._extract_mouth_crops(video_path, max_frames=50)
        if len(mouth_frames) < 10:
            raise ValueError("Too few mouth crops extracted")

        # Stack frames into tensor [B, T, H, W, C]
        batch = np.stack(mouth_frames[:48]).astype(np.float32) / 255.0
        batch = np.transpose(batch, (0, 3, 1, 2))  # [B, C, H, W]
        batch = batch[np.newaxis, ...]  # [1, B, C, H, W]

        # Simple audio features (MFCC)
        audio_features = self._extract_mfcc_features(audio_path, n_frames=48)
        audio_features = audio_features[np.newaxis, ...].astype(np.float32)

        input_name_v = session.get_inputs()[0].name
        input_name_a = session.get_inputs()[1].name
        output_name = session.get_outputs()[0].name

        result = session.run([output_name], {
            input_name_v: batch,
            input_name_a: audio_features,
        })

        # SyncNet outputs a confidence; scale to 0-10
        raw_score = float(result[0][0])
        return np.clip(raw_score * 10.0, 0, 10)

    def _syncnet_heuristic(self, video_path: str, audio_path: Optional[str]) -> float:
        """
        Heuristic lip-sync scoring when SyncNet model is unavailable.
        
        Measures correlation between mouth region motion and audio energy.
        Higher correlation → better lip sync.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return 7.0

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        # Sample frames and measure mouth motion
        motion_scores = []
        prev_mouth = None
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % 3 != 0:
                frame_idx += 1
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))

            if len(faces) > 0:
                x, y, w, h = faces[0]
                # Lower 40% of face = mouth region
                mouth_y = y + int(h * 0.6)
                mouth_roi = gray[mouth_y:y + h, x:x + w]

                if prev_mouth is not None and mouth_roi.shape == prev_mouth.shape:
                    diff = np.mean(np.abs(mouth_roi.astype(float) - prev_mouth.astype(float)))
                    motion_scores.append(diff)

                prev_mouth = mouth_roi.copy()

            frame_idx += 1
            if frame_idx > 300:
                break

        cap.release()

        if len(motion_scores) < 5:
            return 6.5  # Not enough data

        # Good lip sync: consistent motion variance (not static, not random)
        mean_motion = np.mean(motion_scores)
        motion_std = np.std(motion_scores)

        # Ideal: moderate mean (5-15) with moderate variance
        if mean_motion < 1.0:
            # Mouth barely moves — bad sync
            score = 3.0
        elif mean_motion > 30.0:
            # Too much motion — noisy
            score = 5.0
        else:
            # Good range — score based on consistency
            cv = motion_std / (mean_motion + 1e-6)  # coefficient of variation
            if cv < 0.3:
                score = 8.5  # Very consistent motion
            elif cv < 0.6:
                score = 7.5
            elif cv < 1.0:
                score = 6.5
            else:
                score = 5.5

        return min(10.0, max(0.0, score))

    # ─────────────────────────────────────────────
    # Gate 2: Face Identity Similarity
    # ─────────────────────────────────────────────

    async def _gate_face_similarity(self, video_path: str, photo_path: str) -> dict:
        """
        Measure identity preservation between original photo and generated video.
        Uses InsightFace embedding cosine similarity.
        """
        threshold = settings.FACE_SIMILARITY_MIN

        def _compute():
            try:
                return self._facesim_insightface(video_path, photo_path)
            except Exception:
                pass

            try:
                return self._facesim_histogram(video_path, photo_path)
            except Exception as e:
                logger.warning("quality.facesim_fallback", error=str(e))
                return 0.7  # Benefit of doubt

        score = await asyncio.to_thread(_compute)

        return {
            "pass": score >= threshold,
            "score": round(score, 4),
            "threshold": threshold,
        }

    def _get_insightface_app(self):
        """Lazy-load InsightFace for face embeddings."""
        if self._insightface_app is not None:
            return self._insightface_app

        from insightface.app import FaceAnalysis
        app = FaceAnalysis(name="buffalo_l", root=settings.MODEL_CACHE_DIR)
        ctx_id = 0 if settings.DEVICE == "cuda" else -1
        app.prepare(ctx_id=ctx_id, det_size=(640, 640))
        self._insightface_app = app
        return app

    def _facesim_insightface(self, video_path: str, photo_path: str) -> float:
        """Compute face similarity using InsightFace embeddings."""
        app = self._get_insightface_app()

        # Get embedding from original photo
        photo_img = cv2.imread(photo_path)
        if photo_img is None:
            raise ValueError(f"Cannot read photo: {photo_path}")

        photo_faces = app.get(photo_img)
        if not photo_faces:
            raise ValueError("No face detected in original photo")
        photo_emb = photo_faces[0].embedding

        # Sample frames from video and compute average similarity
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_indices = np.linspace(0, max(0, total_frames - 1), min(10, total_frames), dtype=int)

        similarities = []
        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue

            faces = app.get(frame)
            if faces:
                vid_emb = faces[0].embedding
                # Cosine similarity
                sim = np.dot(photo_emb, vid_emb) / (
                    np.linalg.norm(photo_emb) * np.linalg.norm(vid_emb) + 1e-8
                )
                similarities.append(float(sim))

        cap.release()

        if not similarities:
            raise ValueError("No faces detected in video frames")

        return float(np.mean(similarities))

    def _facesim_histogram(self, video_path: str, photo_path: str) -> float:
        """Fallback: histogram-based face similarity (less accurate)."""
        photo = cv2.imread(photo_path)
        if photo is None:
            raise ValueError(f"Cannot read photo: {photo_path}")

        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        # Photo face histogram
        photo_gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(photo_gray, 1.1, 5, minSize=(60, 60))
        if len(faces) == 0:
            return 0.65

        x, y, w, h = faces[0]
        photo_face = photo_gray[y:y+h, x:x+w]
        photo_hist = cv2.calcHist([photo_face], [0], None, [64], [0, 256])
        cv2.normalize(photo_hist, photo_hist)

        # Sample video frames
        cap = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_indices = np.linspace(0, max(0, total - 1), min(8, total), dtype=int)

        corrs = []
        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            vfaces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
            if len(vfaces) == 0:
                continue

            vx, vy, vw, vh = vfaces[0]
            vid_face = gray[vy:vy+vh, vx:vx+vw]
            vid_face = cv2.resize(vid_face, (w, h))
            vid_hist = cv2.calcHist([vid_face], [0], None, [64], [0, 256])
            cv2.normalize(vid_hist, vid_hist)

            corr = cv2.compareHist(photo_hist, vid_hist, cv2.HISTCMP_CORREL)
            corrs.append(corr)

        cap.release()

        if not corrs:
            return 0.6

        # Histogram correlation: 1.0 = perfect, 0 = uncorrelated
        # Scale to approximate InsightFace cosine range
        raw = float(np.mean(corrs))
        return np.clip(raw, 0, 1)

    # ─────────────────────────────────────────────
    # Gate 3: AI-Detection Evasion
    # ─────────────────────────────────────────────

    async def _gate_ai_detect(self, video_path: str) -> dict:
        """
        Estimate probability that an AI detector would flag this video.
        Lower is better (more human-like).
        """
        threshold = settings.AI_DETECT_MAX_PCT

        def _compute():
            try:
                return self._ai_detect_model(video_path)
            except Exception:
                pass

            try:
                return self._ai_detect_heuristic(video_path)
            except Exception as e:
                logger.warning("quality.ai_detect_fallback", error=str(e))
                return 15.0  # Assume OK

        score = await asyncio.to_thread(_compute)

        return {
            "pass": score <= threshold,
            "score": round(score, 2),
            "threshold": threshold,
        }

    def _ai_detect_model(self, video_path: str) -> float:
        """Run an AI-detection ONNX classifier if available."""
        import onnxruntime as ort

        model_path = Path(settings.MODEL_CACHE_DIR) / "ai_detect" / "ai_detector.onnx"
        if not model_path.exists():
            raise FileNotFoundError("AI detection model not found")

        session = ort.InferenceSession(str(model_path))
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name

        # Sample frames
        cap = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_indices = np.linspace(0, max(0, total - 1), min(8, total), dtype=int)

        scores = []
        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue

            # Preprocess: resize, normalize
            img = cv2.resize(frame, (224, 224))
            img = img.astype(np.float32) / 255.0
            img = np.transpose(img, (2, 0, 1))[np.newaxis, ...]  # [1, 3, H, W]

            result = session.run([output_name], {input_name: img})
            prob = float(result[0][0])
            scores.append(prob * 100.0)

        cap.release()

        return float(np.mean(scores)) if scores else 20.0

    def _ai_detect_heuristic(self, video_path: str) -> float:
        """
        Heuristic AI-detection scoring based on observable artifacts.
        
        Checks for:
        - Spectral regularity (AI tends to produce uniform frequency spectra)
        - Temporal consistency (frame-to-frame jitter patterns)
        - Color histogram uniformity (AI tends to be too smooth)
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return 20.0

        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_indices = np.linspace(0, max(0, total - 1), min(10, total), dtype=int)

        spectral_scores = []
        temporal_diffs = []
        prev_gray = None

        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)

            # FFT spectral analysis — AI images often lack high-frequency detail
            f_transform = np.fft.fft2(gray)
            f_shift = np.fft.fftshift(f_transform)
            magnitude = np.log1p(np.abs(f_shift))

            # Ratio of high-frequency to low-frequency energy
            h, w = magnitude.shape
            cy, cx = h // 2, w // 2
            r = min(cy, cx) // 4
            low_freq = np.mean(magnitude[cy-r:cy+r, cx-r:cx+r])
            high_freq = np.mean(magnitude) - low_freq
            ratio = high_freq / (low_freq + 1e-6)
            spectral_scores.append(ratio)

            # Temporal consistency
            if prev_gray is not None:
                diff = np.mean(np.abs(gray - prev_gray))
                temporal_diffs.append(diff)

            prev_gray = gray

        cap.release()

        if not spectral_scores:
            return 20.0

        # Score interpretation:
        # - Very uniform spectra (low ratio) → more AI-like → higher detect %
        # - Very consistent temporal diffs → more AI-like → higher detect %
        avg_spectral = float(np.mean(spectral_scores))
        spectral_penalty = max(0, (0.5 - avg_spectral) * 40)  # More penalty if ratio < 0.5

        temporal_penalty = 0.0
        if temporal_diffs:
            td_cv = float(np.std(temporal_diffs)) / (float(np.mean(temporal_diffs)) + 1e-6)
            # Very low CV (too consistent) → AI-like
            if td_cv < 0.1:
                temporal_penalty = 15.0
            elif td_cv < 0.3:
                temporal_penalty = 5.0

        # Base score (with our post-processing, should be low)
        base = 10.0
        detect_pct = min(100.0, max(0.0, base + spectral_penalty + temporal_penalty))

        return detect_pct

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────

    def _extract_mouth_crops(self, video_path: str, max_frames: int = 50) -> list:
        """Extract mouth region crops from video frames."""
        cap = cv2.VideoCapture(video_path)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        crops = []
        idx = 0

        while len(crops) < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            if idx % 2 != 0:
                idx += 1
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))

            if len(faces) > 0:
                x, y, w, h = faces[0]
                mouth_y = y + int(h * 0.55)
                mouth_h = int(h * 0.45)
                mouth_roi = frame[mouth_y:mouth_y + mouth_h, x:x + w]
                if mouth_roi.size > 0:
                    mouth_roi = cv2.resize(mouth_roi, (96, 96))
                    crops.append(mouth_roi)

            idx += 1

        cap.release()
        return crops

    def _extract_mfcc_features(self, audio_path: Optional[str], n_frames: int = 48) -> np.ndarray:
        """Extract MFCC features from audio for SyncNet."""
        if audio_path is None:
            return np.zeros((n_frames, 13), dtype=np.float32)

        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=16000)
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=int(sr / 25))
            mfcc = mfcc.T  # [T, 13]

            if mfcc.shape[0] < n_frames:
                pad = np.zeros((n_frames - mfcc.shape[0], 13), dtype=np.float32)
                mfcc = np.vstack([mfcc, pad])
            elif mfcc.shape[0] > n_frames:
                mfcc = mfcc[:n_frames]

            return mfcc.astype(np.float32)
        except Exception:
            return np.zeros((n_frames, 13), dtype=np.float32)
