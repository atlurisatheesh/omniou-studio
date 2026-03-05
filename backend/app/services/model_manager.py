"""
CLONEAI ULTRA — Model Manager
===============================
Centralized GPU model loading/unloading with memory management.
Supports: Chatterbox, XTTS v2, LivePortrait, MuseTalk, LatentSync,
          GFPGAN, Real-ESRGAN, InsightFace (Section 3-5).
"""

import gc
from pathlib import Path
from typing import Any, Optional

import structlog
import torch

logger = structlog.get_logger()


class ModelManager:
    """
    Manages all AI model lifecycles.

    - Lazy loading: models only load when first requested
    - Singleton cache: each model loaded once, reused across requests
    - Memory management: can unload models to free GPU memory
    """

    def __init__(self, device: str = "cuda", model_cache_dir: str = "./models"):
        self.device = device if torch.cuda.is_available() else "cpu"
        self.model_cache_dir = model_cache_dir
        self._models: dict[str, Any] = {}

        if self.device == "cuda":
            gpu_name = torch.cuda.get_device_name(0)
            gpu_mem = torch.cuda.get_device_properties(0).total_mem / (1024**3)
            logger.info("model_manager.init", device=self.device, gpu=gpu_name, vram_gb=round(gpu_mem, 1))
        else:
            logger.warning("model_manager.init", device="cpu", msg="No GPU detected. Inference will be slower.")

    def get_model(self, model_name: str) -> Optional[Any]:
        return self._models.get(model_name)

    def is_loaded(self, model_name: str) -> bool:
        return model_name in self._models

    def register_model(self, model_name: str, model: Any) -> None:
        self._models[model_name] = model
        logger.info("model_manager.registered", model=model_name)

    # ── Voice Models ──

    def load_chatterbox(self) -> Any:
        """Load Chatterbox TTS model."""
        if self.is_loaded("chatterbox"):
            return self.get_model("chatterbox")

        logger.info("model_manager.loading", model="chatterbox")
        try:
            from chatterbox.tts import ChatterboxTTS
            model = ChatterboxTTS.from_pretrained(device=self.device)
            self.register_model("chatterbox", model)
            return model
        except Exception as e:
            logger.error("model_manager.load_failed", model="chatterbox", error=str(e))
            raise

    def load_xtts(self) -> Any:
        """Load XTTS v2 voice cloning model."""
        if self.is_loaded("xtts_v2"):
            return self.get_model("xtts_v2")

        logger.info("model_manager.loading", model="xtts_v2")
        try:
            from TTS.api import TTS
            from ..config import settings

            model = TTS(
                model_name=settings.XTTS_MODEL_NAME,
                progress_bar=True,
            ).to(self.device)
            self.register_model("xtts_v2", model)
            return model
        except Exception as e:
            logger.error("model_manager.load_failed", model="xtts_v2", error=str(e))
            raise

    # ── Face Models ──

    def load_insightface(self) -> Any:
        """Load InsightFace face analysis model (buffalo_l)."""
        if self.is_loaded("insightface"):
            return self.get_model("insightface")

        logger.info("model_manager.loading", model="insightface")
        try:
            from insightface.app import FaceAnalysis

            app = FaceAnalysis(
                name="buffalo_l",
                root=self.model_cache_dir,
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
            )
            ctx_id = 0 if self.device == "cuda" else -1
            app.prepare(ctx_id=ctx_id, det_size=(640, 640))
            self.register_model("insightface", app)
            return app
        except Exception as e:
            logger.error("model_manager.load_failed", model="insightface", error=str(e))
            raise

    def load_liveportrait(self) -> Any:
        """Load LivePortrait ONNX pipeline."""
        if self.is_loaded("liveportrait"):
            return self.get_model("liveportrait")

        logger.info("model_manager.loading", model="liveportrait")
        lp_dir = Path(self.model_cache_dir) / "liveportrait"

        try:
            import onnxruntime as ort

            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if self.device == "cuda" else ["CPUExecutionProvider"]
            pipeline = {}

            for name in ["appearance_feature_extractor", "motion_extractor", "warping_module"]:
                path = lp_dir / f"{name}.onnx"
                if path.exists():
                    pipeline[name] = ort.InferenceSession(str(path), providers=providers)
                else:
                    logger.warning("model_manager.liveportrait_missing", file=str(path))

            if pipeline:
                self.register_model("liveportrait", pipeline)
            return pipeline
        except Exception as e:
            logger.error("model_manager.load_failed", model="liveportrait", error=str(e))
            raise

    def load_musetalk(self) -> Any:
        """Load MuseTalk 1.5 ONNX models."""
        if self.is_loaded("musetalk"):
            return self.get_model("musetalk")

        logger.info("model_manager.loading", model="musetalk")
        mt_dir = Path(self.model_cache_dir) / "musetalk"

        try:
            import onnxruntime as ort

            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if self.device == "cuda" else ["CPUExecutionProvider"]
            pipeline = {}

            for name in ["musetalk_unet", "musetalk_vae"]:
                path = mt_dir / f"{name}.onnx"
                if path.exists():
                    pipeline[name.replace("musetalk_", "")] = ort.InferenceSession(str(path), providers=providers)

            if pipeline:
                self.register_model("musetalk", pipeline)
            return pipeline
        except Exception as e:
            logger.error("model_manager.load_failed", model="musetalk", error=str(e))
            raise

    # ── Enhancement Models ──

    def load_gfpgan(self) -> Any:
        """Load GFPGAN face enhancement model."""
        if self.is_loaded("gfpgan"):
            return self.get_model("gfpgan")

        logger.info("model_manager.loading", model="gfpgan")
        try:
            from gfpgan import GFPGANer

            model_path = Path(self.model_cache_dir) / "gfpgan" / "GFPGANv1.4.pth"
            if not model_path.exists():
                model_path = "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth"

            model = GFPGANer(
                model_path=str(model_path),
                upscale=2,
                arch="clean",
                channel_multiplier=2,
                bg_upsampler=None,
                device=torch.device(self.device),
            )
            self.register_model("gfpgan", model)
            return model
        except Exception as e:
            logger.error("model_manager.load_failed", model="gfpgan", error=str(e))
            raise

    def load_realesrgan(self) -> Any:
        """Load Real-ESRGAN background upscaler."""
        if self.is_loaded("realesrgan"):
            return self.get_model("realesrgan")

        logger.info("model_manager.loading", model="realesrgan")
        try:
            from realesrgan import RealESRGANer
            from basicsr.archs.rrdbnet_arch import RRDBNet

            model_path = Path(self.model_cache_dir) / "realesrgan" / "RealESRGAN_x4plus.pth"
            net = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)

            upscaler = RealESRGANer(
                scale=4,
                model_path=str(model_path),
                model=net,
                tile=0,
                tile_pad=10,
                pre_pad=0,
                half=True if self.device == "cuda" else False,
                device=torch.device(self.device),
            )
            self.register_model("realesrgan", upscaler)
            return upscaler
        except Exception as e:
            logger.error("model_manager.load_failed", model="realesrgan", error=str(e))
            raise

    # ── Memory Management ──

    def unload_model(self, model_name: str) -> None:
        """Unload a specific model to free memory."""
        if model_name in self._models:
            del self._models[model_name]
            if self.device == "cuda":
                torch.cuda.empty_cache()
            gc.collect()
            logger.info("model_manager.unloaded", model=model_name)

    def unload_all(self) -> None:
        """Unload all models."""
        model_names = list(self._models.keys())
        for name in model_names:
            self.unload_model(name)
        logger.info("model_manager.unloaded_all", count=len(model_names))

    def gpu_memory_status(self) -> dict:
        """Get current GPU memory usage."""
        if self.device != "cuda":
            return {"device": "cpu", "gpu_available": False}

        allocated = torch.cuda.memory_allocated() / (1024**3)
        reserved = torch.cuda.memory_reserved() / (1024**3)
        total = torch.cuda.get_device_properties(0).total_mem / (1024**3)

        return {
            "device": self.device,
            "gpu_name": torch.cuda.get_device_name(0),
            "allocated_gb": round(allocated, 2),
            "reserved_gb": round(reserved, 2),
            "total_gb": round(total, 2),
            "free_gb": round(total - allocated, 2),
            "models_loaded": list(self._models.keys()),
        }
