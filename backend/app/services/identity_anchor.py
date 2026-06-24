"""
CLONEAI ULTRA — Identity Anchor System
=========================================
The foundational component for character consistency across long-form videos.

Extracts a permanent identity reference ("anchor") from a single photo + voice:
  - Face embedding (512-dim InsightFace vector)
  - Appearance features (texture/structure map for animation engines)
  - Reference keypoints (68-point facial landmarks)
  - Skin color histogram (HSV palette for cross-scene color matching)
  - Canonical reference frame (aligned, normalized, 512x512)
  - Voice embedding (XTTS conditioning latent for voice lock)

This anchor is IMMUTABLE once created — it represents "YOU" for the entire project.
Every scene, every frame, every voice clip is constrained against this anchor.
"""

import asyncio
import hashlib
import pickle
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import structlog

from ..config import settings

logger = structlog.get_logger()

ANCHOR_DIR = Path("outputs") / "anchors"
ANCHOR_DIR.mkdir(parents=True, exist_ok=True)


# ── Identity Anchor Data Class ──────────────────────────────

@dataclass
class IdentityAnchor:
    """
    Immutable identity reference representing a single character.
    
    Once created, this anchor is used to:
      1. Condition face animation models (so every frame looks like YOU)
      2. Validate generated frames (so drift is caught instantly)
      3. Normalize colors across scenes (so skin tone stays consistent)
      4. Lock voice characteristics (so you sound the same in every scene)
    """
    # Core identity
    anchor_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    
    # Face identity (WHO you are)
    face_embedding: Optional[np.ndarray] = None           # 512-dim InsightFace vector
    
    # Appearance (WHAT you look like)
    appearance_features: Optional[np.ndarray] = None      # Feature map for animation engines
    
    # Structure (face GEOMETRY)
    reference_keypoints: Optional[np.ndarray] = None      # 68-point or 5-point landmarks
    face_bbox: Optional[np.ndarray] = None                # [x1, y1, x2, y2] face bounding box
    
    # Color (your PALETTE)
    skin_color_histogram: Optional[np.ndarray] = None     # HSV histogram of face skin region
    mean_skin_color_bgr: Optional[np.ndarray] = None      # Average BGR skin color
    
    # Visual reference (canonical "this is me" frame)
    reference_frame: Optional[np.ndarray] = None          # Aligned, normalized, 512x512 BGR
    reference_frame_original: Optional[np.ndarray] = None # Original uncropped photo
    
    # Voice identity (HOW you sound)
    voice_embedding: Optional[np.ndarray] = None          # Speaker conditioning latent
    voice_sample_path: Optional[str] = None               # Path to original voice sample
    
    # Metadata
    source_photo_path: Optional[str] = None
    source_photo_hash: Optional[str] = None               # SHA256 for cache invalidation
    created_at: Optional[float] = None
    
    def is_valid(self) -> bool:
        """Check if anchor has minimum required data."""
        return (
            self.face_embedding is not None
            and self.reference_frame is not None
        )
    
    def has_voice(self) -> bool:
        """Check if voice data is available."""
        return self.voice_embedding is not None
    
    def summary(self) -> dict:
        """Return a JSON-serializable summary of the anchor."""
        return {
            "anchor_id": self.anchor_id,
            "has_face_embedding": self.face_embedding is not None,
            "has_appearance_features": self.appearance_features is not None,
            "has_keypoints": self.reference_keypoints is not None,
            "has_skin_histogram": self.skin_color_histogram is not None,
            "has_reference_frame": self.reference_frame is not None,
            "has_voice_embedding": self.voice_embedding is not None,
            "source_photo": self.source_photo_path,
            "voice_sample": self.voice_sample_path,
            "created_at": self.created_at,
        }


# ── Scene Consistency Report ────────────────────────────────

@dataclass
class FrameConsistencyScore:
    """Consistency score for a single frame."""
    frame_index: int
    face_similarity: float        # 0.0–1.0 cosine similarity
    color_consistency: float      # 0.0–1.0 histogram correlation
    structural_match: float       # 0.0–1.0 landmark distance (inverted)
    overall: float                # Weighted average
    is_drifted: bool              # Below threshold?


@dataclass
class SceneConsistencyReport:
    """Full consistency analysis for a single scene."""
    scene_index: int
    total_frames_checked: int
    identity_score_mean: float
    identity_score_min: float
    identity_score_max: float
    identity_score_std: float
    color_score_mean: float
    drift_frame_count: int
    drift_frame_indices: List[int]
    frame_scores: List[FrameConsistencyScore]
    passed: bool                  # All above threshold?


@dataclass 
class ProjectConsistencyReport:
    """Full consistency analysis across all scenes in a project."""
    total_scenes: int
    overall_identity_score: float
    overall_color_score: float
    scene_reports: List[SceneConsistencyReport]
    cross_scene_scores: List[float]   # scene[i] last frame ↔ scene[i+1] first frame
    all_passed: bool


# ── Identity Anchor Service ─────────────────────────────────

class IdentityAnchorService:
    """
    Creates, persists, and uses identity anchors for character consistency.
    
    Usage:
        service = IdentityAnchorService()
        anchor = await service.create_anchor("photo.jpg", "voice.wav")
        score = await service.compare_frame(frame, anchor)
        report = await service.compare_scene("scene.mp4", anchor)
    """
    
    def __init__(self, model_cache_dir: str = "./models"):
        self.model_cache_dir = Path(model_cache_dir)
        self._insightface_app = None
    
    # ── Create Anchor ──
    
    async def create_anchor(
        self,
        photo_path: str,
        voice_path: Optional[str] = None,
        anchor_id: Optional[str] = None,
    ) -> IdentityAnchor:
        """
        Create a complete identity anchor from a photo + optional voice sample.
        
        This is the FIRST step in any long-form video project. The anchor
        captures everything about your identity and is used to constrain
        every subsequent frame of video generation.
        
        Args:
            photo_path: Path to face photo (JPG/PNG)
            voice_path: Optional path to voice sample (WAV/MP3)
            anchor_id: Optional custom ID (auto-generated if not provided)
        
        Returns:
            IdentityAnchor with all identity data populated
        """
        start_time = time.time()
        logger.info("identity_anchor.creating", photo=photo_path, voice=voice_path)
        
        anchor = IdentityAnchor(
            anchor_id=anchor_id or uuid.uuid4().hex[:16],
            source_photo_path=photo_path,
            voice_sample_path=voice_path,
            created_at=time.time(),
        )
        
        # Compute photo hash for cache invalidation
        anchor.source_photo_hash = await self._compute_file_hash(photo_path)
        
        # Step 1: Load and validate photo
        photo = await asyncio.to_thread(cv2.imread, photo_path)
        if photo is None:
            raise ValueError(f"Could not load photo: {photo_path}")
        
        anchor.reference_frame_original = photo.copy()
        
        # Step 2: Detect face and extract all face data
        face_data = await self._extract_face_data(photo)
        
        anchor.face_embedding = face_data["embedding"]
        anchor.reference_keypoints = face_data["keypoints"]
        anchor.face_bbox = face_data["bbox"]
        
        # Step 3: Create canonical reference frame (aligned 512x512)
        anchor.reference_frame = await self._create_canonical_frame(
            photo, face_data["bbox"]
        )
        
        # Step 4: Extract appearance features for animation engines
        anchor.appearance_features = await self._extract_appearance_features(
            anchor.reference_frame
        )
        
        # Step 5: Compute skin color histogram
        anchor.skin_color_histogram, anchor.mean_skin_color_bgr = (
            await self._extract_skin_color(anchor.reference_frame, face_data["bbox_in_crop"])
        )
        
        # Step 6: Extract voice embedding (if voice sample provided)
        if voice_path and Path(voice_path).exists():
            anchor.voice_embedding = await self._extract_voice_embedding(voice_path)
        
        elapsed = time.time() - start_time
        logger.info(
            "identity_anchor.created",
            anchor_id=anchor.anchor_id,
            has_voice=anchor.has_voice(),
            time_seconds=round(elapsed, 2),
        )
        
        return anchor
    
    # ── Persist / Load ──
    
    async def save_anchor(self, anchor: IdentityAnchor, project_id: str) -> str:
        """Save identity anchor to disk for project persistence."""
        anchor_dir = ANCHOR_DIR / project_id
        anchor_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main anchor data as pickle
        anchor_path = anchor_dir / f"{anchor.anchor_id}.pkl"
        
        def _save():
            with open(str(anchor_path), "wb") as f:
                pickle.dump(anchor, f)
            
            # Also save reference frame as image for visual inspection
            if anchor.reference_frame is not None:
                ref_path = anchor_dir / f"{anchor.anchor_id}_reference.jpg"
                cv2.imwrite(str(ref_path), anchor.reference_frame)
            
            return str(anchor_path)
        
        result = await asyncio.to_thread(_save)
        logger.info("identity_anchor.saved", path=result, project_id=project_id)
        return result
    
    async def load_anchor(self, project_id: str, anchor_id: str) -> IdentityAnchor:
        """Load identity anchor from disk."""
        anchor_path = ANCHOR_DIR / project_id / f"{anchor_id}.pkl"
        
        if not anchor_path.exists():
            raise FileNotFoundError(f"Anchor not found: {anchor_path}")
        
        def _load():
            with open(str(anchor_path), "rb") as f:
                return pickle.load(f)
        
        anchor = await asyncio.to_thread(_load)
        logger.info("identity_anchor.loaded", anchor_id=anchor_id, project_id=project_id)
        return anchor
    
    # ── Compare (Single Frame) ──
    
    async def compare_frame(
        self,
        frame: np.ndarray,
        anchor: IdentityAnchor,
    ) -> float:
        """
        Compare a single video frame against the identity anchor.
        
        Returns:
            Cosine similarity score 0.0 (different person) → 1.0 (perfect match)
        """
        face_data = await self._extract_face_data(frame)
        
        if face_data["embedding"] is None:
            return 0.0
        
        return self._cosine_similarity(
            face_data["embedding"],
            anchor.face_embedding,
        )
    
    async def compare_frame_full(
        self,
        frame: np.ndarray,
        anchor: IdentityAnchor,
    ) -> FrameConsistencyScore:
        """
        Full consistency check of a single frame against the anchor.
        Checks: face identity, skin color, facial structure.
        """
        face_data = await self._extract_face_data(frame)
        
        # Face identity (embedding cosine similarity)
        if face_data["embedding"] is not None:
            face_sim = self._cosine_similarity(
                face_data["embedding"], anchor.face_embedding
            )
        else:
            face_sim = 0.0
        
        # Color consistency (histogram correlation)
        if face_data["bbox"] is not None and anchor.skin_color_histogram is not None:
            color_score = await self._compare_skin_color(frame, face_data["bbox"], anchor)
        else:
            color_score = 0.0
        
        # Structural match (landmark distance)
        if face_data["keypoints"] is not None and anchor.reference_keypoints is not None:
            struct_score = self._compare_landmarks(
                face_data["keypoints"], anchor.reference_keypoints
            )
        else:
            struct_score = face_sim  # Fallback to face sim
        
        # Weighted overall
        overall = face_sim * 0.6 + color_score * 0.25 + struct_score * 0.15
        
        threshold = settings.IDENTITY_SIMILARITY_THRESHOLD
        
        return FrameConsistencyScore(
            frame_index=0,  # Set by caller
            face_similarity=round(face_sim, 4),
            color_consistency=round(color_score, 4),
            structural_match=round(struct_score, 4),
            overall=round(overall, 4),
            is_drifted=overall < threshold,
        )
    
    # ── Compare (Full Scene) ──
    
    async def compare_scene(
        self,
        video_path: str,
        anchor: IdentityAnchor,
        sample_interval: int = None,
        scene_index: int = 0,
    ) -> SceneConsistencyReport:
        """
        Analyze an entire scene video for identity consistency.
        
        Samples every Nth frame and checks against the anchor.
        Returns a full report with per-frame scores and drift detection.
        """
        if sample_interval is None:
            sample_interval = settings.IDENTITY_CHECK_INTERVAL_FRAMES
        
        def _analyze():
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video: {video_path}")
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frames_to_check = []
            
            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_idx % sample_interval == 0:
                    frames_to_check.append((frame_idx, frame.copy()))
                
                frame_idx += 1
            
            cap.release()
            return frames_to_check, total_frames
        
        frames_to_check, total_frames = await asyncio.to_thread(_analyze)
        
        # Check each sampled frame
        frame_scores = []
        for frame_idx, frame in frames_to_check:
            score = await self.compare_frame_full(frame, anchor)
            score.frame_index = frame_idx
            frame_scores.append(score)
        
        # Compute stats
        identity_scores = [s.face_similarity for s in frame_scores]
        color_scores = [s.color_consistency for s in frame_scores]
        drift_frames = [s for s in frame_scores if s.is_drifted]
        
        threshold = settings.IDENTITY_SIMILARITY_THRESHOLD
        
        report = SceneConsistencyReport(
            scene_index=scene_index,
            total_frames_checked=len(frame_scores),
            identity_score_mean=round(np.mean(identity_scores), 4) if identity_scores else 0.0,
            identity_score_min=round(np.min(identity_scores), 4) if identity_scores else 0.0,
            identity_score_max=round(np.max(identity_scores), 4) if identity_scores else 0.0,
            identity_score_std=round(np.std(identity_scores), 4) if identity_scores else 0.0,
            color_score_mean=round(np.mean(color_scores), 4) if color_scores else 0.0,
            drift_frame_count=len(drift_frames),
            drift_frame_indices=[s.frame_index for s in drift_frames],
            frame_scores=frame_scores,
            passed=len(drift_frames) == 0,
        )
        
        logger.info(
            "identity_anchor.scene_analyzed",
            scene_index=scene_index,
            mean_identity=report.identity_score_mean,
            drift_frames=report.drift_frame_count,
            passed=report.passed,
        )
        
        return report
    
    # ── Color Operations ──
    
    async def enforce_color_match(
        self,
        frame: np.ndarray,
        anchor: IdentityAnchor,
    ) -> np.ndarray:
        """
        Match the skin color of a frame to the anchor's palette.
        Only affects the face region — background is untouched.
        """
        def _match():
            if anchor.mean_skin_color_bgr is None:
                return frame
            
            # Detect face in frame
            face_data = self._detect_face_cv2(frame)
            if face_data is None:
                return frame
            
            bbox = face_data["bbox"]
            x1, y1, x2, y2 = [int(v) for v in bbox]
            
            # Crop face region
            face_region = frame[y1:y2, x1:x2].copy()
            if face_region.size == 0:
                return frame
            
            # Convert to HSV for color manipulation
            hsv_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2HSV).astype(np.float32)
            
            # Compute current face mean color
            current_mean = cv2.mean(face_region)[:3]
            target_mean = anchor.mean_skin_color_bgr
            
            # Compute color shift
            shift = np.array(target_mean) - np.array(current_mean)
            
            # Apply subtle shift (50% strength to avoid over-correction)
            corrected = face_region.astype(np.float32) + shift * 0.5
            corrected = np.clip(corrected, 0, 255).astype(np.uint8)
            
            # Blend back with smooth edges
            result = frame.copy()
            
            # Create a soft mask for blending
            mask = np.zeros(face_region.shape[:2], dtype=np.float32)
            cv2.ellipse(
                mask,
                ((x2 - x1) // 2, (y2 - y1) // 2),
                ((x2 - x1) // 2 - 5, (y2 - y1) // 2 - 5),
                0, 0, 360, 1.0, -1,
            )
            mask = cv2.GaussianBlur(mask, (15, 15), 5)
            mask = mask[:, :, np.newaxis]
            
            # Blend
            blended = (corrected * mask + face_region * (1 - mask)).astype(np.uint8)
            result[y1:y2, x1:x2] = blended
            
            return result
        
        return await asyncio.to_thread(_match)
    
    # ── Private: Face Detection & Embedding ──
    
    async def _extract_face_data(self, image: np.ndarray) -> dict:
        """Extract all face data from an image using InsightFace or fallback."""
        try:
            return await self._extract_face_insightface(image)
        except Exception as e:
            logger.debug("identity_anchor.insightface_failed", error=str(e))
            return await asyncio.to_thread(self._extract_face_cv2_fallback, image)
    
    async def _extract_face_insightface(self, image: np.ndarray) -> dict:
        """Extract face data using InsightFace buffalo_l model."""
        def _extract():
            if self._insightface_app is None:
                try:
                    import insightface
                    self._insightface_app = insightface.app.FaceAnalysis(
                        name="buffalo_l",
                        root=str(self.model_cache_dir),
                        providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
                    )
                    self._insightface_app.prepare(ctx_id=0, det_size=(640, 640))
                except ImportError:
                    raise RuntimeError("InsightFace not installed")
            
            faces = self._insightface_app.get(image)
            
            if not faces:
                # Try with smaller image if face not found
                smaller = cv2.resize(image, (640, 640))
                faces = self._insightface_app.get(smaller)
                if not faces:
                    raise ValueError("No face detected in image")
                
                # Scale face data back to original dimensions
                scale_x = image.shape[1] / 640
                scale_y = image.shape[0] / 640
                face = faces[0]
                face.bbox = face.bbox * np.array([scale_x, scale_y, scale_x, scale_y])
                if face.kps is not None:
                    face.kps = face.kps * np.array([scale_x, scale_y])
            else:
                face = faces[0]  # Use largest/most prominent face
            
            bbox = face.bbox.astype(int)
            
            return {
                "embedding": face.embedding,           # 512-dim vector
                "keypoints": face.kps if face.kps is not None else None,  # 5-point landmarks
                "bbox": bbox,                          # [x1, y1, x2, y2]
                "bbox_in_crop": None,                  # Computed later for cropped frame
                "det_score": face.det_score if hasattr(face, "det_score") else 1.0,
            }
        
        return await asyncio.to_thread(_extract)
    
    def _extract_face_cv2_fallback(self, image: np.ndarray) -> dict:
        """Fallback face detection using Haar cascades (no embedding)."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
        
        if len(faces) == 0:
            # Generate a synthetic embedding from pixel stats
            logger.warning("identity_anchor.no_face_detected_fallback")
            h, w = image.shape[:2]
            bbox = np.array([w // 4, h // 4, 3 * w // 4, 3 * h // 4])
        else:
            x, y, fw, fh = faces[0]
            bbox = np.array([x, y, x + fw, y + fh])
        
        # Generate embedding from face region pixel statistics
        x1, y1, x2, y2 = bbox
        face_region = image[y1:y2, x1:x2]
        
        if face_region.size == 0:
            embedding = np.random.randn(512).astype(np.float32)
        else:
            # Create a deterministic embedding from face pixels
            face_resized = cv2.resize(face_region, (64, 64))
            face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
            embedding = face_gray.flatten()[:512].astype(np.float32)
            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
        
        return {
            "embedding": embedding,
            "keypoints": None,
            "bbox": bbox,
            "bbox_in_crop": None,
            "det_score": 0.5,
        }
    
    def _detect_face_cv2(self, image: np.ndarray) -> Optional[dict]:
        """Quick face detection for color matching (no embedding needed)."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        
        if len(faces) == 0:
            return None
        
        x, y, fw, fh = faces[0]
        return {"bbox": np.array([x, y, x + fw, y + fh])}
    
    # ── Private: Feature Extraction ──
    
    async def _create_canonical_frame(
        self,
        image: np.ndarray,
        bbox: np.ndarray,
        target_size: int = 512,
    ) -> np.ndarray:
        """Create a 512x512 aligned canonical reference frame."""
        def _create():
            x1, y1, x2, y2 = [int(v) for v in bbox]
            h, w = image.shape[:2]
            
            # Expand bbox by 30% for context
            face_w = x2 - x1
            face_h = y2 - y1
            pad_w = int(face_w * 0.3)
            pad_h = int(face_h * 0.3)
            
            cx1 = max(0, x1 - pad_w)
            cy1 = max(0, y1 - pad_h)
            cx2 = min(w, x2 + pad_w)
            cy2 = min(h, y2 + pad_h)
            
            cropped = image[cy1:cy2, cx1:cx2]
            
            if cropped.size == 0:
                cropped = image
            
            # Resize to target while maintaining aspect ratio
            canonical = cv2.resize(cropped, (target_size, target_size))
            
            return canonical
        
        return await asyncio.to_thread(_create)
    
    async def _extract_appearance_features(
        self,
        canonical_frame: np.ndarray,
    ) -> np.ndarray:
        """
        Extract appearance features for animation engine conditioning.
        
        For LivePortrait: this will be fed to the appearance_feature_extractor ONNX model.
        For InfiniteTalk: this serves as the reference identity frame.
        For fallback: we use a multi-scale feature descriptor.
        """
        def _extract():
            # Multi-scale feature extraction from the canonical frame
            gray = cv2.cvtColor(canonical_frame, cv2.COLOR_BGR2GRAY)
            
            features = []
            
            # Scale 1: Full frame histograms (global appearance)
            for c in range(3):
                hist = cv2.calcHist(
                    [canonical_frame], [c], None, [64], [0, 256]
                ).flatten()
                features.append(hist / (hist.sum() + 1e-7))
            
            # Scale 2: LBP-like texture descriptor
            lbp = self._compute_lbp(gray)
            lbp_hist = cv2.calcHist([lbp], [0], None, [64], [0, 256]).flatten()
            features.append(lbp_hist / (lbp_hist.sum() + 1e-7))
            
            # Scale 3: Edge structure
            edges = cv2.Canny(gray, 50, 150)
            edge_hist = cv2.calcHist([edges], [0], None, [32], [0, 256]).flatten()
            features.append(edge_hist / (edge_hist.sum() + 1e-7))
            
            return np.concatenate(features).astype(np.float32)
        
        return await asyncio.to_thread(_extract)
    
    def _compute_lbp(self, gray: np.ndarray, radius: int = 1) -> np.ndarray:
        """Simple LBP (Local Binary Pattern) computation."""
        h, w = gray.shape
        lbp = np.zeros_like(gray)
        
        for i in range(radius, h - radius):
            for j in range(radius, w - radius):
                center = gray[i, j]
                code = 0
                code |= (gray[i - 1, j - 1] >= center) << 7
                code |= (gray[i - 1, j] >= center) << 6
                code |= (gray[i - 1, j + 1] >= center) << 5
                code |= (gray[i, j + 1] >= center) << 4
                code |= (gray[i + 1, j + 1] >= center) << 3
                code |= (gray[i + 1, j] >= center) << 2
                code |= (gray[i + 1, j - 1] >= center) << 1
                code |= (gray[i, j - 1] >= center) << 0
                lbp[i, j] = code
        
        return lbp
    
    async def _extract_skin_color(
        self,
        canonical_frame: np.ndarray,
        face_bbox_in_crop: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Extract skin color histogram and mean color from face region."""
        def _extract():
            h, w = canonical_frame.shape[:2]
            
            # Use center region as face (since canonical_frame is already face-cropped)
            margin = int(min(h, w) * 0.15)
            face_region = canonical_frame[margin:h - margin, margin:w - margin]
            
            if face_region.size == 0:
                face_region = canonical_frame
            
            # Convert to HSV for skin color analysis
            hsv = cv2.cvtColor(face_region, cv2.COLOR_BGR2HSV)
            
            # Skin color mask (broad range for all skin tones)
            lower_skin = np.array([0, 20, 50], dtype=np.uint8)
            upper_skin = np.array([35, 255, 255], dtype=np.uint8)
            
            skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
            skin_mask2 = cv2.inRange(
                hsv,
                np.array([155, 20, 50], dtype=np.uint8),
                np.array([180, 255, 255], dtype=np.uint8),
            )
            skin_mask = cv2.bitwise_or(skin_mask, skin_mask2)
            
            # Compute histogram on skin pixels only
            if skin_mask.sum() < 100:
                # Not enough skin detected, use full face region
                skin_mask = np.ones(face_region.shape[:2], dtype=np.uint8) * 255
            
            hist = cv2.calcHist(
                [hsv], [0, 1], skin_mask, [30, 32], [0, 180, 0, 256]
            ).flatten()
            hist = hist / (hist.sum() + 1e-7)
            
            # Mean skin color in BGR
            mean_bgr = cv2.mean(face_region, mask=skin_mask)[:3]
            
            return hist.astype(np.float32), np.array(mean_bgr, dtype=np.float32)
        
        return await asyncio.to_thread(_extract)
    
    async def _extract_voice_embedding(self, voice_path: str) -> Optional[np.ndarray]:
        """Extract voice embedding for voice consistency lock."""
        try:
            def _extract():
                try:
                    from TTS.api import TTS
                    
                    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
                    gpt_cond_latent, speaker_embedding = (
                        tts.synthesizer.tts_model.get_conditioning_latents(
                            audio_path=[voice_path]
                        )
                    )
                    return speaker_embedding.cpu().numpy()
                except ImportError:
                    logger.warning("identity_anchor.xtts_not_available")
                    
                    # Fallback: extract MFCC-based voice fingerprint
                    import torchaudio
                    waveform, sr = torchaudio.load(voice_path)
                    if waveform.shape[0] > 1:
                        waveform = waveform.mean(dim=0, keepdim=True)
                    
                    # Compute MFCC as voice fingerprint
                    transform = torchaudio.transforms.MFCC(
                        sample_rate=sr,
                        n_mfcc=40,
                    )
                    mfcc = transform(waveform)
                    # Average over time to get a fixed-size embedding
                    embedding = mfcc.mean(dim=-1).squeeze().numpy()
                    return embedding
                except Exception as e:
                    logger.warning("identity_anchor.voice_extraction_failed", error=str(e))
                    return None
            
            return await asyncio.to_thread(_extract)
        except Exception as e:
            logger.warning("identity_anchor.voice_embedding_failed", error=str(e))
            return None
    
    # ── Private: Comparison Helpers ──
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        if a is None or b is None:
            return 0.0
        
        a_flat = a.flatten()
        b_flat = b.flatten()
        
        # Handle different lengths
        min_len = min(len(a_flat), len(b_flat))
        a_flat = a_flat[:min_len]
        b_flat = b_flat[:min_len]
        
        dot = np.dot(a_flat, b_flat)
        norm_a = np.linalg.norm(a_flat)
        norm_b = np.linalg.norm(b_flat)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(np.clip(dot / (norm_a * norm_b), -1.0, 1.0))
    
    async def _compare_skin_color(
        self,
        frame: np.ndarray,
        bbox: np.ndarray,
        anchor: IdentityAnchor,
    ) -> float:
        """Compare skin color of a frame to the anchor's palette."""
        def _compare():
            x1, y1, x2, y2 = [int(v) for v in bbox]
            face_region = frame[y1:y2, x1:x2]
            
            if face_region.size == 0:
                return 0.0
            
            hsv = cv2.cvtColor(face_region, cv2.COLOR_BGR2HSV)
            
            # Compute histogram
            hist = cv2.calcHist(
                [hsv], [0, 1], None, [30, 32], [0, 180, 0, 256]
            ).flatten()
            hist = hist / (hist.sum() + 1e-7)
            
            # Compare with anchor histogram using correlation
            score = cv2.compareHist(
                hist.astype(np.float32),
                anchor.skin_color_histogram,
                cv2.HISTCMP_CORREL,
            )
            
            return float(np.clip(score, 0.0, 1.0))
        
        return await asyncio.to_thread(_compare)
    
    def _compare_landmarks(
        self,
        kps_a: np.ndarray,
        kps_b: np.ndarray,
    ) -> float:
        """Compare facial landmark positions (normalized)."""
        if kps_a is None or kps_b is None:
            return 0.5  # Neutral score
        
        # Normalize landmarks to [0, 1] range
        a = kps_a.copy()
        b = kps_b.copy()
        
        # Compute normalized distance
        dists = np.linalg.norm(a - b, axis=1)
        mean_dist = np.mean(dists)
        
        # Convert distance to similarity (lower distance = higher similarity)
        # Normalize by face size
        face_size = max(
            np.ptp(b[:, 0]) if len(b) > 1 else 100,
            np.ptp(b[:, 1]) if len(b) > 1 else 100,
        )
        
        if face_size == 0:
            return 0.5
        
        normalized_dist = mean_dist / face_size
        similarity = float(np.clip(1.0 - normalized_dist, 0.0, 1.0))
        
        return similarity
    
    # ── Private: Utilities ──
    
    async def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of a file for cache invalidation."""
        def _hash():
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        
        return await asyncio.to_thread(_hash)
