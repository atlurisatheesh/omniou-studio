"""AI Writer Service — Blog Posts, Ad Copy, Scripts, SEO Content."""
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


app = FastAPI(title="Ominou Studio — AI Writer", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

from .routers.writer import router as writer_router
app.include_router(writer_router, prefix="/api", tags=["AI Writer"])


@app.get("/health")
async def health():
    return {"service": "writer", "status": "up"}
