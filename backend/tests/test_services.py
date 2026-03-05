"""
Tests for service-level functionality: postprocess, quality checker, script AI, storage.
"""

import numpy as np
import pytest


# ─── Post-Processing Layers ───

class TestPostProcessLayers:
    """Test individual cinematic post-processing layers."""

    def _make_frame(self, w=320, h=240):
        """Create a dummy BGR frame."""
        return np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)

    def test_microjitter(self):
        from app.services.postprocess import apply_microjitter

        frame = self._make_frame()
        result = apply_microjitter(frame, max_px=2.0)
        assert result.shape == frame.shape
        assert result.dtype == np.uint8

    def test_film_grain(self):
        from app.services.postprocess import apply_film_grain

        frame = self._make_frame()
        result = apply_film_grain(frame, intensity=0.08)
        assert result.shape == frame.shape
        # Grain should change pixel values
        assert not np.array_equal(result, frame)

    def test_barrel_distortion(self):
        from app.services.postprocess import apply_barrel_distortion

        frame = self._make_frame()
        result = apply_barrel_distortion(frame, strength=0.0003)
        assert result.shape == frame.shape

    def test_depth_of_field(self):
        from app.services.postprocess import apply_depth_of_field

        frame = self._make_frame()
        result = apply_depth_of_field(frame)
        assert result.shape == frame.shape

    def test_color_grade(self):
        from app.services.postprocess import apply_color_grade

        frame = self._make_frame()
        result = apply_color_grade(frame)
        assert result.shape == frame.shape
        assert result.dtype == np.uint8


class TestPostProcessService:
    """Test the full PostProcessService."""

    def test_process_frame_all_layers(self):
        from app.services.postprocess import PostProcessService

        service = PostProcessService()
        frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        result = service.process_frame(frame)
        assert result.shape == frame.shape


# ─── Quality Checker ───

class TestQualityChecker:
    """Test quality checker heuristics."""

    def test_syncnet_heuristic_returns_valid_score(self):
        """SyncNet heuristic should return a score between 0-10."""
        from app.services.quality_checker import QualityChecker

        checker = QualityChecker()
        # Without a real video, the heuristic should return a default
        score = checker._syncnet_heuristic("nonexistent.mp4", None)
        assert 0 <= score <= 10

    def test_ai_detect_heuristic_returns_valid_pct(self):
        """AI detect heuristic should return 0-100."""
        from app.services.quality_checker import QualityChecker

        checker = QualityChecker()
        pct = checker._ai_detect_heuristic("nonexistent.mp4")
        assert 0 <= pct <= 100


# ─── Script AI ───

class TestScriptAI:
    """Test script generation service."""

    def test_template_generation(self):
        from app.services.script_ai import ScriptAIService

        service = ScriptAIService()
        script = service._generate_template("machine learning", "professional", 50)
        words = script.split()
        assert len(words) >= 10
        assert "machine learning" in script.lower()

    def test_template_different_tones(self):
        from app.services.script_ai import ScriptAIService

        service = ScriptAIService()
        for tone in ["professional", "casual", "educational"]:
            script = service._generate_template("AI video", tone, 30)
            assert len(script.split()) > 0


# ─── Storage ───

class TestStorageService:
    """Test storage service (local fallback mode)."""

    @pytest.mark.asyncio
    async def test_local_fallback(self):
        from app.services.storage import StorageService

        service = StorageService()
        service._use_minio = False  # Force local mode

        # file_exists should work locally
        exists = await service.file_exists("nonexistent_file.txt")
        assert exists is False
