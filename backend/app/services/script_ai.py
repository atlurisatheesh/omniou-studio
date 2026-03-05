"""
CLONEAI ULTRA — Script AI Service (Ollama)
=============================================
AI script generation using local Ollama LLM.
Falls back to template-based generation when Ollama is unavailable.
"""

import asyncio
import re
from typing import Optional

import structlog

from ..config import settings

logger = structlog.get_logger()


class ScriptAIService:
    """
    Script generation service using Ollama (local LLM).
    
    Generates professional video scripts with proper pacing
    and natural speech patterns.
    """

    # Average speaking rate: ~150 words per minute (2.5 words/sec)
    WORDS_PER_SECOND = 2.5

    async def generate(
        self,
        topic: str,
        tone: str = "professional",
        duration_seconds: int = 60,
        language: str = "en",
    ) -> dict:
        """
        Generate a video script.

        Args:
            topic: What the video should be about
            tone: professional | casual | educational | motivational | funny
            duration_seconds: Target video length
            language: ISO code

        Returns:
            { "script": str, "word_count": int, "estimated_duration": float }
        """
        target_words = int(duration_seconds * self.WORDS_PER_SECOND)

        try:
            script = await self._generate_ollama(topic, tone, target_words, language)
        except Exception as e:
            logger.warning("script_ai.ollama_fallback", error=str(e))
            script = self._generate_template(topic, tone, target_words)

        word_count = len(script.split())
        estimated_duration = round(word_count / self.WORDS_PER_SECOND, 1)

        logger.info(
            "script_ai.generated",
            words=word_count,
            duration=estimated_duration,
            tone=tone,
            method="ollama" if "ollama" not in str(type(script)) else "template",
        )

        return {
            "script": script,
            "word_count": word_count,
            "estimated_duration": estimated_duration,
        }

    async def _generate_ollama(self, topic: str, tone: str, target_words: int, language: str) -> str:
        """Generate script via Ollama API."""
        import httpx

        lang_name = {
            "en": "English", "es": "Spanish", "fr": "French", "de": "German",
            "it": "Italian", "pt": "Portuguese", "hi": "Hindi", "ar": "Arabic",
            "zh": "Chinese", "ja": "Japanese", "ko": "Korean", "ru": "Russian",
        }.get(language, "English")

        prompt = f"""Write a video script for a talking-head video. The speaker talks directly to camera.

Topic: {topic}
Tone: {tone}
Target length: approximately {target_words} words
Language: {lang_name}

Rules:
- Write ONLY the spoken words (no stage directions, no [brackets], no parentheses)
- Use natural, conversational phrasing
- Include brief pauses marked with "..." for natural pacing
- Start with a hook that grabs attention
- End with a clear call-to-action or conclusion
- Do NOT include any formatting, headers, or labels

Script:"""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": target_words * 2,  # tokens ≈ 1.3x words
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            script = data.get("response", "").strip()

            # Clean up any residual formatting
            script = re.sub(r"\[.*?\]", "", script)
            script = re.sub(r"\(.*?\)", "", script)
            script = re.sub(r"\*.*?\*", "", script)
            script = re.sub(r"#{1,6}\s*", "", script)
            script = re.sub(r"\n{3,}", "\n\n", script)
            script = script.strip()

            if len(script.split()) < 10:
                raise ValueError("Ollama returned too short a script")

            return script

    def _generate_template(self, topic: str, tone: str, target_words: int) -> str:
        """Fallback: template-based script generation."""
        templates = {
            "professional": [
                f"Hello everyone. Today I want to talk about {topic}.",
                f"This is something that's become increasingly important in our industry.",
                f"Let me share some key insights about {topic} that I think you'll find valuable.",
                f"First, it's important to understand the fundamentals.",
                f"When we look at {topic} from a strategic perspective, there are three main areas to consider.",
                f"The first area is understanding the current landscape and how it affects us.",
                f"Second, we need to think about practical implementation strategies.",
                f"And third, we should consider the long-term implications.",
                f"I've seen many professionals struggle with {topic}, but it doesn't have to be that complicated.",
                f"The key is to start with a clear framework and build from there.",
                f"Let me give you a concrete example of how this works in practice.",
                f"By applying these principles consistently, you'll see significant improvements.",
                f"If you found this helpful, make sure to follow for more insights on {topic}.",
                f"Thanks for watching, and I'll see you in the next video.",
            ],
            "casual": [
                f"Hey, what's up! So let me tell you about {topic}.",
                f"I've been really into this lately and honestly, it's been a game changer.",
                f"So here's the thing about {topic} that most people don't realize...",
                f"It's actually way simpler than you might think.",
                f"I started looking into this a few weeks ago and wow, just wow.",
                f"The cool part is anyone can get started with this.",
                f"You don't need any special skills or expensive tools.",
                f"Just take it one step at a time, and you'll be amazed at the results.",
                f"Trust me, once you try {topic}, you won't look back.",
                f"Drop a comment if you have any questions, I'm happy to help!",
                f"Alright, that's all for now. Catch you in the next one!",
            ],
            "educational": [
                f"Welcome to today's lesson on {topic}.",
                f"By the end of this video, you'll have a solid understanding of the core concepts.",
                f"Let's start with the basics. What exactly is {topic}?",
                f"In simple terms, it's a method for achieving better results in your work.",
                f"The history behind this is actually quite fascinating.",
                f"Now, let's break down the key components one by one.",
                f"The first component is foundational — everything else builds on this.",
                f"Pay close attention to this next part, because it's where most people get confused.",
                f"Here's a practical exercise you can try right now.",
                f"Think about how this applies to your own situation.",
                f"To summarize what we've learned today about {topic}...",
                f"Remember, practice makes perfect. Keep working at it!",
                f"In our next lesson, we'll dive even deeper into advanced techniques.",
            ],
        }

        sentences = templates.get(tone, templates["professional"])

        # Repeat/trim to approximate target word count
        script = " ".join(sentences)
        words = script.split()

        if len(words) < target_words:
            # Repeat sentences until we reach target
            while len(words) < target_words:
                for s in sentences:
                    words.extend(s.split())
                    if len(words) >= target_words:
                        break

        words = words[:target_words]
        return " ".join(words)
