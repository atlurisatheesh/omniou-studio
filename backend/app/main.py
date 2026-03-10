"""
CLONEAI ULTRA — FastAPI Application Entry Point
=================================================
Main application with lifespan management, CORS, database init,
and route registration (Section 8).
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .models.database import init_db
from .routers import admin, clone, health, script, upload, user, video, voice
from .routers import auth as auth_router
from .routers import analytics as analytics_router
from .routers import templates as templates_router
from .routers import streaming as streaming_router
from .routers import multi_face as multi_face_router
from .services.model_manager import ModelManager
from .utils.ws_manager import ws_manager

load_dotenv()

logger = structlog.get_logger()

# ── Directories ──
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
TEMP_DIR = Path("temp")
MODEL_DIR = Path(settings.MODEL_CACHE_DIR)

for d in [UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR, MODEL_DIR]:
    d.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — init DB + load AI models at startup, cleanup at shutdown."""
    logger.info("cloneai.startup", msg="Initializing CloneAI Ultra backend...")

    # Initialize database tables (dev — use Alembic in production)
    await init_db()
    logger.info("cloneai.startup", msg="Database tables initialized")

    # Initialize model manager (lazy loading — models load on first use)
    app.state.model_manager = ModelManager(
        device=settings.DEVICE,
        model_cache_dir=str(MODEL_DIR),
    )
    logger.info("cloneai.startup", msg="Model manager initialized", device=settings.DEVICE)

    # Start WebSocket heartbeat manager
    ws_manager.start()
    logger.info("cloneai.startup", msg="WebSocket manager started")

    yield

    # Cleanup
    ws_manager.stop()
    logger.info("cloneai.shutdown", msg="Shutting down CloneAI Ultra backend...")
    if hasattr(app.state, "model_manager"):
        app.state.model_manager.unload_all()
    logger.info("cloneai.shutdown", msg="All models unloaded. Goodbye.")


# ── App ──
app = FastAPI(
    title="CloneAI Ultra API",
    description="AI-powered voice cloning + cinematic face animation API. Real AI pipeline with LivePortrait, MuseTalk, Chatterbox, GFPGAN.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──
origins = settings.CORS_ORIGINS.split(",") if hasattr(settings, "CORS_ORIGINS") and settings.CORS_ORIGINS else ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (uploads / outputs) ──
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# ── Routes ──
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
app.include_router(clone.router, prefix="/api/v1", tags=["Clone"])
app.include_router(voice.router, prefix="/api/v1", tags=["Voice"])
app.include_router(video.router, prefix="/api/v1", tags=["Video"])
app.include_router(script.router, prefix="/api/v1", tags=["Script"])
app.include_router(user.router, prefix="/api/v1", tags=["User"])
app.include_router(admin.router, prefix="/api/v1", tags=["Admin"])
app.include_router(auth_router.router, prefix="/api/v1", tags=["Auth"])
app.include_router(analytics_router.router, prefix="/api/v1", tags=["Analytics"])
app.include_router(templates_router.router, prefix="/api/v1", tags=["Templates"])
app.include_router(streaming_router.router, prefix="/api/v1", tags=["Streaming"])
app.include_router(multi_face_router.router, prefix="/api/v1", tags=["MultiFace"])


@app.get("/")
async def root():
    return {
        "app": "CloneAI Ultra",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "online",
    }
