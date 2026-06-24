# Ominou Studio Implementation Tracker

Last updated: 2026-04-03 11:46:43 +05:30

## Purpose

This file is the current source of truth for the platform state as of the timestamp above.
It exists because `OMINOU_STUDIO_MASTER_PROMPT.md` is no longer fully aligned with the live repo.

## Executive Summary

Ominou Studio is currently a video-first platform with:

- a strong Film Studio backend
- a real Auth foundation
- partially real backend engines for Voice, Design, Code, Writer, and Music
- mostly mocked frontend pages outside Film Studio and Auth
- simulated Workflow and Billing behavior
- incomplete service orchestration at runtime

Short version:

- Film Studio: strongest and closest to production
- Auth: real and usable
- Voice / Design / Code / Writer / Music backends: partially live
- Workflow / Billing / Storage: not production-ready
- Frontend outside Film Studio: mostly presentational, not truly wired

## Current State By Area

### 1. Film Studio

Status: implemented, strongest module in the product

What is real:

- screenplay decomposition and fallback logic
- JSON script support
- scene-level provider fallback
- multilingual narration fallback chain
- FFmpeg ambient background music fallback
- FFmpeg stitching and output generation
- progress tracking with job state
- publish and lip-sync integration points

What is still incomplete:

- face swap endpoint returns synthetic success data
- edit endpoint returns synthetic success data
- upscale endpoint returns synthetic success data
- lip sync depends on external provider credentials
- auto-publishing falls back to manual/queued behavior if credentials are missing
- startup/runtime wiring still assumes external microservices for the rest of the platform

### 2. Auth

Status: real backend, real frontend login/register wiring

What is real:

- register
- login
- JWT access tokens
- user table
- API key table
- usage log table
- profile update
- password change
- credits lookup

What is still incomplete:

- wildcard CORS on service app
- hardcoded default JWT secret still exists
- API key flow exists, but broad platform-wide enforcement is not complete
- credit deduction and usage logging are not consistently enforced across all modules

### 3. Voice Studio

Status: backend partially real, frontend still mocked

What is real in backend:

- text-to-speech
- voice preset catalog
- language catalog
- dubbing flow
- ElevenLabs and OpenAI-based execution paths

What is not yet product-complete:

- clone flow is provider-dependent and can fall back to a registration-style placeholder result
- no frontend wiring to backend yet
- no stable offline fallback comparable to Film Studio narration pipeline
- no storage browsing or asset lifecycle support

### 4. Design Studio

Status: backend partially real, frontend still mocked

What is real in backend:

- AI image generation
- template-driven generation
- style and filter catalogs

What is incomplete:

- background removal path is weak and model-dependent
- image upscaling is currently a synthetic response, not real processing
- frontend does not call live API
- no true asset management layer

### 5. Code Studio

Status: backend partially real, frontend still mocked

What is real in backend:

- code generation
- code explanation
- code refactor
- language and template catalogs

What is incomplete:

- project creation is simulated metadata, not actual scaffold generation
- deploy is simulated metadata, not real deployment
- frontend is not connected to backend

### 6. AI Writer

Status: backend partially real, frontend still mocked

What is real in backend:

- content generation
- rewriting
- SEO metadata generation
- content type and tone catalogs

What is incomplete:

- frontend is not connected to backend
- SEO analysis is generation-oriented, not true page analysis
- no durable content/project storage model

### 7. Music Studio

Status: backend partially real, frontend still mocked

What is real in backend:

- generation endpoints exist
- genre / mood / category catalogs exist
- Suno integration points exist

What is incomplete:

- fallback audio is currently spoken-description style audio, not true music
- SFX generation is not real sound-design quality
- remix is not true source-audio transformation
- frontend is not connected to backend

### 8. Workflow Builder

Status: mostly simulated

What exists:

- templates
- step catalog
- workflow CRUD shape
- user ownership checks

What is missing:

- real execution engine
- dependency graph execution
- parallel step execution
- output handoff between steps
- persistent workflow storage
- frontend wiring

### 9. Billing

Status: simulated

What exists:

- plan definitions
- current-plan response shape
- fake subscribe / buy-credit responses
- fake usage breakdown
- fake invoice response

What is missing:

- Stripe integration
- webhook handling
- real subscription lifecycle
- invoice syncing
- credit purchase bookkeeping
- frontend wiring to real account state

### 10. Storage

Status: effectively missing as a service

What exists:

- local file outputs under service storage folders
- gateway static mount for video storage

What is missing:

- actual storage microservice implementation
- central asset index
- upload handling
- thumbnail generation
- retention / cleanup policy
- reusable asset library

## Frontend Truth

Status: visually strong, operationally uneven

What is truly wired:

- auth pages call `/api/v1/auth/...`
- Film Studio calls the video endpoints directly
- Next.js rewrite exists for `/api/v1/*`

What is still mocked:

- Voice Studio page
- Design Studio page
- Code Studio page
- AI Writer page
- Music Studio page
- Workflows page
- Settings page
- Dashboard stats and activity

Most of these pages still use local arrays and timeout-based fake success states instead of shared API client integration.

## Runtime Truth

Status: architecture and startup flow are out of sync

Important mismatch:

- the repo contains multiple FastAPI service apps
- the gateway expects those services to be reachable
- `platform/start-all.ps1` currently launches only the gateway and frontend

Effect:

- many backend modules can exist in code but still be unavailable in a normal local run

## Test Truth

The repo contains a substantial Playwright-style deep test suite and report.

Known evidence currently in repo:

- report timestamp: March 13, 2026
- total tests: 156
- passed: 148
- warnings: 8
- failed: 0

Important caveat:

- this is useful evidence of UI coverage
- it is not a guarantee that current April 3 code still matches those exact results
- several frontend pages still pass UI tests while remaining functionally mocked

## Priority Classification

### Done

- Film Studio core generation pipeline
- Auth DB models and JWT flow
- login/register frontend wiring
- gateway proxy and mounted video routes
- shared API client file
- backend service skeletons for all major studios except Storage

### Partially Done

- Voice backend
- Design backend
- Code backend
- Writer backend
- Music backend
- lip sync integration
- auto-publish integration

### Mocked Or Simulated

- most non-video dashboard pages
- workflow execution
- billing and invoices
- code project creation and deployment
- design upscaling
- video face swap / edit / upscale result handling

### Missing

- real Storage service
- unified asset library
- startup orchestration for all services
- real credit accounting across the platform
- production queueing/workers
- production deployment hardening

## Recommended Build Order

### Phase 1: Make The Existing Platform Honest

1. Wire all dashboard pages to real backend APIs using the shared client.
2. Remove timeout-based fake success flows from Voice, Design, Code, Writer, Music, Workflows, Settings, and Dashboard.
3. Fix Film Studio response/progress handling so frontend matches backend response shape.
4. Update startup scripts so all required services can run together locally.

### Phase 2: Replace Remaining Simulations

1. Build real Workflow execution.
2. Build real Billing and Stripe integration.
3. Replace Design upscaling placeholder with actual processing.
4. Replace Code project/deploy placeholders with real behavior or clearly mark them as roadmap.
5. Improve Music generation from spoken-preview fallback to true audio generation.

### Phase 3: Platform Infrastructure

1. Build Storage service.
2. Add centralized asset indexing.
3. Add cleanup / retention policies.
4. Move toward PostgreSQL, Redis, workers, and S3-compatible storage.

### Phase 4: Production Hardening

1. remove insecure defaults
2. tighten CORS
3. enforce credits and usage logging consistently
4. improve validation and sanitization
5. add CI/CD and monitoring

## Recommended Immediate Work Packages

### Package A: Frontend-to-Backend Wiring

Target outcome:

- all non-video studios use the real backend APIs
- settings and dashboard use real user and billing data where available

Why first:

- highest visible value
- reveals backend gaps quickly
- turns the product from "good shell" into "real platform"

### Package B: Runtime Orchestration

Target outcome:

- one reliable local command to boot the whole platform

Why next:

- removes false negatives during testing
- makes every module easier to validate

### Package C: Workflow + Billing

Target outcome:

- true monetizable platform behavior

Why next:

- these are core business systems, not visual polish

## Risks

- The master prompt currently overstates some areas and understates others.
- The frontend can make the platform look more complete than it is.
- Service code existing in repo is not the same as service availability at runtime.
- The product currently has strong module islands but not yet a fully unified operating platform.

## Change Note

Timestamp: 2026-04-03 11:46:43 +05:30

Changes made in this update:

- created this implementation tracker file
- captured the repo audit in a current-state format
- separated real, partial, simulated, and missing work
- documented immediate build order and execution phases
- recorded the update timestamp so future changes can be tracked against this state

## Next Intended Update Pattern

For each future implementation pass, append a new dated note here with:

- what changed
- what was verified
- what remains blocked
- which phase/package moved forward
