"""
CLONEAI ULTRA — Voice Clone Service
=====================================
Multi-engine voice cloning: Chatterbox (primary) + XTTS v2 (fallback).
Includes RVC v2 second-pass watermark removal and emotion-to-exaggeration mapping.

Engine selection:
  - "chatterbox"  → Resemble AI Chatterbox (zero-shot, 6s sample)
  - "xtts"        → Coqui XTTS v2 (multi-language, 30s+ sample)
  - "auto"        → Try Chatterbox first, fall back to XTTS v2

Pipeline:
  1. Audio preprocessing (resample, normalize, denoise)
  2. Engine-specific inference (with emotion → exaggeration mapping)
  3. RVC v2 watermark removal pass (removes Chatterbox Perth watermark)
  4. Post-processing (normalize loudness, trim silence, fade)
"""

import asyncio
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Optional

import numpy as np
import structlog
import torch
import torchaudio

from ..config import settings

logger = structlog.get_logger()

OUTPUT_DIR = Path("outputs")
TEMP_DIR = Path("temp")

# ── Emotion → Chatterbox Exaggeration Mapping ──
# Controls vocal expressiveness: 0.0 = monotone, 1.0 = maximum expression
EMOTION_TO_EXAGGERATION = {
    "neutral":  0.5,   # Natural, balanced delivery
    "happy":    0.75,  # Warm, positive, upbeat
    "excited":  0.9,   # High energy, enthusiastic
    "sad":      0.4,   # Subdued, slower, softer
    "angry":    0.85,  # Strong, forceful, intense
    "loving":   0.65,  # Warm, intimate, gentle
}

# ── Emotion → XTTS Speed/Style Hints ──
# XTTS doesn't have exaggeration, so we adjust generation parameters
EMOTION_TO_XTTS_PARAMS = {
    "neutral":  {"speed": 1.0},
    "happy":    {"speed": 1.05},
    "excited":  {"speed": 1.1},
    "sad":      {"speed": 0.9},
    "angry":    {"speed": 1.05},
    "loving":   {"speed": 0.95},
}


class VoiceCloneService:
    """
    Multi-engine voice cloning service with watermark removal.

    Supports Chatterbox (zero-shot, English primary) and XTTS v2
    (multilingual, 17 languages). Engine selected via config.VOICE_ENGINE.

    Chatterbox outputs are run through an RVC v2 second pass to remove
    the built-in Perth neural watermark that would otherwise make output
    detectable as AI-generated.
    """

    SUPPORTED_LANGUAGES = [
        "en", "es", "fr", "de", "it", "pt", "pl", "tr",
        "ru", "nl", "cs", "ar", "zh", "ja", "hu", "ko", "hi",
    ]

    def __init__(self, device: str = "cuda", model_cache_dir: str = "./models"):
        self.device = device if torch.cuda.is_available() else "cpu"
        self.model_cache_dir = model_cache_dir
        self.model_dir = Path(model_cache_dir)
        self.engine = settings.VOICE_ENGINE  # "chatterbox" | "xtts" | "auto"
        self._chatterbox_model = None
        self._xtts_model = None
        self.sample_rate = 24000  # Chatterbox default

    async def clone_voice(
        self,
        voice_sample_path: str,
        text: str,
        language: str = "en",
        emotion: str = "neutral",
        output_dir: Optional[str] = None,
    ) -> Path:
        """
        Clone a voice and generate speech from text.

        Args:
            voice_sample_path: Path to reference voice audio (min 6s for Chatterbox, 30s for XTTS)
            text: Text to speak in the cloned voice
            language: ISO language code
            emotion: Emotion tag (neutral, happy, sad, angry, excited, loving)
            output_dir: Optional custom output directory

        Returns:
            Path to generated audio file (WAV)
        """
        start_time = time.time()
        logger.info(
            "voice_clone.start",
            engine=self.engine,
            language=language,
            emotion=emotion,
            text_length=len(text),
            sample=voice_sample_path,
        )

        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")

        # Step 1: Preprocess reference audio
        processed_audio_path = await self._preprocess_audio(voice_sample_path)

        # Step 2: Route to engine (with emotion)
        used_chatterbox = False
        if self.engine == "chatterbox" or (self.engine == "auto" and language == "en"):
            try:
                output_path = await self._generate_chatterbox(
                    processed_audio_path, text, emotion, output_dir
                )
                used_chatterbox = True
            except Exception as e:
                logger.warning("voice_clone.chatterbox_failed", error=str(e), msg="Falling back to XTTS")
                output_path = await self._generate_xtts(
                    processed_audio_path, text, language, emotion, output_dir
                )
        elif self.engine == "xtts":
            output_path = await self._generate_xtts(
                processed_audio_path, text, language, emotion, output_dir
            )
        else:  # auto + non-English
            output_path = await self._generate_xtts(
                processed_audio_path, text, language, emotion, output_dir
            )

        # Step 3: RVC v2 watermark removal (only for Chatterbox output)
        if used_chatterbox:
            clean_path = output_path.parent / f"clean_{output_path.name}"
            output_path = Path(await self._remove_watermark_rvc(
                str(output_path), str(clean_path)
            ))

        # Step 4: Post-process (normalize, trim, fade)
        final_path = await self._postprocess_audio(output_path)

        elapsed = time.time() - start_time
        logger.info(
            "voice_clone.complete",
            output=str(final_path),
            engine=self.engine,
            emotion=emotion,
            watermark_removed=used_chatterbox,
            time_seconds=round(elapsed, 2),
        )

        return final_path

    # ── Chatterbox Engine ──

    async def _load_chatterbox(self):
        """Load Chatterbox model (install from source, not pip)."""
        if self._chatterbox_model is not None:
            return self._chatterbox_model

        def _load():
            logger.info("voice_clone.loading_model", model="chatterbox")
            try:
                from chatterbox.tts import ChatterboxTTS

                model = ChatterboxTTS.from_pretrained(device=self.device)
                logger.info("voice_clone.model_loaded", model="chatterbox", device=self.device)
                return model
            except ImportError:
                logger.error("voice_clone.chatterbox_not_installed")
                raise RuntimeError(
                    "Chatterbox not installed. Install from source:\n"
                    "  git clone https://github.com/resemble-ai/chatterbox.git /tmp/chatterbox\n"
                    "  cd /tmp/chatterbox && pip install -e .\n"
                    "DO NOT use 'pip install chatterbox-tts' — it has dependency conflicts."
                )
            except Exception as e:
                logger.error("voice_clone.chatterbox_load_failed", error=str(e))
                raise

        self._chatterbox_model = await asyncio.to_thread(_load)
        return self._chatterbox_model

    async def _generate_chatterbox(
        self,
        reference_audio: str,
        text: str,
        emotion: str = "neutral",
        output_dir: Optional[str] = None,
    ) -> Path:
        """
        Generate speech using Chatterbox (zero-shot, English).
        Maps emotion to exaggeration parameter for expressive output.
        """
        model = await self._load_chatterbox()

        out_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / f"voice_cb_{uuid.uuid4().hex[:12]}.wav"

        exaggeration = EMOTION_TO_EXAGGERATION.get(emotion, 0.5)

        def _generate():
            wav = model.generate(
                text=text,
                audio_prompt_path=reference_audio,
                exaggeration=exaggeration,
                cfg_weight=0.5,
            )
            # Save output — Chatterbox returns a tensor at model.sr
            torchaudio.save(str(output_path), wav.cpu(), model.sr)
            return output_path

        result = await asyncio.to_thread(_generate)
        self.sample_rate = model.sr
        logger.info(
            "voice_clone.chatterbox_generated",
            output=str(result),
            emotion=emotion,
            exaggeration=exaggeration,
        )
        return result

    # ── XTTS v2 Engine ──

    async def _load_xtts(self):
        """Load XTTS v2 model."""
        if self._xtts_model is not None:
            return self._xtts_model

        def _load():
            logger.info("voice_clone.loading_model", model="xtts_v2")
            try:
                from TTS.api import TTS

                tts = TTS(
                    model_name=settings.XTTS_MODEL_NAME,
                    progress_bar=True,
                ).to(self.device)

                logger.info("voice_clone.model_loaded", model="xtts_v2", device=self.device)
                return tts
            except Exception as e:
                logger.error("voice_clone.xtts_load_failed", error=str(e))
                raise

        self._xtts_model = await asyncio.to_thread(_load)
        return self._xtts_model

    async def _generate_xtts(
        self,
        reference_audio: str,
        text: str,
        language: str,
        emotion: str = "neutral",
        output_dir: Optional[str] = None,
    ) -> Path:
        """Generate speech using XTTS v2 (multilingual) with emotion hints."""
        model = await self._load_xtts()

        out_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / f"voice_xtts_{uuid.uuid4().hex[:12]}.wav"

        xtts_params = EMOTION_TO_XTTS_PARAMS.get(emotion, {"speed": 1.0})

        def _generate():
            model.tts_to_file(
                text=text,
                speaker_wav=reference_audio,
                language=language,
                file_path=str(output_path),
                speed=xtts_params.get("speed", 1.0),
            )
            return output_path

        result = await asyncio.to_thread(_generate)
        self.sample_rate = 22050
        logger.info("voice_clone.xtts_generated", output=str(result), emotion=emotion)
        return result

    # ── RVC v2 Watermark Removal ──

    async def _remove_watermark_rvc(
        self,
        input_wav: str,
        output_wav: str,
        f0_method: str = "rmvpe",
    ) -> str:
        """
        Pass Chatterbox output through RVC v2 to remove Perth neural watermark.

        Chatterbox embeds an imperceptible neural watermark (Perth watermarker)
        into every audio output. This watermark survives MP3 compression, speed
        changes, pitch shifts, and even our 7-layer post-processing.

        RVC v2 reconstructs the audio waveform from scratch using its own vocoder,
        which completely removes any embedded watermarks while preserving voice
        characteristics.

        Args:
            input_wav: Path to Chatterbox-generated audio (watermarked)
            output_wav: Path for clean output audio
            f0_method: Pitch extraction method (rmvpe = most accurate)

        Returns:
            Path to clean audio file (or original if RVC unavailable)
        """
        rvc_dir = self.model_dir / "rvc"

        # Check if RVC is available
        if not rvc_dir.exists():
            logger.warning(
                "voice_clone.rvc_not_available",
                msg="RVC v2 not found. Chatterbox watermark will remain in output. "
                    "To enable watermark removal, install RVC v2 in models/rvc/",
            )
            return input_wav

        rvc_cli = rvc_dir / "infer_cli.py"
        rvc_model = rvc_dir / "voice_model.pth"

        if not rvc_cli.exists() or not rvc_model.exists():
            logger.warning(
                "voice_clone.rvc_incomplete",
                msg="RVC installation incomplete (missing infer_cli.py or voice_model.pth)",
            )
            return input_wav

        try:
            logger.info("voice_clone.rvc_pass_start", input=input_wav)

            cmd = [
                "python", str(rvc_cli),
                "--input", input_wav,
                "--output", output_wav,
                "--model", str(rvc_model),
                "--f0_method", f0_method,
                "--transpose", "0",         # No pitch shift — preserve original pitch
                "--index_rate", "0.0",      # No voice character change — only remove watermark
                "--protect", "0.33",        # Protect consonant clarity
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0 and Path(output_wav).exists() and Path(output_wav).stat().st_size > 0:
                logger.info("voice_clone.rvc_watermark_removed", output=output_wav)
                return output_wav
            else:
                stderr_text = stderr.decode(errors="replace")[:500]
                logger.warning(
                    "voice_clone.rvc_pass_failed",
                    returncode=proc.returncode,
                    stderr=stderr_text,
                    msg="Using original (watermarked) audio",
                )
                return input_wav

        except FileNotFoundError:
            logger.warning("voice_clone.rvc_python_not_found", msg="Python not found for RVC subprocess")
            return input_wav
        except Exception as e:
            logger.warning("voice_clone.rvc_error", error=str(e), msg="Using original audio")
            return input_wav

    # ── Audio Processing ──

    async def _preprocess_audio(self, audio_path: str) -> str:
        """Preprocess reference audio: resample, mono, normalize, trim silence."""
        logger.info("voice_clone.preprocess", input=audio_path)

        def _process():
            waveform, sr = torchaudio.load(audio_path)

            # Convert to mono
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)

            # Resample to 22050
            target_sr = 22050
            if sr != target_sr:
                resampler = torchaudio.transforms.Resample(sr, target_sr)
                waveform = resampler(waveform)

            # Normalize
            waveform = waveform / (waveform.abs().max() + 1e-7)

            # Trim silence (energy-based)
            energy = waveform.abs().mean(dim=0)
            threshold = energy.max() * 0.01
            mask = energy > threshold
            if mask.any():
                start = mask.nonzero(as_tuple=True)[0][0]
                end = mask.nonzero(as_tuple=True)[0][-1] + 1
                waveform = waveform[:, start:end]

            TEMP_DIR.mkdir(parents=True, exist_ok=True)
            out_path = TEMP_DIR / f"preprocessed_{uuid.uuid4().hex[:8]}.wav"
            torchaudio.save(str(out_path), waveform, target_sr)
            return str(out_path)

        return await asyncio.to_thread(_process)

    async def _postprocess_audio(self, audio_path: Path) -> Path:
        """Post-process: normalize loudness, trim trailing silence, fade out."""
        logger.info("voice_clone.postprocess", input=str(audio_path))

        def _process():
            waveform, sr = torchaudio.load(str(audio_path))

            # Normalize peak
            peak = waveform.abs().max()
            if peak > 0:
                waveform = waveform * (0.95 / peak)

            # Trim trailing silence
            energy = waveform.abs().mean(dim=0)
            threshold = energy.max() * 0.005
            mask = energy > threshold
            if mask.any():
                end = mask.nonzero(as_tuple=True)[0][-1] + 1
                waveform = waveform[:, :end]

            # Fade out (100ms)
            fade_samples = int(0.1 * sr)
            if waveform.shape[1] > fade_samples:
                fade = torch.linspace(1.0, 0.0, fade_samples)
                waveform[:, -fade_samples:] *= fade

            final_path = audio_path.parent / f"final_{audio_path.name}"
            torchaudio.save(str(final_path), waveform, sr)
            return final_path

        result = await asyncio.to_thread(_process)
        logger.info("voice_clone.postprocessed", output=str(result))
        return result

    async def get_speaker_embedding(self, audio_path: str) -> np.ndarray:
        """Extract speaker embedding for caching/reuse."""
        model = await self._load_xtts()

        def _extract():
            gpt_cond_latent, speaker_embedding = model.synthesizer.tts_model.get_conditioning_latents(
                audio_path=[audio_path]
            )
            return speaker_embedding.cpu().numpy()

        return await asyncio.to_thread(_extract)
