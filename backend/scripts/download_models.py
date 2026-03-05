#!/usr/bin/env python3
"""
CLONEAI ULTRA — AI Model Downloader
=====================================
Downloads all required AI models for the CloneAI Ultra pipeline.
Run: python scripts/download_models.py [--force]

Models downloaded:
  1. LivePortrait ONNX     (~800 MB) — Face animation
  2. MuseTalk 1.5          (~1.2 GB) — Lip synchronization
  3. GFPGAN v1.4           (~350 MB) — Face enhancement
  4. InsightFace buffalo_l (~1.5 GB) — Face detection/analysis
  5. Real-ESRGAN x2        (~65 MB)  — Background upscaler (optional)

Total: ~4 GB first-time download, then cached.
"""

import argparse
import hashlib
import os
import shutil
import sys
import time
import urllib.request
from pathlib import Path

# ── Optional: tqdm progress bars ──
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# ── Constants ──
BASE_MODEL_DIR = Path(__file__).resolve().parent.parent / "models"

MODELS = {
    "liveportrait": {
        "description": "LivePortrait ONNX — Face Animation (3 models)",
        "dir": "liveportrait",
        "files": [
            {
                "filename": "appearance_feature_extractor.onnx",
                "source": "huggingface",
                "repo_id": "KwaiVGI/LivePortrait",
                "repo_filename": "liveportrait_onnx/appearance_feature_extractor.onnx",
            },
            {
                "filename": "motion_extractor.onnx",
                "source": "huggingface",
                "repo_id": "KwaiVGI/LivePortrait",
                "repo_filename": "liveportrait_onnx/motion_extractor.onnx",
            },
            {
                "filename": "warping_module.onnx",
                "source": "huggingface",
                "repo_id": "KwaiVGI/LivePortrait",
                "repo_filename": "liveportrait_onnx/warping_module.onnx",
            },
        ],
    },
    "musetalk": {
        "description": "MuseTalk 1.5 — Lip Synchronization",
        "dir": "musetalk",
        "files": [
            {
                "filename": "musetalk.json",
                "source": "huggingface",
                "repo_id": "TMElyralab/MuseTalk",
                "repo_filename": "models/musetalk/musetalk.json",
            },
            {
                "filename": "pytorch_model.bin",
                "source": "huggingface",
                "repo_id": "TMElyralab/MuseTalk",
                "repo_filename": "models/musetalk/pytorch_model.bin",
            },
        ],
    },
    "musetalk_vae": {
        "description": "Stable Diffusion VAE — Required by MuseTalk",
        "dir": "musetalk/vae",
        "files": [
            {
                "filename": "diffusion_pytorch_model.bin",
                "source": "huggingface",
                "repo_id": "stabilityai/sd-vae-ft-mse",
                "repo_filename": "diffusion_pytorch_model.bin",
            },
            {
                "filename": "config.json",
                "source": "huggingface",
                "repo_id": "stabilityai/sd-vae-ft-mse",
                "repo_filename": "config.json",
            },
        ],
    },
    "gfpgan": {
        "description": "GFPGAN v1.4 — Face Enhancement/Restoration",
        "dir": "gfpgan",
        "files": [
            {
                "filename": "GFPGANv1.4.pth",
                "source": "url",
                "url": "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth",
                "size_mb": 348,
            },
        ],
    },
    "realesrgan": {
        "description": "Real-ESRGAN x2 — Background Upscaler",
        "dir": "realesrgan",
        "files": [
            {
                "filename": "RealESRGAN_x2plus.pth",
                "source": "url",
                "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth",
                "size_mb": 64,
            },
        ],
    },
}


# ── Progress Reporter ──

class DownloadProgressBar:
    """Shows download progress, tqdm if available, else dots."""

    def __init__(self, filename: str, total_size: int = 0):
        self.filename = filename
        self.total_size = total_size
        self.downloaded = 0
        self.last_print = 0
        self._bar = None

        if HAS_TQDM and total_size > 0:
            self._bar = tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=f"  {filename[:40]:<40}",
                ncols=90,
            )

    def update(self, block_num, block_size, total_size):
        if total_size > 0:
            self.total_size = total_size
        self.downloaded = block_num * block_size

        if self._bar:
            if self._bar.total != self.total_size and self.total_size > 0:
                self._bar.total = self.total_size
            self._bar.update(block_size)
        else:
            # Fallback: print dots
            now = time.time()
            if now - self.last_print > 2.0:
                if self.total_size > 0:
                    pct = min(100, int(self.downloaded / self.total_size * 100))
                    print(f"\r  {self.filename[:40]:<40} {pct:>3}%", end="", flush=True)
                else:
                    mb = self.downloaded / (1024 * 1024)
                    print(f"\r  {self.filename[:40]:<40} {mb:.1f} MB", end="", flush=True)
                self.last_print = now

    def close(self):
        if self._bar:
            self._bar.close()
        else:
            print()  # newline after dots


def download_from_url(url: str, dest_path: Path, force: bool = False) -> bool:
    """Download a file from a direct URL."""
    if dest_path.exists() and dest_path.stat().st_size > 0 and not force:
        print(f"  [SKIP] {dest_path.name} — already exists ({dest_path.stat().st_size / 1024 / 1024:.1f} MB)")
        return True

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")

    try:
        progress = DownloadProgressBar(dest_path.name)
        urllib.request.urlretrieve(url, str(tmp_path), reporthook=progress.update)
        progress.close()
        shutil.move(str(tmp_path), str(dest_path))
        size_mb = dest_path.stat().st_size / (1024 * 1024)
        print(f"  [OK]   {dest_path.name} — {size_mb:.1f} MB")
        return True
    except Exception as e:
        print(f"  [FAIL] {dest_path.name} — {e}")
        if tmp_path.exists():
            tmp_path.unlink()
        return False


def download_from_huggingface(repo_id: str, repo_filename: str, dest_path: Path, force: bool = False) -> bool:
    """Download a file from HuggingFace Hub."""
    if dest_path.exists() and dest_path.stat().st_size > 0 and not force:
        print(f"  [SKIP] {dest_path.name} — already exists ({dest_path.stat().st_size / 1024 / 1024:.1f} MB)")
        return True

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("  [WARN] huggingface_hub not installed. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub>=0.23.0"])
        from huggingface_hub import hf_hub_download

    try:
        print(f"  Downloading {repo_id}/{repo_filename}...")
        cached_path = hf_hub_download(
            repo_id=repo_id,
            filename=repo_filename,
            local_dir=None,
        )
        shutil.copy2(cached_path, str(dest_path))
        size_mb = dest_path.stat().st_size / (1024 * 1024)
        print(f"  [OK]   {dest_path.name} — {size_mb:.1f} MB")
        return True
    except Exception as e:
        print(f"  [FAIL] {dest_path.name} — {e}")
        return False


def download_insightface(model_dir: Path, force: bool = False) -> bool:
    """
    Download InsightFace buffalo_l model.
    InsightFace auto-downloads on first use, but we trigger it here to pre-cache.
    """
    insightface_dir = model_dir / "insightface" / "models" / "buffalo_l"

    # Check if already downloaded (buffalo_l has multiple .onnx files)
    if insightface_dir.exists() and any(insightface_dir.glob("*.onnx")) and not force:
        onnx_count = len(list(insightface_dir.glob("*.onnx")))
        print(f"  [SKIP] InsightFace buffalo_l — already cached ({onnx_count} ONNX files)")
        return True

    print("  Downloading InsightFace buffalo_l (this uses insightface's built-in downloader)...")

    try:
        import insightface
        from insightface.app import FaceAnalysis

        # This triggers automatic download of buffalo_l model pack
        fa = FaceAnalysis(
            name="buffalo_l",
            root=str(model_dir / "insightface"),
            providers=["CPUExecutionProvider"],
        )
        fa.prepare(ctx_id=0, det_size=(640, 640))
        print("  [OK]   InsightFace buffalo_l — ready")
        return True
    except ImportError:
        print("  [WARN] insightface package not installed. Skipping.")
        print("         Install with: pip install insightface onnxruntime")
        return False
    except Exception as e:
        print(f"  [FAIL] InsightFace buffalo_l — {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download all AI models required by CloneAI Ultra"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if files already exist",
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default=str(BASE_MODEL_DIR),
        help=f"Model directory (default: {BASE_MODEL_DIR})",
    )
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help="Download only specific model set (liveportrait, musetalk, gfpgan, realesrgan, insightface)",
    )
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("  CLONEAI ULTRA — Model Downloader")
    print("=" * 70)
    print(f"  Model directory: {model_dir.resolve()}")
    print(f"  Force re-download: {args.force}")
    if not HAS_TQDM:
        print("  TIP: Install tqdm for progress bars: pip install tqdm")
    print("=" * 70)
    print()

    results = {}
    total_start = time.time()

    # Filter models if --only specified
    models_to_download = MODELS
    if args.only:
        if args.only in MODELS:
            models_to_download = {args.only: MODELS[args.only]}
        elif args.only == "insightface":
            models_to_download = {}  # handled separately below
        else:
            print(f"Unknown model: {args.only}")
            print(f"Available: {', '.join(list(MODELS.keys()) + ['insightface'])}")
            sys.exit(1)

    # Download each model set
    for model_key, model_info in models_to_download.items():
        print(f"[{model_key.upper()}] {model_info['description']}")
        dest_dir = model_dir / model_info["dir"]
        dest_dir.mkdir(parents=True, exist_ok=True)

        all_ok = True
        for file_info in model_info["files"]:
            dest_path = dest_dir / file_info["filename"]

            if file_info["source"] == "url":
                success = download_from_url(file_info["url"], dest_path, args.force)
            elif file_info["source"] == "huggingface":
                success = download_from_huggingface(
                    file_info["repo_id"],
                    file_info["repo_filename"],
                    dest_path,
                    args.force,
                )
            else:
                print(f"  [WARN] Unknown source: {file_info['source']}")
                success = False

            if not success:
                all_ok = False

        results[model_key] = all_ok
        print()

    # InsightFace (uses its own downloader)
    if args.only is None or args.only == "insightface":
        print("[INSIGHTFACE] InsightFace buffalo_l — Face Detection/Analysis")
        results["insightface"] = download_insightface(model_dir, args.force)
        print()

    # ── Summary ──
    elapsed = time.time() - total_start
    print("=" * 70)
    print("  DOWNLOAD SUMMARY")
    print("=" * 70)

    ok_count = 0
    fail_count = 0
    skip_note = ""

    for name, success in results.items():
        status = "READY" if success else "FAILED"
        icon = "[OK]  " if success else "[FAIL]"
        print(f"  {icon} {name:<20} — {status}")
        if success:
            ok_count += 1
        else:
            fail_count += 1

    print(f"\n  Total time: {elapsed:.1f}s")
    print(f"  Ready: {ok_count} | Failed: {fail_count}")

    if fail_count > 0:
        print("\n  Some models failed to download. The pipeline will use fallback engines")
        print("  for any missing models. Re-run with --force to retry.")
        print("  Check your internet connection and try again.")

    # Show total disk usage
    total_size = 0
    for root, dirs, files in os.walk(model_dir):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    print(f"\n  Total model cache size: {total_size / (1024 * 1024 * 1024):.2f} GB")
    print("=" * 70)

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
