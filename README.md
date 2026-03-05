# 🎬 CloneAI Pro

**Free, open-source AI avatar video generator** — a self-hosted alternative to HeyGen ($29/mo), ElevenLabs ($22/mo), and Synthesia ($30/mo).

Upload a photo + voice sample + script → get a talking avatar video with cloned voice, animated face, perfect lip sync, and enhanced quality. **No watermark. No monthly fees. Your GPU, your data.**

---

## ✨ Features

| Feature | Details |
|---|---|
| **Voice Cloning** | XTTS v2 — clone any voice from a 30-second sample, 17 languages |
| **Face Animation** | MuseTalk-style pipeline — audio-driven facial animation |
| **Lip Sync** | LatentSync refinement — pixel-accurate mouth movements |
| **Face Enhancement** | GFPGAN v1.4 — restore face quality to 1080p |
| **Real-time Progress** | WebSocket-based live pipeline status |
| **No Watermark** | Full 1080p MP4 output, completely free |
| **Auth System** | Google OAuth + magic link email (NextAuth.js v5) |
| **Rate Limiting** | Configurable per-IP and per-user limits |
| **Docker Deploy** | One-command deployment with Docker Compose |

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Next.js   │────▶│   FastAPI    │────▶│  Celery Worker  │
│  Frontend   │◀────│   Backend    │◀────│  (GPU Tasks)    │
│  Port 3000  │ WS  │  Port 8000   │Redis│                 │
└─────────────┘     └──────────────┘     └────────┬────────┘
                           │                       │
                    ┌──────┴──────┐        ┌───────┴───────┐
                    │  PostgreSQL │        │  AI Pipeline  │
                    │  (Users/    │        │               │
                    │   Jobs)     │        │  XTTS v2      │
                    └─────────────┘        │  MuseTalk     │
                    ┌─────────────┐        │  LatentSync   │
                    │    MinIO    │        │  GFPGAN       │
                    │  (S3 Files) │        │  FFmpeg       │
                    └─────────────┘        └───────────────┘
```

### AI Pipeline Flow

```
Photo + Voice + Script
        │
        ▼
  ┌─────────────┐  20%    ┌────────────────┐  35%
  │  XTTS v2    │────────▶│   MuseTalk     │──────┐
  │ Voice Clone │         │ Face Animation │      │
  └─────────────┘         └────────────────┘      │
                                                   ▼
  ┌─────────────┐  10%    ┌────────────────┐  20% ┌──────────┐ 15%
  │   FFmpeg    │◀────────│   GFPGAN v1.4  │◀─────│LatentSync│
  │  Encoding   │         │  Enhancement   │      │ Lip Sync │
  └──────┬──────┘         └────────────────┘      └──────────┘
         │
         ▼
    Final MP4 (1080p)
```

## 🚀 Quick Start

### Prerequisites

- **Docker** + **Docker Compose** v2
- **NVIDIA GPU** with 8GB+ VRAM (RTX 3060 or better)
- **NVIDIA Container Toolkit** (`nvidia-docker2`)

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/cloneai-pro.git
cd cloneai-pro

# Copy and edit environment variables
cp .env.example .env
# Edit .env with your secrets (Postgres password, NextAuth secret, etc.)
```

### 2. Launch with Docker Compose

```bash
# Full production stack (requires NVIDIA GPU)
docker compose up -d

# Development (no GPU — just infra services)
docker compose -f docker-compose.dev.yml up -d
```

### 3. Open in browser

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001

---

## 🛠️ Development Setup

### Backend (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start dev infrastructure
docker compose -f ../docker-compose.dev.yml up -d

# Run the API server
python run.py
# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Copy environment variables
cp .env.local.example .env.local
# Edit .env.local with your settings

# Start dev server
npm run dev
# App available at http://localhost:3000
```

### Celery Worker

```bash
cd backend
celery -A app.tasks worker --loglevel=info --concurrency=2
```

---

## 📁 Project Structure

```
cloneai-pro/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Pydantic settings
│   │   ├── routers/
│   │   │   ├── health.py        # Health check endpoint
│   │   │   ├── upload.py        # File upload (photo/voice)
│   │   │   ├── clone.py         # Clone CRUD + WebSocket
│   │   │   ├── voice.py         # Voice-only endpoints
│   │   │   └── video.py         # Video download/preview
│   │   ├── models/
│   │   │   ├── schemas.py       # Pydantic v2 request/response
│   │   │   └── database.py      # SQLAlchemy async models
│   │   ├── services/
│   │   │   ├── voice_clone.py   # XTTS v2 wrapper
│   │   │   ├── face_animate.py  # MuseTalk face animation
│   │   │   ├── lip_sync.py      # LatentSync refinement
│   │   │   ├── enhance.py       # GFPGAN v1.4 enhancement
│   │   │   ├── pipeline.py      # Full orchestrator
│   │   │   └── model_manager.py # Model loading/caching
│   │   ├── tasks/
│   │   │   └── generation.py    # Celery async tasks
│   │   └── utils/
│   │       ├── file_handler.py  # File validation & cleanup
│   │       └── gpu_manager.py   # GPU memory management
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Landing page
│   │   ├── layout.tsx           # Root layout + fonts
│   │   ├── globals.css          # Tailwind + custom styles
│   │   ├── dashboard/
│   │   │   ├── page.tsx         # Dashboard (job history)
│   │   │   └── create/page.tsx  # Clone creation wizard
│   │   ├── auth/
│   │   │   ├── signin/page.tsx  # Sign in (Google + Magic Link)
│   │   │   └── error/page.tsx   # Auth error page
│   │   └── api/auth/[...nextauth]/route.ts
│   ├── components/
│   │   ├── landing/             # 8 landing page sections
│   │   ├── clone-wizard/        # 4-step creation wizard
│   │   └── providers.tsx        # React Query + Auth providers
│   ├── lib/
│   │   ├── api.ts               # API client + WebSocket
│   │   ├── auth.ts              # NextAuth.js v5 config
│   │   ├── store.ts             # Zustand state management
│   │   └── utils.ts             # Utilities
│   ├── middleware.ts            # Auth route protection
│   ├── Dockerfile
│   └── package.json
├── nginx/
│   └── nginx.conf               # Reverse proxy config
├── docker-compose.yml           # Full production stack
├── docker-compose.dev.yml       # Dev (infra only)
├── .env.example
└── README.md
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_PASSWORD` | `cloneai_secret` | PostgreSQL password |
| `MINIO_ROOT_USER` | `cloneai` | MinIO access key |
| `MINIO_ROOT_PASSWORD` | `cloneai_secret` | MinIO secret key |
| `NEXTAUTH_SECRET` | — | NextAuth.js encryption secret |
| `GOOGLE_CLIENT_ID` | — | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | — | Google OAuth secret |
| `RESEND_API_KEY` | — | Resend API key for magic links |

### GPU Requirements

| GPU | VRAM | Performance |
|---|---|---|
| RTX 3060 | 12GB | ~90s per video |
| RTX 3080 | 10GB | ~60s per video |
| RTX 4090 | 24GB | ~30s per video |
| A100 | 40GB | ~15s per video |

## 🌍 Supported Languages

XTTS v2 supports 17 languages out of the box:

English, Spanish, French, German, Italian, Portuguese, Polish, Turkish, Russian, Dutch, Czech, Arabic, Chinese, Japanese, Korean, Hungarian, Hindi

## 🔒 Security

- All uploads validated (MIME type + magic bytes)
- File size limits (10MB photos, 25MB voice)
- Rate limiting per IP (Nginx) and per user (FastAPI)
- CORS restricted to allowed origins
- Auth middleware protects dashboard routes
- No user data sent to external services (100% self-hosted)

## 📊 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/upload/photo` | Upload photo |
| `POST` | `/api/v1/upload/voice` | Upload voice sample |
| `POST` | `/api/v1/clone/create` | Start clone generation |
| `GET` | `/api/v1/clone/{id}/status` | Get job status |
| `WS` | `/api/v1/clone/{id}/ws` | Real-time progress |
| `GET` | `/api/v1/video/{id}/download` | Download result |
| `GET` | `/api/v1/voice/languages` | List supported languages |
| `DELETE` | `/api/v1/clone/{id}` | Delete a clone job |

## 🆚 Cost Comparison

| Service | Monthly Cost | Videos/mo | Watermark |
|---|---|---|---|
| HeyGen | $29 | 15 | Yes (free) |
| Synthesia | $30 | 10 | Yes (free) |
| ElevenLabs | $22 | Limited | N/A |
| **CloneAI Pro** | **$0** | **Unlimited** | **No** |

*Only cost: your GPU electricity (~$0.05/video on RTX 3060)*

## 📄 License

MIT License — free for personal and commercial use.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

**Built with** FastAPI · Next.js 15 · XTTS v2 · MuseTalk · GFPGAN · Docker
