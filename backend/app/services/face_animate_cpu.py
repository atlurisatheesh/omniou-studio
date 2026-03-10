"""
services/face_animate_cpu.py — CPU-optimised face animation (Phase 12).

Replaces the naive per-frame loop with:
1. Resolution downscaling on CPU (480p → upscale at end)
2. Frame batching via multiprocessing.Pool
3. MFCC feature caching (compute once)
4. Keypoint interpolation (every 3rd frame)
5. Progressive frame writing for live preview
"""

from __future__ import annotations

import math
import multiprocessing as mp
import os
import time
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
import structlog

log = structlog.get_logger(__name__)

CPU_PROCESS_RESOLUTION = (480, 360)
CPU_OUTPUT_RESOLUTION = (854, 480)
KEYPOINT_INTERVAL = 3
WORKER_COUNT = max(1, (os.cpu_count() or 2) - 1)


def extract_audio_features(audio_path: str, total_frames: int, fps: float = 30.0) -> np.ndarray:
    try:
        import librosa
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        hop_length = int(sr / fps)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop_length)
        energy = np.sqrt(np.mean(mfcc ** 2, axis=0))
        if len(energy) < total_frames:
            energy = np.pad(energy, (0, total_frames - len(energy)))
        else:
            energy = energy[:total_frames]
        mx = energy.max()
        if mx > 0:
            energy = energy / mx
        return energy
    except Exception as e:
        log.warning("mfcc_extraction_failed", error=str(e))
        return np.zeros(total_frames)


def detect_face_region(frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(cascade_path)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
    if len(faces) == 0:
        return None
    return max(faces, key=lambda f: f[2] * f[3])


def detect_mouth_region(frame: np.ndarray, face: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
    x, y, w, h = face
    mx = x + w // 4
    my = y + int(h * 0.65)
    mw = w // 2
    mh = h // 4
    return mx, my, mw, mh


def compute_displacement(energy: float, face: Tuple[int, int, int, int], frame_idx: int) -> dict:
    rng = np.random.default_rng(seed=frame_idx)
    return {
        "jaw_open": energy * 0.12,
        "head_sway": math.sin(frame_idx * 0.08) * 1.2 * energy,
        "blink_open": 1.0 if (frame_idx % 120) not in range(3) else 0.2,
        "noise_x": rng.uniform(-0.5, 0.5),
        "noise_y": rng.uniform(-0.5, 0.5),
    }


def interpolate_displacements(d1: dict, d2: dict, t: float) -> dict:
    return {k: d1[k] * (1 - t) + d2[k] * t for k in d1}


def _process_frame_worker(args: tuple) -> bytes:
    frame_bytes, face_rect, mouth_rect, disp = args
    frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        return frame_bytes

    h, w = frame.shape[:2]
    x, y, fw, fh = face_rect
    mx, my, mw, mh = mouth_rect
    jaw_open = disp["jaw_open"]
    head_sway = disp["head_sway"]

    sway_px = int(head_sway * w * 0.005)
    M_sway = np.float32([[1, 0, sway_px], [0, 1, 0]])
    frame = cv2.warpAffine(frame, M_sway, (w, h), borderMode=cv2.BORDER_REPLICATE)

    if jaw_open > 0.01 and my + mh < h and my > 0:
        jaw_pixels = int(jaw_open * fh)
        if jaw_pixels > 0:
            lip_region = frame[my:my + mh, mx:mx + mw]
            stretched = cv2.resize(lip_region, (mw, mh + jaw_pixels))
            if my + stretched.shape[0] <= h and mx + stretched.shape[1] <= w:
                frame[my:my + stretched.shape[0], mx:mx + stretched.shape[1]] = stretched

    blink = disp.get("blink_open", 1.0)
    if blink < 0.9:
        eye_y1 = y + int(fh * 0.2)
        eye_y2 = y + int(fh * 0.45)
        if eye_y1 < eye_y2 <= h:
            frame[eye_y1:eye_y2, x:x + fw] = (frame[eye_y1:eye_y2, x:x + fw] * blink).astype(np.uint8)

    _, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return encoded.tobytes()


class CPUFaceAnimator:
    def __init__(self, workers: int = WORKER_COUNT):
        self.workers = workers

    def animate(
        self,
        face_image_path: str,
        audio_path: str,
        output_path: str,
        duration_sec: float,
        fps: float = 30.0,
        progress_callback=None,
        stream_dir: Optional[str] = None,
    ) -> str:
        start = time.time()
        total_frames = int(duration_sec * fps)
        log.info("cpu_animate_start", frames=total_frames, workers=self.workers)

        source = cv2.imread(face_image_path)
        if source is None:
            raise RuntimeError(f"Cannot read face image: {face_image_path}")
        source_small = cv2.resize(source, CPU_PROCESS_RESOLUTION)

        face_rect = detect_face_region(source_small) or (0, 0, source_small.shape[1], source_small.shape[0])
        mouth_rect = detect_mouth_region(source_small, face_rect)
        audio_energy = extract_audio_features(audio_path, total_frames, fps)

        keypoint_indices = list(range(0, total_frames, KEYPOINT_INTERVAL))
        if total_frames - 1 not in keypoint_indices:
            keypoint_indices.append(total_frames - 1)

        keypoint_disps = {
            idx: compute_displacement(float(audio_energy[idx]), face_rect, idx)
            for idx in keypoint_indices
        }

        all_disps: List[dict] = []
        kp_sorted = sorted(keypoint_disps.keys())
        for i in range(total_frames):
            lo = max(k for k in kp_sorted if k <= i)
            hi = min(k for k in kp_sorted if k >= i)
            if lo == hi:
                all_disps.append(keypoint_disps[lo])
            else:
                t = (i - lo) / (hi - lo)
                all_disps.append(interpolate_displacements(keypoint_disps[lo], keypoint_disps[hi], t))

        _, src_bytes = cv2.imencode(".jpg", source_small, [cv2.IMWRITE_JPEG_QUALITY, 92])
        src_bytes_b = src_bytes.tobytes()

        work_items = [(src_bytes_b, face_rect, mouth_rect, all_disps[i]) for i in range(total_frames)]

        BATCH = 60
        all_frame_bytes: List[bytes] = [b""] * total_frames
        pool_ctx = mp.get_context("spawn")
        with pool_ctx.Pool(processes=self.workers) as pool:
            for batch_start in range(0, total_frames, BATCH):
                batch_end = min(batch_start + BATCH, total_frames)
                results = pool.map(_process_frame_worker, work_items[batch_start:batch_end])
                for j, frame_bytes in enumerate(results):
                    all_frame_bytes[batch_start + j] = frame_bytes
                    if stream_dir:
                        preview_path = Path(stream_dir) / f"frame_{batch_start + j:06d}.jpg"
                        preview_path.write_bytes(frame_bytes)
                if progress_callback:
                    pct = (batch_end / total_frames) * 80
                    progress_callback(pct, f"Animating frame {batch_end}/{total_frames}")

        self._encode_video(all_frame_bytes, output_path, fps, total_frames, progress_callback)
        elapsed = time.time() - start
        log.info("cpu_animate_done", elapsed_sec=round(elapsed, 1))
        return output_path

    def _encode_video(self, frame_bytes_list, output_path, fps, total_frames, progress_callback):
        w, h = CPU_OUTPUT_RESOLUTION
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        tmp_video = output_path.replace(".mp4", "_tmp.mp4")
        writer = cv2.VideoWriter(tmp_video, fourcc, fps, (w, h))
        try:
            for i, fb in enumerate(frame_bytes_list):
                arr = np.frombuffer(fb, np.uint8)
                frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if frame is not None:
                    frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_LANCZOS4)
                    writer.write(frame)
                if progress_callback and i % 30 == 0:
                    pct = 80 + (i / total_frames) * 20
                    progress_callback(pct, "Encoding video…")
        finally:
            writer.release()
        import shutil
        shutil.move(tmp_video, output_path)
