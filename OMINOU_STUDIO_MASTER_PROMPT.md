# OMINOU STUDIO — MASTER PROMPT

> **Use this prompt with any AI coding tool (ChatGPT, Claude, Gemini, Copilot, Cursor, etc.) to continue developing Ominou Studio. Paste this entire document as context.**

---

## IDENTITY & VISION

You are the lead architect and full-stack developer for **Ominou Studio** — a premium, all-in-one AI creative platform that combines 7 AI-powered studios into a single product. Think of it as **Adobe Creative Suite meets AI** — one subscription, one interface, seven specialized creative tools powered by AI.

**Brand Name:** Ominou Studio (sometimes stylized as "OMINOU")
**Tagline:** "Your AI Production Crew"
**Philosophy:** Every external AI provider (OpenAI, Google, Runway, ElevenLabs, etc.) is rebranded under Ominou's own engine names. Users never see third-party branding — everything feels like Ominou's proprietary technology.

---

## PLATFORM ARCHITECTURE

### Tech Stack
| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 15.1.0 (App Router), React 19, TypeScript 5.7, Tailwind CSS 3.4, Zustand 5.0 |
| **Gateway** | FastAPI (Python), port 1993, unified API entry point |
| **Services** | 10 FastAPI microservices (ports 8001-8010) |
| **Database** | SQLite + aiosqlite (dev), PostgreSQL (prod) |
| **Auth** | JWT tokens (HS256, 24h expiry), API key management |
| **Storage** | Local filesystem (dev), S3-compatible (prod) |
| **Video Processing** | FFmpeg (required on system PATH) |
| **TTS** | Edge TTS (free, 40+ languages), OpenAI TTS, ElevenLabs |
| **AI Video** | 6 providers with automatic fallback chain |
| **AI Music** | Suno API → FFmpeg ambient synthesis fallback |
| **Deployment** | Docker Compose, Nginx reverse proxy |

### Directory Structure
```
d:\ominou-studio\
├── platform/
│   ├── gateway/              # FastAPI gateway (port 1993)
│   │   └── main.py           # Unified entry point, CORS, rate limiting, routing
│   ├── frontend/             # Next.js 15 app (port 2102)
│   │   └── src/
│   │       ├── app/          # App Router pages
│   │       │   ├── (auth)/   # Login, Register
│   │       │   └── (dashboard)/dashboard/
│   │       │       ├── page.tsx              # Main dashboard
│   │       │       ├── video-studio/         # Film Studio (MAIN FEATURE)
│   │       │       ├── voice-studio/         # Voice Studio
│   │       │       ├── design-studio/        # Design Studio
│   │       │       ├── code-studio/          # Code Studio
│   │       │       ├── ai-writer/            # AI Writer
│   │       │       ├── music-studio/         # Music Studio
│   │       │       ├── workflows/            # Workflow Builder
│   │       │       └── settings/             # Profile, Billing, API Keys, Team
│   │       ├── components/   # Reusable UI components
│   │       ├── lib/          # API client, auth, utils
│   │       ├── store/        # Zustand state management
│   │       └── types/        # TypeScript type definitions
│   ├── services/
│   │   ├── auth/             # Auth + User management (port 8001) ✅ IMPLEMENTED
│   │   ├── video/            # Film Studio engine (port 8005) ✅ FULLY IMPLEMENTED
│   │   │   └── app/engines/
│   │   │       ├── video_engine.py        # 7-step pipeline orchestrator
│   │   │       ├── screenplay_engine.py   # Script→Screenplay decomposition
│   │   │       ├── audio_pipeline.py      # TTS + background music
│   │   │       ├── video_stitcher.py      # FFmpeg scene concat + audio mix
│   │   │       ├── lip_sync_engine.py     # Lip sync (placeholder)
│   │   │       ├── auto_publish_engine.py # Social media publishing (placeholder)
│   │   │       └── providers/
│   │   │           ├── base.py            # Abstract VideoProvider + ProviderResult
│   │   │           ├── local_provider.py  # FFmpeg offline ✅ ALWAYS WORKS
│   │   │           ├── sora_provider.py   # OpenAI Sora (ominou_prime)
│   │   │           ├── runway_provider.py # Runway Gen-4 (ominou_studio)
│   │   │           ├── kling_provider.py  # Kling v2 (ominou_flow)
│   │   │           ├── seedance_provider.py # Seedance 2.0 (ominou_motion)
│   │   │           └── veo_provider.py    # Google Veo 3 (ominou_vision)
│   │   ├── voice/            # Voice Studio (port 8002) ⚠️ STUB
│   │   ├── design/           # Design Studio (port 8003) ⚠️ STUB
│   │   ├── code/             # Code Studio (port 8004) ⚠️ STUB
│   │   ├── writer/           # AI Writer (port 8006) ⚠️ STUB
│   │   ├── music/            # Music Studio (port 8007) ⚠️ STUB
│   │   ├── workflow/         # Workflow engine (port 8008) ⚠️ STUB
│   │   ├── billing/          # Billing + Stripe (port 8009) ⚠️ STUB
│   │   └── storage/          # Asset storage (port 8010) ❌ EMPTY
│   └── shared/               # Shared infra (auth, config, credits, database)
├── cloneai-pro/              # Sub-project: AI avatar video generator (HeyGen alternative)
├── models/                   # AI model weights
├── outputs/                  # Generated content
└── temp/                     # Temporary files
```

### Startup Commands
```powershell
# Gateway (must set PYTHONPATH)
$env:PYTHONPATH = "d:\ominou-studio\platform"
cd d:\ominou-studio\platform\gateway
python -m uvicorn main:app --host 0.0.0.0 --port 1993

# Frontend
cd d:\ominou-studio\platform\frontend
npx next dev --port 2102

# Or use start-all.ps1 / stop-all.ps1 scripts
```

---

## THE 7 AI STUDIOS

### 1. Film Studio (Video Generation) — ✅ FULLY IMPLEMENTED & TESTED

**The flagship feature.** A complete video generation pipeline that takes a text prompt or structured JSON script and produces a narrated, scored video with multiple scenes.

#### 7-Step Pipeline
```
Step 1: Screenplay Decomposition
    Input: Text prompt OR JSON script → Output: Scene-by-scene screenplay
    
Step 2: Narration Generation (Edge TTS / OpenAI / ElevenLabs)
    Input: Per-scene narration text → Output: MP3 audio per scene
    
Step 3: Video Scene Generation (6 AI providers with fallback)
    Input: Per-scene visual prompt → Output: MP4 clip per scene
    
Step 4: Lip Sync (optional, placeholder)
    Input: Scene video + narration audio → Output: Lip-synced video
    
Step 5: Background Music Generation (Suno / FFmpeg synthesis)
    Input: Mood + genre + duration → Output: Ambient music track
    
Step 6: Video Stitching (FFmpeg)
    Input: All scene clips + narration + music → Output: Final MP4
    
Step 7: Auto-Publishing (placeholder)
    Input: Final video → Output: Published to YouTube/TikTok/Instagram/X/LinkedIn
```

#### Video Providers (Branded as Ominou Engines)
| Internal Name | Display Name | Real Provider | Max Duration | Needs API Key | Special |
|--------------|-------------|--------------|-------------|--------------|---------|
| `ominou_local` | Ominou Local | FFmpeg | 600s | None | Always available, offline |
| `ominou_prime` | Ominou Prime | OpenAI Sora | 20s | OPENAI_API_KEY | Story, physics |
| `ominou_vision` | Ominou Vision | Google Veo 3 | 8s | GOOGLE_AI_API_KEY | Audio+video generation |
| `ominou_motion` | Ominou Motion | Seedance 2.0 | 16s | SEEDANCE_API_KEY | Cinematic realism |
| `ominou_flow` | Ominou Flow | Kling v2 | 16s | KLING_API_KEY | Motion, animation |
| `ominou_studio` | Ominou Studio | Runway Gen-4 | 16s | RUNWAY_API_KEY | Camera control |

**Provider Fallback:** If primary fails → tries `ominou_local` → then each provider in order. Pipeline never fully fails.

#### Screenplay Engine — JSON Script Support
The system accepts structured JSON scripts in ANY language:
```json
{
    "title": "My Video",
    "language": "telugu",
    "voice": { "type": "male", "tone": "devotional", "speed": 0.9 },
    "duration": 180,
    "scenes": [
        {
            "scene": 1,
            "visual": "Description of what to show (English recommended)",
            "camera": "Camera movement description",
            "bgm": "Background music description",
            "narration": "నేరేషన్ టెక్స్ట్ ఏ భాషలోనైనా",
            "dialogue": "Character dialogue",
            "sfx": "Sound effects description"
        }
    ]
}
```

**Supported JSON fields:** title, language, voice (type/tone/speed), duration, scenes (scene/visual/camera/bgm/narration/dialogue/sfx)

**Screenplay fallback chain:**
1. `_parse_json_script()` — Try JSON parsing first
2. `_parse_script_to_scenes()` — Try SCENE/INT./EXT. markers
3. GPT-4o enhancement (if OPENAI_API_KEY set) — AI-powered screenplay generation
4. `_fallback_screenplay()` — Split by sentences, cycle through preset cameras/lighting

#### TTS Narration — 40+ Language Support
**Fallback chain:** ElevenLabs → OpenAI TTS → Edge TTS (free, always works)

**Language auto-detection** via Unicode character ranges:
- **Indic:** Telugu (te-IN), Hindi (hi-IN), Tamil (ta-IN), Kannada (kn-IN), Malayalam (ml-IN), Bengali (bn-IN), Gujarati (gu-IN), Marathi (mr-IN)
- **East Asian:** Japanese (ja-JP), Korean (ko-KR), Chinese (zh-CN)
- **European:** Spanish (es-ES), French (fr-FR), German (de-DE), Portuguese (pt-BR)
- **Middle Eastern:** Arabic (ar-SA)
- **Default:** English (en-US)

Each language has dedicated male + female voice pairs. Language detected automatically from text, or forced via JSON script's `language` field.

#### Background Music — Mood-based Synthesis
**Fallback chain:** Suno API → FFmpeg ambient synthesis (always works, no API key)

FFmpeg synthesis creates layered sine wave pads:
- **Epic:** C2 + E2 + C3 (powerful bass)
- **Calm:** C3 + E3 + G3 (gentle major triad)
- **Dark:** B1 + Eb2 + Gb2 (dissonant minor)
- **Romantic, Tense, Uplifting** — each with specialized chord voicings
- Tempo modulation: slow (0.5Hz), medium (1Hz), fast (2Hz)

#### Video Stitching — FFmpeg Pipeline
```
Stage 1: Concatenate scene clips → scale/pad to target resolution
Stage 2: Merge narration audio files → mix with music (narration=1.0, music=0.3)
Stage 3: Mux video + mixed audio → final MP4

Quality Presets:
  standard: CRF 23, fast preset, 128k audio
  high:     CRF 18, medium preset, 192k audio
  ultra:    CRF 12, slow preset, 320k audio + noise filter + vignette
```

#### Local Provider (FFmpeg Offline Generation)
When no API keys are available, the local provider creates cinematic scenes using FFmpeg filters:
- Animated gradient backgrounds (mood-based color palettes)
- Ken Burns zoom effect (slow zoom in)
- Film grain overlay
- Vignette effect
- Scene title text overlay (English only — non-Latin scripts gracefully handled)
- Lower-third text for visual descriptions
- 24fps, libx264, AAC audio

---

### 2. Voice Studio — ⚠️ STUB (Routes + UI exist, engines return mock data)

**Frontend:** Complete UI with TTS, Voice Clone, Dubbing tabs
**Backend:** 7 API routes defined, return hardcoded fake responses
**Needs:** Real TTS engine integration (Edge TTS already works in video pipeline — can be reused), voice cloning via XTTS v2 or Coqui, dubbing pipeline

**API Routes:**
- `POST /api/tts` — Text-to-speech (1 credit)
- `POST /api/clone` — Voice cloning (5 credits)
- `POST /api/dub` — Translation + dubbing (10 credits)
- `GET /api/voices` — 8 voice presets (Aria, Marcus, Priya, Chen, Sofia, Kai, Luna, Ravi)
- `GET /api/styles` — Voice styles
- `GET /api/languages` — Supported languages

---

### 3. Design Studio — ⚠️ STUB (Routes + UI exist, engines return mock data)

**Frontend:** Complete UI with AI Generate, Templates, Edit Tools tabs
**Backend:** 7 API routes, return hardcoded fake responses
**Needs:** Image generation (DALL-E 3, Stable Diffusion, Flux), background removal (rembg), upscaling (Real-ESRGAN)

**API Routes:**
- `POST /api/generate` — AI image generation (3 credits)
- `POST /api/remove-background` — BG removal (2 credits)
- `POST /api/upscale` — Image upscaling (2 credits)
- `POST /api/from-template` — Template-based creation (1 credit)
- `GET /api/templates`, `GET /api/styles`, `GET /api/filters`

**Styles:** photorealistic, digital_art, watercolor, oil_painting, sketch, anime, 3d_render, pop_art, minimalist, cyberpunk, fantasy, pixel_art

---

### 4. Code Studio — ⚠️ STUB (Routes + UI exist, engines return sample code)

**Frontend:** Complete UI with Generate, Explain, New Project tabs
**Backend:** 7 API routes, return sample code snippets
**Needs:** LLM integration (GPT-4o / Claude / local models) for code generation, explanation, refactoring

**API Routes:**
- `POST /api/generate` — Code generation (2 credits)
- `POST /api/explain` — Code explanation (1 credit)
- `POST /api/refactor` — Code refactoring (2 credits)
- `POST /api/project` — Project scaffolding
- `POST /api/deploy` — Deployment (5 credits)
- `GET /api/languages` — 14 languages (Python, JS, TS, Java, Go, Rust, C++, Ruby, PHP, Swift, Kotlin, Dart, SQL, Bash)
- `GET /api/templates` — 6 project templates (Next.js, FastAPI, Express, Django, React Native, Flask)

---

### 5. AI Writer — ⚠️ STUB (Routes + UI exist, engines return mock markdown)

**Frontend:** Complete UI with Write, Rewrite, SEO Tools tabs
**Backend:** 5 API routes, return mock content
**Needs:** LLM integration for content generation, SEO analysis tools

**API Routes:**
- `POST /api/generate` — Content generation (1-5 credits based on type)
- `POST /api/rewrite` — Content rewriting (2 credits)
- `POST /api/seo` — SEO optimization (2 credits)
- `GET /api/content-types` — 10 types (blog, ad copy, social post, email, script, product desc, press release, landing page, SEO meta, resume)
- `GET /api/tones` — 8 tones (professional, casual, friendly, authoritative, humorous, inspirational, technical, persuasive)

---

### 6. Music Studio — ⚠️ STUB (Routes + UI exist, engines return mock data)

**Frontend:** Complete UI with Generate Music, Jingle Maker, Sound Effects, Remix tabs
**Backend:** 7 API routes, return fake responses
**Needs:** Music generation AI (Suno API already partially integrated in video pipeline — can be reused), SFX library, audio processing

**API Routes:**
- `POST /api/generate` — Music generation (5 credits)
- `POST /api/jingle` — Brand jingle (3 credits)
- `POST /api/sfx` — Sound effects (2 credits)
- `POST /api/remix` — Audio remix (5 credits)
- `GET /api/genres` — 18 genres
- `GET /api/moods` — 16 moods
- `GET /api/sfx-categories` — 5 categories (UI sounds, nature, transitions, ambient, musical)

---

### 7. Workflow Builder — ⚠️ STUB (Routes + UI exist, no execution engine)

**Frontend:** Complete UI with My Workflows, Templates, Builder tabs
**Backend:** 7 API routes, CRUD only, no actual workflow execution
**Needs:** Workflow execution engine that chains services together, step dependency resolution, parallel execution

**API Routes:**
- `POST /api/create`, `POST /api/from-template`, `POST /api/run/{id}`
- `GET /api/list`, `GET /api/{id}`, `DELETE /api/{id}`
- `GET /api/templates`, `GET /api/steps`

**Templates:** Content Campaign, Video Production, Brand Kit, Podcast Pipeline

---

## FRONTEND UI DESIGN

### Theme & Design System
```css
/* Color Palette */
Primary Brand:     #6366f1 (indigo)
Dark Background:   #06060b (near-black body)
Card Background:   #111119
Border Color:      #1e1e30
Text Primary:      #f0f0f5 (off-white)
Text Secondary:    #9ca3af (light gray)
Accent Green:      #34d399
Accent Red:        #f87171
Accent Yellow:     #fbbf24
Accent Purple:     #a78bfa
Accent Cyan:       #22d3ee

/* Key Effects */
.glass         → frosted glass (backdrop-blur 24px)
.glass-strong  → stronger glass (backdrop-blur 40px)
.gradient-text → animated gradient (indigo → purple → pink)
.glow          → brand color drop-shadow
.card-hover    → transform + shadow lift on hover
.bg-mesh       → animated radial gradient background (20s loop)
.bg-noise      → turbulence noise overlay (cinematic texture)
```

### Dashboard Layout
- **Sidebar:** Collapsible (240px / 68px), 10 navigation items with icons, credit bar at bottom
- **Topbar:** 56px height, plan badge, credit display, user avatar, logout
- **Content:** max-w-7xl centered container
- **Dashboard Home:** Welcome header, 4 stat cards, AI Crew bar (7 specialists), Studios grid (3-column), Workflows CTA, Recent Activity

### AI Crew (7 Virtual Specialists)
| Role | Icon | Active During |
|------|------|--------------|
| Director | 🎬 | 10-25% progress |
| DOP (Cinematographer) | 📷 | 25-50% progress |
| Scriptwriter | ✍️ | 0-10% progress |
| Music Director | 🎵 | 50-80% progress |
| Designer | 🎨 | 25-50% progress |
| VFX Artist | ✨ | 25-50% progress |
| Choreographer | 💃 | 50-80% progress |

### Film Studio Page (Main Feature)
**3 Tabs:** Film Studio | Clone Lab | AI Crew

**Film Studio Tab — Two-column layout:**

Left Panel (5 col):
- Input mode toggle: Chat (💬) / Script (📜)
- Chat interface (520px, auto-scroll, role-based message styling)
- Script textarea (supports SCENE markers + JSON format)

Right Panel (7 col):
- Duration: 1min, 2min, 3min, 5min, 10min, Custom (range slider)
- Style: Cinematic, 3D, 2D Animation, Normal, Documentary, Slow Motion, Time Lapse, Vlog, Commercial, Music Video
- Resolution: 1080p, 2K, 4K
- Quality: Standard, High, Ultra
- Aspect Ratio: 16:9, 9:16, 1:1, 4:5, etc.
- Narration toggle + Voice selector (Aria, Marcus, Priya, Chen, Sofia, Luna)
- Music toggle
- Lip Sync toggle
- Provider: Auto or specific engine
- Publishing: YouTube, Instagram Reels, TikTok, X, LinkedIn
- 6 Prompt Templates: Product Demo, Travel Vlog, Brand Story, Music Video, Documentary, Social Ad
- Generate button (gradient, full-width)

**Clone Lab Tab:** Voice/Face clone upload interfaces
**AI Crew Tab:** 7 crew members with real-time status during generation

---

## API REFERENCE

### Gateway Routes (port 1993)
```
GET  /                → App info + active modules
GET  /health          → Health check (pings all services)
*    /api/v1/{service}/{path} → Proxy to microservice
```

### Video API (mounted directly on gateway)
```
POST   /api/v1/video/generate          → Generate video from prompt/script
GET    /api/v1/video/progress/{job_id} → Poll generation progress
GET    /api/v1/video/providers         → List available providers
POST   /api/v1/video/publish           → Publish to social platforms
GET    /api/v1/video/platforms         → Supported platforms
POST   /api/v1/video/face-swap         → Face swap in video
POST   /api/v1/video/edit              → Apply video edits
POST   /api/v1/video/upscale           → Upscale resolution
GET    /api/v1/video/styles            → 10 video styles
GET    /api/v1/video/resolutions       → Available resolutions
GET    /api/v1/video/formats           → mp4, mov, avi, webm, mkv
```

### Generate Request Schema
```json
{
    "prompt": "Required (1-2000 chars)",
    "script": "Optional (max 50000) — JSON or screenplay format",
    "duration": 15,
    "style": "cinematic",
    "resolution": "1080p",
    "quality": "standard",
    "aspect_ratio": "16:9",
    "include_narration": true,
    "include_music": true,
    "voice": "onyx",
    "provider": "auto",
    "enable_lip_sync": false,
    "publish_to": ["youtube", "tiktok"]
}
```

---

## CREDIT SYSTEM

### Plans
| Plan | Price | Monthly Credits |
|------|-------|----------------|
| Free | $0 | 50 |
| Pro | $29/mo | 2,000 |
| Team | $79/seat/mo | 10,000 |
| Enterprise | Custom | Unlimited |

### Credit Costs
```
voice_tts: 1          voice_clone: 5         voice_dub: 10
design_generate: 3    design_remove_bg: 2    design_template: 1
code_generate: 2      code_deploy: 5
video_generate: 15    video_clone: 10        video_subtitle: 3
writer_blog: 3        writer_copy: 1         writer_script: 5    writer_seo: 2
music_generate: 5     music_sfx: 2
workflow_run: 0 (charged per step)
```

---

## DATABASE MODELS

### User
```
id, email (unique), password_hash, full_name, company, phone, avatar_url
plan (free/pro/team/enterprise), credits_remaining, credits_used_total
stripe_customer_id, stripe_subscription_id
is_active, is_verified, is_admin
created_at, updated_at, last_login
```

### APIKey
```
id, user_id, name, key_hash, key_prefix, permissions, is_active, last_used, created_at
```

### UsageLog
```
id, user_id, service, action, credits_used, metadata_json, created_at
```

---

## SHARED INFRASTRUCTURE

### Configuration (shared/config.py)
```python
APP_NAME = "Ominou Studio"
JWT_SECRET = "ominou-studio-secret-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 1440  # 24 hours
DATABASE_URL = "sqlite+aiosqlite:///./ominou_studio.db"
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_PER_HOUR = 1000

# API Keys (all optional — system degrades gracefully without them)
OPENAI_API_KEY, ANTHROPIC_API_KEY, STABILITY_API_KEY, ELEVENLABS_API_KEY
GOOGLE_AI_API_KEY, RUNWAY_API_KEY, KLING_API_KEY, SEEDANCE_API_KEY
SUNO_API_KEY, STRIPE_SECRET_KEY
```

### Service Ports
```
Gateway:  1993        Auth:     8001       Voice:    8002
Design:   8003        Code:     8004       Video:    8005
Writer:   8006        Music:    8007       Workflow: 8008
Billing:  8009        Storage:  8010       Frontend: 2102
```

---

## CLONEAI PRO (Sub-Project)

A standalone **open-source HeyGen/Synthesia alternative** — AI avatar video generator with lip-synced talking head videos.

**Pipeline:** XTTS v2 voice cloning (20%) → MuseTalk face animation (35%) → LatentSync lip-sync (15%) → GFPGAN enhancement (20%) → FFmpeg encoding (10%)

**Features:** Voice cloning from 30-sec sample (17 languages), perfect lip sync, face enhancement to 1080p, WebSocket progress, Google OAuth, Docker Compose deployment.

**Tech:** Next.js 15 frontend + FastAPI + Celery workers + PostgreSQL + MinIO

---

## WHAT'S FULLY WORKING (Tested & Verified) ✅

1. **Video Generation Pipeline** — End-to-end from text/JSON script to final MP4
2. **JSON Script Parser** — Parses structured scripts with per-scene visual/camera/bgm/narration/dialogue/sfx
3. **40+ Language TTS** — Auto-detects language from text, selects correct voice (Telugu, Hindi, Tamil, etc.)
4. **6 Video Providers** — With automatic fallback chain (local provider always works without API keys)
5. **Background Music** — FFmpeg ambient synthesis when no Suno API key
6. **FFmpeg Stitching** — Scene concatenation, narration + music mixing, quality presets
7. **Frontend Dashboard** — Full UI for all 7 studios (forms, settings, outputs)
8. **Auth System** — Registration, login, JWT, API keys, credits
9. **Gateway** — Routing, rate limiting, CORS, static file serving
10. **Real-time Progress** — Polling-based progress with AI Crew status updates

---

## WHAT NEEDS TO BE IMPLEMENTED 🔧

### HIGH PRIORITY (Core Revenue Features)

1. **Voice Studio Engine** — Wire up real TTS (Edge TTS already in video pipeline — reuse it), add voice cloning (XTTS v2 / Coqui TTS), add dubbing pipeline
2. **Design Studio Engine** — Wire up image generation (DALL-E 3 / Stable Diffusion XL / Flux via API), background removal (rembg Python library), upscaling (Real-ESRGAN)
3. **Music Studio Engine** — Wire up Suno API (already partially integrated), add SFX library, add jingle generator, add remix capability
4. **Writer Engine** — Wire up LLM (GPT-4o / Claude) for content generation, SEO analysis, rewriting
5. **Code Studio Engine** — Wire up LLM for code generation, explanation, refactoring, project scaffolding

### MEDIUM PRIORITY (Platform Completion)

6. **Billing + Stripe Integration** — Connect Stripe for subscriptions and credit purchases, webhook handling, invoice generation
7. **Workflow Execution Engine** — Build the engine that actually chains services together, resolves dependencies, runs steps in parallel where possible
8. **Storage Service** — Asset management, file uploads, CDN integration, thumbnail generation
9. **Real-time WebSocket** — Replace polling with WebSocket for live progress updates
10. **User Dashboard Stats** — Real data instead of hardcoded numbers (projects, credits, time saved, assets)

### LOW PRIORITY (Enhancement & Polish)

11. **Social Media Publishing** — Real YouTube/TikTok/Instagram API integration for auto-publishing
12. **Lip Sync Engine** — Real lip sync using LatentSync or similar (placeholder exists)
13. **Face Swap** — Wire up face swap capability (route exists, no engine)
14. **Video Editing** — Wire up trim, crop, filter operations (route exists, no engine)
15. **Video Upscaling** — Wire up Real-ESRGAN for video upscaling (route exists, no engine)
16. **Per-Scene BGM** — Use JSON script's per-scene `bgm` field to generate different music per scene (currently one track for whole video)
17. **Character Consistency** — AI-powered character tracking across scenes (prompt injection exists, needs stronger enforcement)
18. **CloneAI Pro Integration** — Merge Clone Lab features with CloneAI Pro's avatar pipeline
19. **Team Collaboration** — Multi-user workspaces, shared projects, role-based access
20. **Asset Library** — User's generated content organized, searchable, reusable

### INFRASTRUCTURE

21. **Production Database** — Migrate from SQLite to PostgreSQL
22. **Redis Cache** — Session caching, rate limiting, job queues
23. **Celery Workers** — Background task processing for long-running generations
24. **S3 Storage** — Move from local filesystem to S3-compatible storage
25. **Docker Production** — Production-ready Docker Compose with health checks, restart policies, logging
26. **CI/CD** — Automated testing, building, deployment pipeline
27. **Monitoring** — Error tracking (Sentry), metrics (Prometheus), logging (structured JSON)
28. **Security Hardening** — Rate limiting per user (not just IP), input sanitization, CSRF protection, Content Security Policy

---

## KNOWN ISSUES & TECHNICAL DEBT

1. **Hardcoded JWT secret** — "ominou-studio-secret-change-in-production" must be changed for production
2. **Invalid OpenAI API key** — Falls through to Edge TTS (works, but limits screenplay AI enhancement)
3. **FFmpeg drawtext can't render non-Latin scripts** — Telugu/Hindi/etc. text falls back to scene number labels in local provider
4. **Single-threaded gateway** — No Celery workers for background processing
5. **No file cleanup** — Generated videos/audio accumulate in storage directories without TTL
6. **Frontend isScript detection** — Checks for JSON format `{...}` and SCENE/INT./EXT. markers, but edge cases may exist
7. **No input sanitization** on several endpoints — needs validation hardening
8. **CORS allows localhost origins** — Must be restricted for production
9. **Rate limiting is in-memory** — Resets on server restart, not shared across instances
10. **All studio pages (except Film Studio) display mock data** — Users see fake results

---

## DEVELOPMENT RULES

1. **Brand Everything Under Ominou** — Never expose third-party provider names (OpenAI, Google, Runway, etc.) in the UI. Use Ominou engine names.
2. **Graceful Degradation** — Every feature must work without API keys. Use free alternatives (Edge TTS, FFmpeg synthesis, local provider) as fallbacks.
3. **Fault Tolerance** — No single step failure should crash the pipeline. Each stage handles its own errors and passes through.
4. **Async Everything** — All backend code uses `async/await`. Use `asyncio.gather()` for parallel operations.
5. **Type Safety** — TypeScript strict mode on frontend. Pydantic models for all API schemas on backend.
6. **Credit Awareness** — Every action has a credit cost. Check credits before execution. Log all usage.
7. **Multi-Language Support** — All text processing must handle Unicode. Auto-detect language. Support RTL scripts.
8. **Quality Tiers** — Standard, High, Ultra quality settings affect every stage (CRF, preset, audio bitrate).
9. **Provider Pattern** — All AI providers follow the abstract base class pattern with `is_available()` + `generate()` + standardized `ProviderResult`.
10. **No Hardcoded Paths** — Use configuration and environment variables. Platform must work on any OS.

---

## EXAMPLE: END-TO-END VIDEO GENERATION FLOW

```
User submits JSON script (Telugu, 3 scenes, 60 seconds)
    ↓
Frontend detects JSON format → sends as `body.script`
    ↓
Gateway receives POST /api/v1/video/generate
    ↓
Step 1: screenplay_engine._parse_json_script()
    → Parses JSON, extracts 3 scenes with Telugu narration
    → Sets language="telugu", voice.type="male"
    → Returns screenplay with visual_prompt, narration, bgm per scene
    ↓
Step 2: audio_pipeline.generate_scene_narrations()
    → Detects Telugu from Unicode range [\u0C00-\u0C7F]
    → Selects voice: te-IN-MohanNeural (male Telugu)
    → ElevenLabs fails (no key) → OpenAI fails (invalid key) → Edge TTS succeeds
    → Generates 3 MP3 files with Telugu narration
    ↓
Step 3: video_engine._generate_scene_with_fallback()
    → Tries ominou_prime (no valid key) → falls back to ominou_local
    → FFmpeg generates 3 cinematic scene clips with gradient backgrounds,
      Ken Burns zoom, film grain, English visual descriptions as overlays
    → 3 parallel batches of scenes
    ↓
Step 4: lip_sync_engine (skipped — not enabled)
    ↓
Step 5: audio_pipeline.generate_background_music()
    → Suno fails (no key) → FFmpeg generates ambient pad
    → Mood="epic" → C2+E2+C3 sine waves with tremolo
    ↓
Step 6: video_stitcher.stitch_scenes()
    → Concatenates 3 scene clips (scale + pad to 1280x720)
    → Merges 3 narration files → mixes with music (1.0 : 0.3 volume)
    → Outputs final_XXXXX.mp4 (3.61 MB)
    ↓
Step 7: auto_publish (skipped — not requested)
    ↓
Response: { job_id, file_url, scenes_generated: 3, has_narration: true, has_music: true }
```

---

## QUICK REFERENCE: ALL API KEYS

| Key | Provider | Used By | Required? |
|-----|---------|---------|-----------|
| `OPENAI_API_KEY` | OpenAI | Screenplay AI (GPT-4o), TTS, Sora video | Optional |
| `GOOGLE_AI_API_KEY` | Google | Veo 3 video generation | Optional |
| `RUNWAY_API_KEY` | Runway | Gen-4 video generation | Optional |
| `KLING_API_KEY` | Kling | Kling v2 video generation | Optional |
| `SEEDANCE_API_KEY` | Seedance | Seedance 2.0 video generation | Optional |
| `ELEVENLABS_API_KEY` | ElevenLabs | Premium TTS voices | Optional |
| `SUNO_API_KEY` | Suno | AI music generation | Optional |
| `ANTHROPIC_API_KEY` | Anthropic | (Reserved for future use) | Optional |
| `STABILITY_API_KEY` | Stability AI | (Reserved for future use) | Optional |
| `STRIPE_SECRET_KEY` | Stripe | Payments & subscriptions | Optional |

**The platform works with ZERO API keys** — all features gracefully degrade to free alternatives (Edge TTS, FFmpeg synthesis, local video provider).

---

*Last updated: April 3, 2026*
*Platform version: 1.0.0*
*Status: Film Studio fully operational, other studios have complete UI but stub backends*
