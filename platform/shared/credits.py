"""Credit tracking and usage metering."""
from dataclasses import dataclass

CREDIT_COSTS = {
    "voice_tts": 1,
    "voice_clone": 5,
    "voice_dub": 10,
    "design_template": 1,
    "design_ai_generate": 3,
    "design_remove_bg": 2,
    "code_generate": 2,
    "code_deploy": 5,
    "video_clone": 10,
    "video_generate": 15,
    "video_subtitle": 3,
    "writer_blog": 3,
    "writer_copy": 1,
    "writer_script": 5,
    "writer_seo": 2,
    "music_generate": 5,
    "music_sfx": 2,
    "workflow_run": 0,  # charged per step
}


@dataclass
class UsageResult:
    allowed: bool
    credits_used: int
    credits_remaining: int
    message: str


def check_credits(user_credits: int, action: str) -> UsageResult:
    cost = CREDIT_COSTS.get(action, 1)
    if user_credits >= cost:
        return UsageResult(True, cost, user_credits - cost, "OK")
    return UsageResult(False, 0, user_credits, f"Insufficient credits. Need {cost}, have {user_credits}")
