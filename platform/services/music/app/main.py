"""Music Studio Service — AI Music, Jingles, Sound Effects."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from shared.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Ominou Studio — Music Studio", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

from .routers.music import router as music_router
app.include_router(music_router, prefix="/api", tags=["Music Studio"])


@app.get("/health")
async def health():
    return {"service": "music", "status": "up"}
