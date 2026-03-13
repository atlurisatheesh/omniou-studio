# Ominou Studio

**One Studio. Every Creative Tool. Zero Switching.**

An all-in-one AI-powered creative platform combining voice synthesis, code generation, graphic design, video production, AI writing, and music creation — so creators never leave the platform.

## Architecture

```
platform/
├── gateway/           # API Gateway (FastAPI reverse proxy + rate limiting)
├── services/
│   ├── auth/          # Authentication (JWT + OAuth2 + API keys)
│   ├── voice/         # Voice Studio (TTS, cloning, dubbing)
│   ├── design/        # Design Studio (templates, AI image gen)
│   ├── code/          # Code Studio (browser IDE, AI generation)
│   ├── video/         # Video Studio (CloneAI Pro integration)
│   ├── writer/        # AI Writer (blog, copy, scripts, SEO)
│   ├── music/         # Music Studio (BGM, jingles, SFX)
│   ├── workflow/      # Workflow Engine (chain modules)
│   ├── billing/       # Billing & Usage Metering (Stripe)
│   └── storage/       # Asset Manager (S3-compatible)
├── shared/            # Shared utilities, middleware, types
├── frontend/          # Next.js 15 unified dashboard
└── docker/            # Docker & deployment configs
```

## Modules

| Module | Status | Description |
|--------|--------|-------------|
| Voice Studio | MVP | Text-to-speech, voice cloning, multilingual dubbing |
| Design Studio | MVP | Templates, AI image generation, brand kits |
| Code Studio | MVP | Browser IDE, AI code generation, one-click deploy |
| Video Studio | MVP | Video cloning, text-to-video, auto-subtitles |
| AI Writer | MVP | Blog posts, ad copy, scripts, SEO content |
| Music Studio | MVP | Background scores, jingles, sound effects |
| Workflow Engine | MVP | Chain modules together into pipelines |

## Quick Start

```bash
# Backend services
cd platform/gateway
pip install -r requirements.txt
python -m uvicorn app:app --port 8080

# Frontend
cd platform/frontend
npm install
npm run dev
```

## Tech Stack

- **Backend:** Python 3.11+ / FastAPI / SQLAlchemy
- **Frontend:** Next.js 15 / React 19 / Tailwind CSS / Zustand
- **AI:** OpenAI, Anthropic, Stable Diffusion, Whisper, Bark
- **Database:** PostgreSQL + Redis + S3
- **Payments:** Stripe (subscriptions + usage metering)
