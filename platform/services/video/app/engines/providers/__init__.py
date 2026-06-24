"""Ominou Video Engine Adapters — Proprietary video generation engines."""
from .base import VideoProvider, ProviderResult
from .local_provider import LocalProvider
from .sora_provider import SoraProvider
from .kling_provider import KlingProvider
from .seedance_provider import SeedanceProvider
from .veo_provider import VeoProvider
from .runway_provider import RunwayProvider

PROVIDERS: dict[str, type[VideoProvider]] = {
    "ominou_local": LocalProvider,
    "ominou_prime": SoraProvider,
    "ominou_flow": KlingProvider,
    "ominou_motion": SeedanceProvider,
    "ominou_vision": VeoProvider,
    "ominou_studio": RunwayProvider,
}


def get_provider(name: str) -> VideoProvider:
    """Get an instantiated provider by name."""
    cls = PROVIDERS.get(name)
    if not cls:
        raise ValueError(f"Unknown provider: {name}. Available: {list(PROVIDERS.keys())}")
    return cls()


def get_available_providers() -> list[dict]:
    """Return list of providers with their availability status."""
    results = []
    for name, cls in PROVIDERS.items():
        p = cls()
        results.append({
            "id": name,
            "name": p.display_name,
            "company": p.company,
            "strengths": p.strengths,
            "max_duration": p.max_duration,
            "supports_audio": p.supports_audio,
            "available": p.is_available(),
        })
    return results
