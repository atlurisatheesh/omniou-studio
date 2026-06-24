"""
CLONEAI ULTRA — Clone Agent (Self-Cloning Agent)
==================================================
Your digital twin — a persistent persona that generates videos
that look, sound, and speak exactly like you.

The Clone Agent combines:
  - Persistent identity anchor (face + appearance + skin color)
  - Locked voice embedding (identical voice across all outputs)
  - Speaking style profile (pace, vocabulary, sentence patterns)
  - Optional RAG knowledge base (for Q&A video generation)

Usage:
    agent = CloneAgent()
    
    # Create your digital twin
    persona_id = await agent.create_persona(
        user_id="...",
        photos=["photo1.jpg", "photo2.jpg"],
        voice_samples=["voice.wav"],
    )
    
    # Generate a video as your clone
    video_path = await agent.generate_video(
        persona_id=persona_id,
        script="Hello, this is my clone speaking...",
        duration_minutes=2,
    )
    
    # Answer questions as your clone
    video_path = await agent.answer_question(
        persona_id=persona_id,
        question="What is your approach to AI?",
    )
"""

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import structlog

from ..config import settings
from .identity_anchor import IdentityAnchor, IdentityAnchorService

logger = structlog.get_logger()

PERSONA_DIR = Path("outputs") / "personas"
PERSONA_DIR.mkdir(parents=True, exist_ok=True)


class CloneAgent:
    """
    Self-cloning agent that creates and manages persistent digital twins.
    
    A persona is created ONCE from photos + voice samples, then reused
    for unlimited video generations — all looking/sounding like YOU.
    """
    
    def __init__(self, model_cache_dir: str = "./models"):
        self.model_cache_dir = model_cache_dir
        self.anchor_service = IdentityAnchorService(model_cache_dir=model_cache_dir)
    
    # ── Create Persona ──
    
    async def create_persona(
        self,
        user_id: str,
        photos: List[str],
        voice_samples: List[str] = None,
        name: str = "My Clone",
    ) -> dict:
        """
        Create a persistent persona from photos and voice samples.
        
        If multiple photos are provided, embeddings are averaged for
        a more robust identity representation.
        
        Returns:
            Dict with persona_id, anchor_id, and quality metrics
        """
        start_time = time.time()
        persona_id = uuid.uuid4().hex[:16]
        persona_dir = PERSONA_DIR / persona_id
        persona_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            "clone_agent.creating_persona",
            user_id=user_id,
            photo_count=len(photos),
            voice_count=len(voice_samples) if voice_samples else 0,
        )
        
        # Create primary anchor from best photo
        primary_photo = photos[0]
        primary_voice = voice_samples[0] if voice_samples else None
        
        anchor = await self.anchor_service.create_anchor(
            photo_path=primary_photo,
            voice_path=primary_voice,
        )
        
        # If multiple photos, average the embeddings for robustness
        if len(photos) > 1 and anchor.face_embedding is not None:
            embeddings = [anchor.face_embedding]
            
            for photo_path in photos[1:]:
                try:
                    extra_anchor = await self.anchor_service.create_anchor(
                        photo_path=photo_path,
                    )
                    if extra_anchor.face_embedding is not None:
                        embeddings.append(extra_anchor.face_embedding)
                except Exception as e:
                    logger.warning(
                        "clone_agent.extra_photo_failed",
                        photo=photo_path,
                        error=str(e),
                    )
            
            if len(embeddings) > 1:
                # Average embeddings and re-normalize
                avg_embedding = np.mean(embeddings, axis=0)
                norm = np.linalg.norm(avg_embedding)
                if norm > 0:
                    anchor.face_embedding = avg_embedding / norm
                
                logger.info(
                    "clone_agent.embeddings_averaged",
                    count=len(embeddings),
                )
        
        # Analyze speaking style (if voice samples provided)
        style_profile = {}
        if voice_samples:
            style_profile = await self._analyze_speaking_style(voice_samples)
        
        # Save everything
        anchor_path = await self.anchor_service.save_anchor(anchor, f"persona_{persona_id}")
        
        # Save style profile
        style_path = persona_dir / "style_profile.json"
        with open(str(style_path), "w") as f:
            json.dump(style_profile, f, indent=2)
        
        # Save persona metadata
        metadata = {
            "persona_id": persona_id,
            "user_id": user_id,
            "name": name,
            "anchor_id": anchor.anchor_id,
            "anchor_path": anchor_path,
            "photos": photos,
            "voice_samples": voice_samples or [],
            "style_profile": style_profile,
            "created_at": time.time(),
        }
        
        meta_path = persona_dir / "metadata.json"
        with open(str(meta_path), "w") as f:
            json.dump(metadata, f, indent=2, default=str)
        
        elapsed = time.time() - start_time
        logger.info(
            "clone_agent.persona_created",
            persona_id=persona_id,
            anchor_id=anchor.anchor_id,
            time_seconds=round(elapsed, 2),
        )
        
        return {
            "persona_id": persona_id,
            "anchor_id": anchor.anchor_id,
            "anchor_path": anchor_path,
            "name": name,
            "has_voice": anchor.has_voice(),
            "style_profile": style_profile,
            "processing_time": round(elapsed, 2),
        }
    
    # ── Generate Video ──
    
    async def generate_video(
        self,
        persona_id: str,
        script: Optional[str] = None,
        prompt: Optional[str] = None,
        duration_minutes: float = 1.0,
        emotion: str = "neutral",
        background: str = "original",
    ) -> dict:
        """
        Generate a video using a saved persona.
        
        The persona's identity anchor ensures every frame looks/sounds like them.
        
        Args:
            persona_id: ID of saved persona
            script: Full script text (if provided, used directly)
            prompt: Topic/prompt (if no script, generates one via LLM)
            duration_minutes: Target video duration
            emotion: Default emotion for scenes
            background: Default background
        
        Returns:
            Dict with video_path, identity_score, and metadata
        """
        # Load persona
        persona_dir = PERSONA_DIR / persona_id
        meta_path = persona_dir / "metadata.json"
        
        if not meta_path.exists():
            raise ValueError(f"Persona not found: {persona_id}")
        
        with open(str(meta_path)) as f:
            metadata = json.load(f)
        
        # Load identity anchor
        anchor = await self.anchor_service.load_anchor(
            f"persona_{persona_id}",
            metadata["anchor_id"],
        )
        
        # Generate script from prompt if needed
        if not script and prompt:
            script = await self._generate_script_from_prompt(
                prompt=prompt,
                duration_minutes=duration_minutes,
                style_profile=metadata.get("style_profile", {}),
            )
        
        if not script:
            raise ValueError("Either script or prompt must be provided")
        
        # Use DirectorAgent for multi-scene generation
        from .director_agent import DirectorAgent
        
        director = DirectorAgent(
            identity_anchor=anchor,
            device=settings.DEVICE,
            model_cache_dir=self.model_cache_dir,
        )
        
        scenes = await director.analyze_script(
            script_text=script,
            target_duration_minutes=duration_minutes,
            default_emotion=emotion,
            default_background=background,
        )
        
        project_id = f"persona_{persona_id}_{uuid.uuid4().hex[:8]}"
        result = await director.generate_project(project_id, scenes)
        
        return {
            "persona_id": persona_id,
            "project_id": project_id,
            "video_path": result.final_video_path,
            "status": result.status,
            "identity_score": result.overall_identity_score,
            "color_score": result.overall_color_score,
            "scenes_completed": result.completed_scenes,
            "scenes_failed": result.failed_scenes,
            "processing_time": result.processing_time_seconds,
        }
    
    # ── Answer Question ──
    
    async def answer_question(
        self,
        persona_id: str,
        question: str,
        knowledge_base_path: Optional[str] = None,
    ) -> dict:
        """
        Generate a video of the persona answering a question.
        
        If a knowledge base is provided, uses RAG to find relevant context
        before generating the answer in the persona's speaking style.
        """
        # Load persona
        persona_dir = PERSONA_DIR / persona_id
        meta_path = persona_dir / "metadata.json"
        
        if not meta_path.exists():
            raise ValueError(f"Persona not found: {persona_id}")
        
        with open(str(meta_path)) as f:
            metadata = json.load(f)
        
        style_profile = metadata.get("style_profile", {})
        
        # Build context from knowledge base (RAG)
        context = ""
        if knowledge_base_path:
            context = await self._search_knowledge_base(
                knowledge_base_path, question
            )
        
        # Generate answer script using LLM
        answer_script = await self._generate_answer_script(
            question=question,
            context=context,
            style_profile=style_profile,
            persona_name=metadata.get("name", "the speaker"),
        )
        
        # Generate video with the answer
        return await self.generate_video(
            persona_id=persona_id,
            script=answer_script,
            duration_minutes=1.0,  # Short answer format
            emotion="professional",
        )
    
    # ── Batch Generate ──
    
    async def batch_generate(
        self,
        persona_id: str,
        content_list: List[dict],
    ) -> List[dict]:
        """
        Generate multiple videos using the same persona.
        
        All videos will have identical identity — same face, same voice.
        
        Args:
            persona_id: Saved persona ID
            content_list: List of dicts with keys: script/prompt, duration_minutes, emotion
        
        Returns:
            List of generation results
        """
        results = []
        
        for i, content in enumerate(content_list):
            logger.info(
                "clone_agent.batch_generating",
                persona_id=persona_id,
                index=i,
                total=len(content_list),
            )
            
            try:
                result = await self.generate_video(
                    persona_id=persona_id,
                    script=content.get("script"),
                    prompt=content.get("prompt"),
                    duration_minutes=content.get("duration_minutes", 1.0),
                    emotion=content.get("emotion", "neutral"),
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "persona_id": persona_id,
                    "index": i,
                    "status": "failed",
                    "error": str(e),
                })
        
        return results
    
    # ── Private: Speaking Style Analysis ──
    
    async def _analyze_speaking_style(
        self,
        voice_samples: List[str],
    ) -> dict:
        """Analyze speaking patterns from voice samples."""
        style = {
            "typical_pace": "moderate",  # words per minute estimate
            "pause_frequency": "normal",
            "sentence_length": "medium",
            "tone": "professional",
        }
        
        try:
            # Attempt audio analysis for pace estimation
            for sample_path in voice_samples:
                if not Path(sample_path).exists():
                    continue
                
                try:
                    import torchaudio
                    waveform, sr = torchaudio.load(sample_path)
                    duration = waveform.shape[1] / sr
                    
                    if duration > 0:
                        # Rough estimation based on audio duration
                        if duration < 10:
                            style["typical_pace"] = "fast"
                        elif duration > 30:
                            style["typical_pace"] = "slow"
                        else:
                            style["typical_pace"] = "moderate"
                    
                    break  # Use first valid sample
                except ImportError:
                    pass
        except Exception as e:
            logger.debug("clone_agent.style_analysis_failed", error=str(e))
        
        return style
    
    # ── Private: Script Generation ──
    
    async def _generate_script_from_prompt(
        self,
        prompt: str,
        duration_minutes: float,
        style_profile: dict,
    ) -> str:
        """Generate a script from a prompt using LLM, matching the persona's style."""
        try:
            import httpx
            
            pace = style_profile.get("typical_pace", "moderate")
            word_count = int(duration_minutes * 150)  # ~150 words per minute
            
            system_prompt = f"""Write a {duration_minutes}-minute video script (approximately {word_count} words).
Speaking pace: {pace}.
Style: Natural, conversational, as if speaking directly to camera.
Do not include stage directions, camera cues, or formatting.
Just write the words the speaker should say."""

            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={
                        "model": settings.DIRECTOR_LLM_MODEL,
                        "prompt": f"{system_prompt}\n\nTopic: {prompt}",
                        "stream": False,
                    },
                )
                
                if response.status_code == 200:
                    return response.json().get("response", "")
        
        except Exception as e:
            logger.warning("clone_agent.script_generation_failed", error=str(e))
        
        return f"Hello, today I want to talk about {prompt}."
    
    async def _generate_answer_script(
        self,
        question: str,
        context: str,
        style_profile: dict,
        persona_name: str,
    ) -> str:
        """Generate an answer script using LLM with RAG context."""
        try:
            import httpx
            
            prompt_parts = [
                f"You are {persona_name}. Answer the following question naturally, as if speaking to camera.",
                f"Question: {question}",
            ]
            
            if context:
                prompt_parts.insert(1, f"Use this context to inform your answer:\n{context}")
            
            prompt_parts.append(
                "Give a clear, concise answer in 30-60 seconds of speech (~75-150 words)."
            )
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={
                        "model": settings.DIRECTOR_LLM_MODEL,
                        "prompt": "\n\n".join(prompt_parts),
                        "stream": False,
                    },
                )
                
                if response.status_code == 200:
                    return response.json().get("response", "")
        
        except Exception as e:
            logger.warning("clone_agent.answer_gen_failed", error=str(e))
        
        return f"That's a great question about {question}. Let me share my thoughts."
    
    async def _search_knowledge_base(
        self,
        knowledge_base_path: str,
        query: str,
    ) -> str:
        """Search a knowledge base for relevant context (simple text search)."""
        try:
            kb_path = Path(knowledge_base_path)
            
            if kb_path.is_file():
                with open(str(kb_path)) as f:
                    content = f.read()
                
                # Simple keyword search (upgrade to vector search later)
                query_words = set(query.lower().split())
                paragraphs = content.split("\n\n")
                
                scored = []
                for para in paragraphs:
                    para_words = set(para.lower().split())
                    overlap = len(query_words & para_words)
                    if overlap > 0:
                        scored.append((overlap, para))
                
                scored.sort(reverse=True)
                
                # Return top 3 relevant paragraphs
                return "\n\n".join(para for _, para in scored[:3])
            
            elif kb_path.is_dir():
                # Search all .txt files in directory
                all_text = []
                for txt_file in kb_path.glob("*.txt"):
                    with open(str(txt_file)) as f:
                        all_text.append(f.read())
                
                combined = "\n\n".join(all_text)
                return combined[:2000]  # Limit context size
        
        except Exception as e:
            logger.warning("clone_agent.kb_search_failed", error=str(e))
        
        return ""
