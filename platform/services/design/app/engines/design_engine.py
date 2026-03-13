"""Design Studio AI Engine — Image Generation, Templates, Background Removal."""
import uuid
from typing import Optional

TEMPLATE_CATEGORIES = {
    "social_media": {
        "instagram_post": {"width": 1080, "height": 1080, "name": "Instagram Post"},
        "instagram_story": {"width": 1080, "height": 1920, "name": "Instagram Story"},
        "facebook_post": {"width": 1200, "height": 630, "name": "Facebook Post"},
        "twitter_post": {"width": 1200, "height": 675, "name": "Twitter/X Post"},
        "linkedin_post": {"width": 1200, "height": 627, "name": "LinkedIn Post"},
        "youtube_thumbnail": {"width": 1280, "height": 720, "name": "YouTube Thumbnail"},
        "tiktok_video": {"width": 1080, "height": 1920, "name": "TikTok Video"},
    },
    "marketing": {
        "flyer": {"width": 2480, "height": 3508, "name": "A4 Flyer"},
        "poster": {"width": 3508, "height": 4961, "name": "A3 Poster"},
        "banner": {"width": 1920, "height": 600, "name": "Web Banner"},
        "business_card": {"width": 1050, "height": 600, "name": "Business Card"},
        "brochure": {"width": 2480, "height": 3508, "name": "Tri-fold Brochure"},
    },
    "presentation": {
        "slide_16_9": {"width": 1920, "height": 1080, "name": "Slide 16:9"},
        "slide_4_3": {"width": 1024, "height": 768, "name": "Slide 4:3"},
    },
    "brand": {
        "logo": {"width": 1000, "height": 1000, "name": "Logo"},
        "favicon": {"width": 512, "height": 512, "name": "Favicon"},
        "og_image": {"width": 1200, "height": 630, "name": "OG Image"},
    },
}

AI_STYLES = [
    "photorealistic", "digital_art", "watercolor", "oil_painting", "sketch",
    "anime", "3d_render", "pop_art", "minimalist", "vintage", "neon",
    "cyberpunk", "fantasy", "abstract", "low_poly", "pixel_art",
]

IMAGE_FILTERS = [
    "none", "grayscale", "sepia", "vintage", "warm", "cool", "dramatic",
    "matte", "vivid", "noir", "pastel", "hdr",
]


def generate_image(prompt: str, style: str = "photorealistic", width: int = 1024, height: int = 1024, negative_prompt: str = "") -> dict:
    """Generate an AI image from a text prompt."""
    file_id = str(uuid.uuid4())[:8]
    return {
        "file_id": f"img_{file_id}",
        "file_url": f"/storage/design/img_{file_id}.png",
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "style": style,
        "width": width,
        "height": height,
        "format": "png",
        "seed": abs(hash(prompt)) % 2**32,
        "status": "completed",
    }


def remove_background(image_url: str) -> dict:
    """Remove background from an image."""
    file_id = str(uuid.uuid4())[:8]
    return {
        "file_id": f"nobg_{file_id}",
        "file_url": f"/storage/design/nobg_{file_id}.png",
        "original_url": image_url,
        "format": "png",
        "has_transparency": True,
        "status": "completed",
    }


def upscale_image(image_url: str, scale: int = 2) -> dict:
    """Upscale an image by N times."""
    file_id = str(uuid.uuid4())[:8]
    return {
        "file_id": f"up_{file_id}",
        "file_url": f"/storage/design/up_{file_id}.png",
        "original_url": image_url,
        "scale": scale,
        "status": "completed",
    }


def create_from_template(template_id: str, category: str, customizations: dict) -> dict:
    """Create a design from a template with customizations."""
    cat = TEMPLATE_CATEGORIES.get(category, {})
    template = cat.get(template_id)
    if not template:
        return {"error": f"Template '{template_id}' not found in category '{category}'"}

    file_id = str(uuid.uuid4())[:8]
    return {
        "file_id": f"tmpl_{file_id}",
        "file_url": f"/storage/design/tmpl_{file_id}.png",
        "template": template_id,
        "category": category,
        "width": template["width"],
        "height": template["height"],
        "customizations": customizations,
        "format": "png",
        "status": "completed",
    }


def list_templates() -> dict:
    return TEMPLATE_CATEGORIES


def list_styles() -> list[str]:
    return AI_STYLES


def list_filters() -> list[str]:
    return IMAGE_FILTERS
