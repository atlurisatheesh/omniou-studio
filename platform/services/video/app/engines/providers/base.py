"""Base class for all video generation providers."""
import abc
import os
from dataclasses import dataclass, field


@dataclass
class ProviderResult:
    """Standardized result from any video provider."""
    status: str  # "completed", "failed", "processing"
    scene_file: str | None = None
    file_url: str | None = None
    duration_seconds: float = 0
    resolution: str = ""
    has_audio: bool = False
    provider: str = ""
    attempt: int = 1
    error: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


class VideoProvider(abc.ABC):
    """Abstract base for video generation providers."""

    display_name: str = "Unknown"
    company: str = "Unknown"
    strengths: list[str] = []
    max_duration: int = 10
    supports_audio: bool = False
    env_key: str = ""

    def is_available(self) -> bool:
        """Check if this provider's API key is configured."""
        return bool(os.getenv(self.env_key)) if self.env_key else False

    @abc.abstractmethod
    async def generate(
        self,
        prompt: str,
        duration_seconds: int = 5,
        resolution: str = "1080p",
        style: str = "cinematic",
        **kwargs,
    ) -> ProviderResult:
        """Generate a video clip from a text prompt."""
        ...

    async def generate_with_audio(
        self,
        prompt: str,
        duration_seconds: int = 5,
        resolution: str = "1080p",
        **kwargs,
    ) -> ProviderResult:
        """Generate video with synchronized audio (if supported)."""
        return await self.generate(prompt, duration_seconds, resolution, **kwargs)
