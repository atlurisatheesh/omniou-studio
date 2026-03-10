"""
utils/model_downloader.py — Atomic model downloads with resume, checksum, and progress (Phase 12).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import threading
import time
from pathlib import Path
from typing import Callable, Dict, Optional
from urllib.request import Request, urlopen

import structlog

log = structlog.get_logger(__name__)

MODEL_MANIFEST: Dict[str, Dict] = {
    "GFPGANv1.4.pth": {
        "url": "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth",
        "sha256": "e2cd4703ab14f4d01fd1383a8a8b266f9a5833dacee8e6a79d3bf21a1b6be5ad",
        "size_mb": 332,
    },
    "buffalo_l.zip": {
        "url": "https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip",
        "sha256": None,
        "size_mb": 326,
    },
    "liveportrait_appearance.onnx": {
        "url": "https://huggingface.co/warmshao/LivePortrait/resolve/main/appearance_feature_extractor.onnx",
        "sha256": None,
        "size_mb": 63,
    },
    "liveportrait_motion.onnx": {
        "url": "https://huggingface.co/warmshao/LivePortrait/resolve/main/motion_extractor.onnx",
        "sha256": None,
        "size_mb": 28,
    },
    "liveportrait_warp.onnx": {
        "url": "https://huggingface.co/warmshao/LivePortrait/resolve/main/warping_spade.onnx",
        "sha256": None,
        "size_mb": 194,
    },
    "musetalk_unet.onnx": {
        "url": "https://huggingface.co/TMElyralab/MuseTalk/resolve/main/musetalk/pytorch_model.bin",
        "sha256": None,
        "size_mb": 401,
    },
}

_download_locks: Dict[str, threading.Lock] = {}
_locks_mutex = threading.Lock()


def _get_lock(model_name: str) -> threading.Lock:
    with _locks_mutex:
        if model_name not in _download_locks:
            _download_locks[model_name] = threading.Lock()
        return _download_locks[model_name]


def _publish_progress(model_name: str, pct: float, status: str, message: str = ""):
    try:
        import redis as sync_redis
        from app.config import settings
        r = sync_redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.publish("cloneai:model_downloads", json.dumps({
            "type": "model_download", "model": model_name,
            "pct": round(pct, 1), "status": status, "message": message, "ts": time.time(),
        }))
    except Exception:
        pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_checksum(path: Path, expected: str, model_name: str) -> bool:
    if not expected:
        return True
    _publish_progress(model_name, 99.0, "verifying", "Verifying integrity…")
    actual = _sha256(path)
    if actual != expected:
        log.error("checksum_mismatch", model=model_name, expected=expected, actual=actual)
        return False
    return True


def download_model(
    model_name: str,
    dest_dir: Path,
    on_progress: Optional[Callable[[float, str], None]] = None,
    retries: int = 3,
) -> Path:
    manifest = MODEL_MANIFEST.get(model_name)
    if not manifest:
        raise ValueError(f"Unknown model '{model_name}'.")

    dest_dir.mkdir(parents=True, exist_ok=True)
    final_path = dest_dir / model_name
    tmp_path = dest_dir / f"{model_name}.tmp"

    if final_path.exists():
        if _verify_checksum(final_path, manifest.get("sha256", ""), model_name):
            return final_path
        else:
            final_path.unlink()

    lock = _get_lock(model_name)
    with lock:
        if final_path.exists():
            return final_path

        url = manifest["url"]
        expected = manifest.get("sha256", "")

        for attempt in range(1, retries + 1):
            try:
                _download_attempt(model_name, url, tmp_path, on_progress, attempt)
                break
            except Exception as e:
                log.warning("download_attempt_failed", model=model_name, attempt=attempt, error=str(e))
                if attempt == retries:
                    if tmp_path.exists():
                        tmp_path.unlink()
                    raise
                time.sleep(2 ** attempt)

        if not _verify_checksum(tmp_path, expected, model_name):
            tmp_path.unlink()
            raise RuntimeError(f"Checksum verification failed for {model_name}")

        shutil.move(str(tmp_path), str(final_path))
        _publish_progress(model_name, 100.0, "complete", f"Downloaded {model_name}")
        return final_path


def _download_attempt(model_name, url, tmp_path, on_progress, attempt):
    headers = {"User-Agent": "CloneAI/1.0"}
    resume_from = 0
    if tmp_path.exists():
        resume_from = tmp_path.stat().st_size
        if resume_from > 0:
            headers["Range"] = f"bytes={resume_from}-"

    req = Request(url, headers=headers)
    response = urlopen(req, timeout=30)
    total_size = int(response.headers.get("Content-Length", 0))
    if resume_from and response.status == 206:
        total_size += resume_from
    elif response.status == 200 and resume_from:
        resume_from = 0

    downloaded = resume_from
    mode = "ab" if resume_from > 0 else "wb"
    with open(tmp_path, mode) as f:
        while True:
            chunk = response.read(1 << 17)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            pct = downloaded / total_size * 100 if total_size > 0 else min(downloaded / (1 << 29) * 100, 99.0)
            _publish_progress(model_name, pct, "downloading", f"Attempt {attempt}: {downloaded >> 20} MB")
            if on_progress:
                on_progress(pct, f"{downloaded >> 20} MB downloaded")


async def download_model_async(model_name: str, dest_dir: Path, on_progress=None) -> Path:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: download_model(model_name, dest_dir, on_progress))


async def download_all(dest_dir: Path):
    results = {}
    for name in MODEL_MANIFEST:
        try:
            path = await download_model_async(name, dest_dir)
            results[name] = {"status": "ok", "path": str(path)}
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}
    return results
