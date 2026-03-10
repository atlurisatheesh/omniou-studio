"""
services/multi_face_pipeline.py — Multi-person / group video generation (Phase 12).

Supports generating a video with N people speaking sequentially or simultaneously.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

import cv2
import numpy as np
import structlog

log = structlog.get_logger(__name__)

MAX_PERSONS = 6


@dataclass
class PersonSpec:
    face_path: str
    voice_path: str
    script: str
    name: str = ""
    language: str = "en"
    emotion: str = "neutral"


@dataclass
class PersonResult:
    index: int
    spec: PersonSpec
    audio_path: Optional[str] = None
    video_path: Optional[str] = None
    error: Optional[str] = None
    duration_sec: float = 0.0


@dataclass
class MultiPersonResult:
    persons: List[PersonResult] = field(default_factory=list)
    final_video_path: Optional[str] = None
    total_duration_sec: float = 0.0
    error: Optional[str] = None


class MultiFacePipeline:
    """
    Orchestrates multi-person video generation.

    Layout modes:
    - "grid":       All faces in a grid (up to 4)
    - "sequential": Each person speaks in turn
    - "spotlight":  Active speaker large, others as thumbnails
    """

    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = Path(temp_dir or tempfile.mkdtemp())
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def generate(
        self,
        persons: List[PersonSpec],
        output_path: str,
        layout: str = "sequential",
        background_path: Optional[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> MultiPersonResult:
        if len(persons) > MAX_PERSONS:
            raise ValueError(f"Maximum {MAX_PERSONS} persons supported, got {len(persons)}")
        if not persons:
            raise ValueError("At least one person required")

        log.info("multi_face_start", persons=len(persons), layout=layout)
        result = MultiPersonResult()
        start = time.time()

        # Stage 1: Voice cloning (parallel)
        if progress_callback:
            progress_callback(5, f"Cloning {len(persons)} voices…")

        voice_tasks = [self._clone_voice(i, p, progress_callback) for i, p in enumerate(persons)]
        person_results: List[PersonResult] = list(await asyncio.gather(*voice_tasks))

        # Stage 2: Face animation (parallel, semaphore-limited)
        if progress_callback:
            progress_callback(30, "Animating faces…")

        sem = asyncio.Semaphore(2)
        anim_tasks = [self._animate_face_with_sem(sem, pr, progress_callback) for pr in person_results]
        person_results = list(await asyncio.gather(*anim_tasks))

        # Stage 3: Composite
        if progress_callback:
            progress_callback(75, f"Compositing {layout} layout…")

        try:
            composite_path = await self._composite(person_results, layout, background_path, progress_callback)
            result.final_video_path = composite_path
        except Exception as e:
            log.error("composite_failed", error=str(e))
            result.error = str(e)
            for pr in person_results:
                if pr.video_path:
                    result.final_video_path = pr.video_path
                    break

        result.persons = person_results
        result.total_duration_sec = time.time() - start
        if progress_callback:
            progress_callback(100, "Complete")
        return result

    async def _clone_voice(self, index: int, spec: PersonSpec, cb) -> PersonResult:
        pr = PersonResult(index=index, spec=spec)
        try:
            from app.services.voice_clone import VoiceCloneService
            svc = VoiceCloneService()
            out_path = str(self.temp_dir / f"voice_{index}_{uuid.uuid4().hex[:8]}.wav")
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: svc.clone_voice(
                    voice_sample_path=spec.voice_path, text=spec.script,
                    output_path=out_path, language=spec.language,
                )
            )
            pr.audio_path = out_path
        except Exception as e:
            log.error("voice_clone_failed", index=index, error=str(e))
            pr.error = f"Voice clone failed: {e}"
        return pr

    async def _animate_face_with_sem(self, sem, pr, cb) -> PersonResult:
        async with sem:
            return await self._animate_face(pr, cb)

    async def _animate_face(self, pr: PersonResult, cb) -> PersonResult:
        if pr.error or not pr.audio_path:
            return pr
        try:
            from app.services.face_animate import FaceAnimateService
            svc = FaceAnimateService()
            out_path = str(self.temp_dir / f"face_{pr.index}_{uuid.uuid4().hex[:8]}.mp4")
            duration = self._get_audio_duration(pr.audio_path)
            pr.duration_sec = duration
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: svc.animate(
                    face_image_path=pr.spec.face_path, audio_path=pr.audio_path,
                    output_path=out_path, duration_sec=duration, emotion=pr.spec.emotion,
                )
            )
            pr.video_path = out_path
        except Exception as e:
            log.error("face_animate_failed", index=pr.index, error=str(e))
            pr.error = f"Face animation failed: {e}"
        return pr

    def _get_audio_duration(self, audio_path: str) -> float:
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=None)
            return len(y) / sr
        except Exception:
            return 10.0

    async def _composite(self, persons, layout, background_path, cb) -> str:
        valid = [p for p in persons if p.video_path and not p.error]
        if not valid:
            raise RuntimeError("No valid person videos to composite")
        if layout == "sequential":
            return await asyncio.get_event_loop().run_in_executor(None, lambda: self._composite_sequential(valid))
        elif layout == "grid":
            return await asyncio.get_event_loop().run_in_executor(None, lambda: self._composite_grid(valid, background_path))
        elif layout == "spotlight":
            return await asyncio.get_event_loop().run_in_executor(None, lambda: self._composite_grid(valid, background_path))
        else:
            raise ValueError(f"Unknown layout: {layout}")

    def _composite_sequential(self, persons: List[PersonResult]) -> str:
        import subprocess, shutil
        out_path = str(self.temp_dir / f"multi_sequential_{uuid.uuid4().hex[:8]}.mp4")
        if len(persons) == 1:
            shutil.copy(persons[0].video_path, out_path)
            return out_path
        list_file = str(self.temp_dir / "concat_list.txt")
        with open(list_file, "w") as f:
            for p in persons:
                f.write(f"file '{p.video_path}'\n")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
            "-c:v", "libx264", "-crf", "20", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k", out_path,
        ], check=True, capture_output=True)
        return out_path

    def _composite_grid(self, persons: List[PersonResult], background_path: Optional[str]) -> str:
        out_path = str(self.temp_dir / f"multi_grid_{uuid.uuid4().hex[:8]}.mp4")
        n = len(persons)
        cols = min(n, 2) if n <= 4 else 3
        rows = (n + cols - 1) // cols
        cell_w, cell_h = 640, 480
        canvas_w, canvas_h = cols * cell_w, rows * cell_h

        caps = [cv2.VideoCapture(p.video_path) for p in persons]
        fps = caps[0].get(cv2.CAP_PROP_FPS) or 30.0
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        tmp_video = out_path.replace(".mp4", "_noaudio.mp4")
        writer = cv2.VideoWriter(tmp_video, fourcc, fps, (canvas_w, canvas_h))

        if background_path and os.path.exists(background_path):
            bg = cv2.resize(cv2.imread(background_path), (canvas_w, canvas_h))
        else:
            bg = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
            bg[:] = (30, 30, 30)

        try:
            while True:
                canvas = bg.copy()
                any_frame = False
                for i, cap in enumerate(caps):
                    ret, frame = cap.read()
                    if not ret:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap.read()
                    if ret:
                        any_frame = True
                        frame = cv2.resize(frame, (cell_w, cell_h))
                        r, c = divmod(i, cols)
                        y1, x1 = r * cell_h, c * cell_w
                        canvas[y1:y1 + cell_h, x1:x1 + cell_w] = frame
                        name = persons[i].spec.name or f"Person {i+1}"
                        cv2.putText(canvas, name, (x1 + 10, y1 + cell_h - 15),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                if not any_frame:
                    break
                writer.write(canvas)
        finally:
            writer.release()
            for cap in caps:
                cap.release()

        self._mux_audio(tmp_video, persons[0].audio_path, out_path)
        return out_path

    def _mux_audio(self, video_path: str, audio_path: str, out_path: str):
        import subprocess
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-i", audio_path,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out_path,
        ], check=True, capture_output=True)
