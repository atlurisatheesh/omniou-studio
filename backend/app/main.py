"""
AgriSense — Agricultural Intelligence Platform
Main FastAPI Application
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import settings
from .models.database import init_db
from .routers import auth, disease, soil, weather, crops, market, community


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    Path("uploads").mkdir(exist_ok=True)
    Path("uploads/scans").mkdir(exist_ok=True)
    Path("uploads/community").mkdir(exist_ok=True)
    yield


app = FastAPI(
    title="AgriSense API",
    description="Agricultural Intelligence Platform — Disease Detection, Soil Analysis, Weather Forecasting, Crop Calendar, Market Prices & Community",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
uploads_path = Path("uploads")
uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

# Register routers
app.include_router(auth.router)
app.include_router(disease.router)
app.include_router(soil.router)
app.include_router(weather.router)
app.include_router(crops.router)
app.include_router(market.router)
app.include_router(community.router)


@app.get("/")
async def root():
    return {
        "name": "AgriSense API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "auth": "/auth",
            "disease": "/disease",
            "soil": "/soil",
            "weather": "/weather",
            "calendar": "/calendar",
            "market": "/market",
            "community": "/community",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
