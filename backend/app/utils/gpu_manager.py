"""
CLONEAI PRO — GPU Manager
===========================
GPU memory management and device selection.
"""

from typing import Optional

import structlog

logger = structlog.get_logger()


class GPUManager:
    """Manages GPU resources for AI inference."""

    def __init__(self):
        self._device = None
        self._check_gpu()

    def _check_gpu(self):
        """Check GPU availability and set device."""
        try:
            import torch

            if torch.cuda.is_available():
                self._device = "cuda"
                gpu_name = torch.cuda.get_device_name(0)
                total_mem = torch.cuda.get_device_properties(0).total_mem / (1024**3)
                logger.info(
                    "gpu.detected",
                    name=gpu_name,
                    total_memory_gb=round(total_mem, 1),
                    cuda_version=torch.version.cuda,
                )
            else:
                self._device = "cpu"
                logger.warning("gpu.not_available", msg="Using CPU. Inference will be significantly slower.")
        except ImportError:
            self._device = "cpu"
            logger.warning("gpu.torch_not_installed", msg="PyTorch not installed. Using CPU.")

    @property
    def device(self) -> str:
        return self._device

    def get_memory_info(self) -> Optional[dict]:
        """Get current GPU memory usage."""
        if self._device != "cuda":
            return None

        import torch

        allocated = torch.cuda.memory_allocated() / (1024**3)
        reserved = torch.cuda.memory_reserved() / (1024**3)
        total = torch.cuda.get_device_properties(0).total_mem / (1024**3)

        return {
            "allocated_gb": round(allocated, 2),
            "reserved_gb": round(reserved, 2),
            "total_gb": round(total, 2),
            "free_gb": round(total - allocated, 2),
            "utilization_pct": round(allocated / total * 100, 1),
        }

    def clear_cache(self):
        """Clear GPU cache to free memory."""
        if self._device == "cuda":
            import torch
            import gc

            torch.cuda.empty_cache()
            gc.collect()
            logger.info("gpu.cache_cleared")

    def can_fit_model(self, model_size_gb: float) -> bool:
        """Check if a model can fit in available GPU memory."""
        info = self.get_memory_info()
        if info is None:
            return False
        return info["free_gb"] >= model_size_gb
