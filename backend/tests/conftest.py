"""
Shared test fixtures for CloneAI ULTRA backend tests.
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Force SQLite for tests
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_cloneai.db"
os.environ["APP_ENV"] = "test"

from app.main import app  # noqa: E402
from app.models.database import init_db  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def client():
    """Async HTTP client bound to the FastAPI app."""
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_data():
    """Common test data."""
    return {
        "clone_request": {
            "photo_path": "uploads/photos/test.jpg",
            "voice_path": "uploads/voices/test.wav",
            "script_text": "Hello, this is a test script for CloneAI.",
            "target_language": "en",
            "emotion": "neutral",
            "background": "original",
        },
        "user": {
            "name": "Test User",
            "email": "test@cloneai.pro",
        },
        "voice_profile": {
            "name": "Test Voice",
            "language": "en",
        },
        "script_request": {
            "topic": "artificial intelligence",
            "tone": "professional",
            "duration_seconds": 30,
            "language": "en",
        },
    }
