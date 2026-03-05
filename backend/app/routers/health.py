"""
CLONEAI ULTRA — Health Check Router
"""

from fastapi import APIRouter

from ..config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "CloneAI Ultra API",
        "version": "2.0.0",
        "voice_engine": settings.VOICE_ENGINE,
        "face_engine": settings.FACE_ENGINE,
        "lipsync_engine": settings.LIPSYNC_ENGINE,
    }


@router.get("/health/gpu")
async def gpu_check():
    """Check GPU availability and memory."""
    import torch

    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        props = torch.cuda.get_device_properties(0)
        gpu_mem_total = props.total_mem / (1024**3)
        gpu_mem_used = torch.cuda.memory_allocated(0) / (1024**3)
        return {
            "gpu_available": True,
            "gpu_name": gpu_name,
            "gpu_memory_total_gb": round(gpu_mem_total, 1),
            "gpu_memory_used_gb": round(gpu_mem_used, 2),
            "cuda_version": torch.version.cuda,
        }
    return {"gpu_available": False, "fallback": "cpu"}
