"""
CLONEAI PRO — File Handler Utilities
=====================================
Secure file handling, validation, and cleanup.
"""

import hashlib
import mimetypes
import os
import uuid
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger()

# Strict MIME type validation
VALID_MIMES = {
    "photo": {"image/jpeg", "image/png", "image/webp"},
    "voice": {"audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3", "audio/mp4", "audio/m4a", "audio/flac"},
    "video": {"video/mp4", "video/webm", "video/quicktime"},
}

# Magic bytes for file type verification
MAGIC_BYTES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG"],
    "image/webp": [b"RIFF"],
    "audio/wav": [b"RIFF"],
    "video/mp4": [b"\x00\x00\x00", b"ftyp"],
}


def validate_file_type(file_path: str, expected_category: str) -> bool:
    """
    Validate file type by both MIME type and magic bytes.
    Returns True if valid, raises ValueError if not.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check MIME type
    mime, _ = mimetypes.guess_type(str(path))
    if mime and mime not in VALID_MIMES.get(expected_category, set()):
        raise ValueError(f"Invalid file type: {mime} for category {expected_category}")

    # Check magic bytes
    with open(file_path, "rb") as f:
        header = f.read(16)

    # Basic header check for common formats
    if expected_category == "photo":
        if not (header[:3] == b"\xff\xd8\xff" or  # JPEG
                header[:4] == b"\x89PNG" or         # PNG
                header[:4] == b"RIFF"):             # WebP
            raise ValueError("File does not appear to be a valid image")

    return True


def get_file_hash(file_path: str) -> str:
    """Get SHA-256 hash of a file (for deduplication)."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def cleanup_temp_files(directory: str, max_age_hours: int = 24) -> int:
    """Remove temp files older than max_age_hours."""
    import time

    count = 0
    now = time.time()
    cutoff = now - (max_age_hours * 3600)

    for root, dirs, files in os.walk(directory):
        for f in files:
            fpath = os.path.join(root, f)
            try:
                if os.path.getmtime(fpath) < cutoff:
                    os.remove(fpath)
                    count += 1
            except OSError:
                pass

    logger.info("cleanup.complete", directory=directory, removed=count)
    return count


def ensure_dir(path: str) -> Path:
    """Ensure a directory exists, create if not."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
