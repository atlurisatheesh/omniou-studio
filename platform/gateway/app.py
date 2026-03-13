"""Ominou Studio — API Gateway.

Routes all requests to the appropriate microservice.
Handles rate limiting, CORS, and request logging.
"""
import time
import httpx
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.config import settings

app = FastAPI(
    title="Ominou Studio Gateway",
    version=settings.APP_VERSION,
    description="Unified API Gateway for Ominou Studio",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "https://ominou.studio"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory rate limiter (use Redis in production)
rate_limit_store: dict[str, list[float]] = defaultdict(list)

SERVICE_MAP = {
    "auth": settings.AUTH_SERVICE_URL,
    "voice": settings.VOICE_SERVICE_URL,
    "design": settings.DESIGN_SERVICE_URL,
    "code": settings.CODE_SERVICE_URL,
    "video": settings.VIDEO_SERVICE_URL,
    "writer": settings.WRITER_SERVICE_URL,
    "music": settings.MUSIC_SERVICE_URL,
    "workflow": settings.WORKFLOW_SERVICE_URL,
    "billing": settings.BILLING_SERVICE_URL,
    "storage": settings.STORAGE_SERVICE_URL,
}


def check_rate_limit(client_ip: str) -> bool:
    now = time.time()
    window = 60
    rate_limit_store[client_ip] = [t for t in rate_limit_store[client_ip] if now - t < window]
    if len(rate_limit_store[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
        return False
    rate_limit_store[client_ip].append(now)
    return True


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "modules": list(SERVICE_MAP.keys()),
    }


@app.get("/health")
async def health():
    service_status = {}
    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, url in SERVICE_MAP.items():
            try:
                r = await client.get(f"{url}/health")
                service_status[name] = "up" if r.status_code == 200 else "degraded"
            except Exception:
                service_status[name] = "down"
    return {"gateway": "up", "services": service_status}


@app.api_route("/api/v1/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(service: str, path: str, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    base_url = SERVICE_MAP.get(service)
    if not base_url:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")

    target_url = f"{base_url}/api/{path}"
    headers = dict(request.headers)
    headers.pop("host", None)

    body = await request.body()

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=dict(request.query_params),
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type"),
            )
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail=f"Service '{service}' is unavailable")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail=f"Service '{service}' timed out")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
