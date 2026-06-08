# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`INNOVAI-LTDA/swaif_LTV-mentor` is the **DEVA — Acelerador Médico** platform: a decision-support system for medical-mentorship programs. It groups student evolution data into actionable views for mentors (Radar de Evolução, Matriz de Decisão, Centro de Comando) and exposes an Admin panel + Student workspace. The architecture is being evolved into a **Core + Skin + Client** multi-tenant platform (see `docs/architecture/platform_architecture_operational_model.md`); today's primary client is `accmed` (Acelerador Médico) hosted on Vercel + Railway.

This is a **brownfield** repo in final stabilization. Follow `AGENTS.md` and the project-context rules — do not redesign or refactor beyond the requested change.

## Common commands

### Local dev (single command, Windows + PowerShell)

```bash
./start-localhost.ps1                      # default: backend 8000, frontend 5173
./start-localhost.ps1 -BackendPort 8002 -FrontendPort 5175
# alias:
./start-local.bat
```

The script binds free ports, launches uvicorn + vite in background jobs, writes logs to `.logs/runtime/`, and runs a 1s SLA probe against the backend.

### Bootstrap a client env (frontend + backend `.env`)

```bash
scripts/mvp_bootstrap.bat --client-code accmed
py -3 scripts/mvp_bootstrap.py --client-code accmed
```

Reads `frontend/.env.client.<code>` (or `.example`) and `backend/.env.client.<code>` (or `.example`) and writes `.env` files.

### Backend (FastAPI)

```bash
cd backend
py -m pip install -r requirements.txt
APP_ENV=local CLIENT_CODE=local CORS_ALLOW_ORIGINS=http://127.0.0.1:5173 \
  py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend (Vite + React + TS)

```bash
cd frontend
npm install
VITE_DEPLOY_TARGET=local npm run dev          # dev server on 127.0.0.1:5173
VITE_DEPLOY_TARGET=local npm run build        # local build
npm run test                                  # vitest run (single shot)
npm run test:watch                            # vitest watch
npm run preview                               # vite preview on 127.0.0.1:4173
```

Client-safe build (production contract — fails fast if env invalid):

```bash
VITE_DEPLOY_TARGET=client \
VITE_CLIENT_CODE=accmed \
VITE_API_BASE_URL=https://api-accmed.innovai-solutions.com.br \
VITE_APP_BASE_PATH=/ \
  npm run build
```

### Tests

Backend (pytest, with `APP_ENV=local` and `CLIENT_CODE=test-client` set in `backend/tests/conftest.py`):

```bash
cd backend
py -m pytest -q
py -m pytest -q tests/api/test_admin_students_api.py         # single file
py -m pytest -q tests/unit/test_admin_pillar_service.py     # single file
py -m pytest -q -k "test_create_metric"                     # by node id
```

Frontend (vitest, jsdom, `VITE_DEPLOY_TARGET=local` stubbed in `src/test/setup.ts`):

```bash
cd frontend
npm run test
npx vitest run src/test/admin-api-panel.test.tsx            # single file
npx vitest run -t "auth provider"                            # by name
```

### Storage maintenance (legacy JSON stores, Supabase-mirror is the runtime source)

```bash
cd backend
py -m app.operations.storage_maintenance backup
py -m app.operations.storage_maintenance restore <snapshot_dir>
```

### BMAD operator loop

`Makefile` exposes `bmad-smoke`, `bmad-status`, `bmad-route`, `bmad-story`, `bmad-dev`, `bmad-review`, `bmad-fix`, `bmad-run`, `bmad-resume`, `bmad-lean`, and the full set of `bmad-*` workflow / phase commands driven by `ops/run_bmad_*.py`. See `docs/01_OPERATING_MODEL.md` and `docs/02_LOOP_MAP.md` for which loop to pick.

## Repository layout

```
backend/                  FastAPI app
  app/
    main.py               create_app(); wires routers, CORS, error handlers, startup sync
    config/runtime.py     APP_ENV, CLIENT_CODE, CORS, auth-secret, mentor-route policy
    api/
      errors.py           Standardized envelope: { error: { status, code, message, details } }
      routes/             Thin FastAPI routers; one module per admin domain + auth/mentor/provider/student/health
    schemas/              Pydantic models (request/response)
    services/             Business logic; services expose EntityNotFoundError/ValidationError/ConsistencyError
    storage/              Repositories. JSON store is disabled at runtime (JsonRepository.__init__ raises);
                          Supabase is the only runtime source for provider/admin flows
    operations/           storage_maintenance, supabase sync, canonical export
  data/                   JSON store files (legacy / fallback only) — do not edit at runtime
  tests/                  api/, unit/, e2e/, integration/ — conftest sets APP_ENV=local, CLIENT_CODE=test-client

frontend/                 Vite + React 18 + TS strict + react-router v6
  src/
    main.tsx, app/        Router + AuthProvider + AppLayout; routes.tsx is the single routing source
    pages/                Top-level /login, /404, /acesso-negado
    features/             One folder per UX view (admin, command-center, radar, matrix, student, mentor, …)
                          + admin sub-views (Provider/Client/Database/API) reachable via /mock/admin?panel=
    domain/               View-agnostic app core:
      models.ts           Canonical domain types
      services/           Per-view use-case services (commandCenterService, radarService, …)
      hooks/              useXxx + useAsyncResource (data fetching out of JSX)
      adapters/           raw API -> domain models
    shared/
      api/                httpClient + AppError + toUserErrorMessage
      auth/               tokenStorage, roleRouting, authEvents
      config/env.ts       Single env reader (do not read import.meta.env elsewhere)
      formatters/, ui/, contracts/  UI helpers, shared components, request/response DTOs
    test/                 vitest specs co-located in name (auth-service, routes.smoke, etc.)
  .env*                   env templates (.env.example, .env.client.accmed.example, .env.preview.example, .env.production.example)
  vercel.json             SPA rewrite + baseline security headers (X-Frame-Options, Permissions-Policy,
                          Content-Security-Policy-Report-Only). trailingSlash=false. Do not add HSTS or
                          enforce CSP here yet.

docs/                     Architecture, MVP-mentoria contracts, admin mockups, runbooks, trackers
ops/                      BMAD/Codex operator harness (run_bmad_*.py, prompts/, state/)
_bmad/                    BMAD method packs (bmm, cis, gds, wds, …) — see .agents/skills for the same catalog
.github/workflows/        bmad-plan-dispatch, bmad-story-dispatch, bmad-dev-review-dispatch
```

## Architecture essentials

### Backend layering

- **Routes** (`app/api/routes/*`) — thin. Receive HTTP, call a service, return schema. Use `api_error()` from `app/api.errors` to emit the standard envelope.
- **Services** (`app/services/*`) — own business rules. Raise domain errors (`EntityNotFoundError`, `ValidationError`, `ConsistencyError`, `DomainNotReadyError`, `RuntimeDependencyError`, `JsonFallbackForbiddenError`) — routes translate them to HTTP.
- **Repositories** (`app/storage/*`) — Supabase is the runtime source of truth. `JsonRepository` rejects construction (`RuntimeError`); the legacy `backend/data/*.json` files exist only for offline snapshot/import. New code should target the Supabase repositories under `app/storage/supabase_*.py`.
- **Schemas** — Pydantic v2 (`pydantic==2.12.5`). `enrollment`, `student`, `indicator_load`, `user` are the most-edited.
- **Runtime config** — `APP_ENV` must be set in all envs. `APP_AUTH_SECRET` is required for production-like envs. `CLIENT_CODE` must match the frontend `VITE_CLIENT_CODE` in the same deploy. CORS origins must be bare (no path/query/fragment). `ENABLE_MENTOR_ROUTES` is the runtime toggle; `ENABLE_MENTOR_DEMO_ROUTES` is a legacy alias.
- **Startup sync** — `main.py` can run `sync_runtime_stores_from_supabase(...)` on startup when `SUPABASE_SYNC_ON_STARTUP=true` and a valid `SUPABASE_DB_URL` is present.

### Frontend layering

The frontend follows the **Service → Adapter → Hook → Page** flow:

```
Page (features/<view>/pages)
  ↳ Hook (domain/hooks/useXxx + useAsyncResource)
    ↳ Service (domain/services/*Service)
      ↳ httpClient (shared/api)
        ↳ endpoints v1 backend
      ↳ Adapter (domain/adapters/*) raw -> domain
      ↳ Formatter (shared/formatters) for display
```

Rules (from `AGENTS.md`):

- `any` is forbidden unless the boundary is explicitly unknown and unavoidable.
- Raw API payloads are typed `unknown` at the boundary; normalize through adapters in `src/domain/adapters/`. Alias migration / contract translation belongs in adapters, not in React components.
- All `import.meta.env` access goes through `src/shared/config/env.ts`; do not read env directly in feature code.
- Data fetching lives in hooks, not in page JSX. Reuse `useAsyncResource` for loading/error/empty conventions.
- Routing stays centralized in `src/app/routes.tsx`. Use existing shells: `AdminShell`, `MentorShell`, `StudentShell`.
- Portuguese user-facing copy is preserved where the convention already exists.
- Reuse the `AppError` flow for network/HTTP failures (`shared/api/types.ts`).

### Frozen v1 contracts (do not break)

`docs/mvp-mentoria/contracts-freeze-v1.md` freezes the API contract as of 2026-03-09: don't remove/rename endpoints or change field types; new versions must bump the contract. Error envelope is universal:

```json
{ "error": { "status": 409, "code": "MENTORIA_CONFLICT", "message": "…", "details": null } }
```

Status hardening targets: `401` (auth), `404` (not found), `409` (conflict), `422` (validation). Functional contract docs:

- `docs/mvp-mentoria/contracts-command-center.md`
- `docs/mvp-mentoria/contracts-radar.md`
- `docs/mvp-mentoria/contracts-renewal-matrix.md`

Backend guard tests: `backend/tests/api/test_error_payload_api.py`, `backend/tests/e2e/test_smoke_mvp_flow.py`.

### Roles & authorization

Three published roles, mapped from legacy `mentor`/`student`:

- `admin` — full audit and management; routes are guarded by `RequireAdmin` in `routes.tsx` and by `require_admin_user` in admin routers.
- `provider` — owns a portfolio of clients; access to `/provider/*` mentor surface (Centro, Radar, Matriz) and admin-style dashboard.
- `client` (legacy `aluno`) — sees their own Radar + metrics in `/app/aluno`.

`/login` is the only public page. `RequireAuth` waits for `authReady`; `RequireAdmin` / `RequireMentorWorkspace` / `RequireStudentWorkspace` enforce role-based redirects to `/login` or `/app/acesso-negado`. Mentor legacy: `mentor-demo` routes still exist as a compatibility shim but the published mentor surface lives under `mentor` — do not re-introduce demo credentials, preview sessions, or localhost defaults on production paths.

### Admin panel structure (one route, four views)

`/app/admin` is gated by `RequireAdmin` and renders a single `AdminPage` that internally drives four sub-views (Cliente / Produto / Mentor / Pilar / Métrica / Aluno CRUD). The mock versions of the four provider/admin views live at `/mock/admin?panel=provider|clientes|database|api` and are documented under `docs/admin-mockups/`.

## Environment contract

Frontend `.env` (see `frontend/.env.example`):

- `VITE_DEPLOY_TARGET` — `local` or `client`. **Required for build.**
- `VITE_CLIENT_CODE` — required for `client` deploys; must match backend `CLIENT_CODE`.
- `VITE_API_BASE_URL` — absolute `http(s)` URL, no credentials/query/fragment. Required for `client`.
- `VITE_APP_BASE_PATH` — `/` for root; subpath allowed but not the current hosted contract.
- `VITE_CLIENT_NAME`, `VITE_APP_NAME`, `VITE_APP_TAGLINE`, `VITE_SHELL_SUBTITLE` — branding strings.
- `VITE_BRANDING_*_PATH`, `VITE_THEME_*` — branding assets and color tokens (default to the AccMed palette).
- `VITE_HTTP_TIMEOUT_MS` — defaults to 15000.
- `VITE_ENABLE_DEMO_MODE` / `VITE_ENABLE_INTERNAL_MENTOR_SURFACE` (alias `VITE_ENABLE_INTERNAL_MENTOR_DEMO`) — must be `false` in any client env. Demo login previews are local-only.

Backend `.env` (see `backend/.env.example`):

- `APP_ENV` — `local` / production-like.
- `CLIENT_CODE` — must match `VITE_CLIENT_CODE`.
- `CORS_ALLOW_ORIGINS` — bare origins, comma-separated; required in production-like envs.
- `CORS_ALLOW_ORIGIN_REGEX` — optional, for Vercel Preview subdomains.
- `APP_AUTH_SECRET` — required outside `local`/`development`/`dev`/`test`.
- `ENABLE_MENTOR_ROUTES` (alias `ENABLE_MENTOR_DEMO_ROUTES`) — defaults to enabled.
- `STORAGE_BACKUP_DIR` — used by `storage_maintenance backup`; on Railway, mount `/app/data` and point this at `/app/data/backups`.
- `SUPABASE_DB_URL` — required for `/admin/alunos/{id}/indicadores/carga-inicial` and all Supabase-backed flows.

The contract for hosted deploys is in `DEPLOY.md`; the operational release gate is `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`; the runbook is `docs/client-launch-runbook.md`; the live tracker is `docs/production-release-tracker.md`.

## Working rules (read before editing)

The `AGENTS.md` startup rule is mandatory: read in order `_bmad-output/project-context.md` (the 56-rule coordination artifact, listed first by `AGENTS.md`'s priority order), then `docs/architecture/platform_architecture_operational_model.md`, then the relevant MVP-mentoria contract, then the deployment-readiness checklist.

- **Smallest safe change.** Localize edits to the nearest module. No broad refactors. No parallel paths. No speculative improvements.
- **Test at the nearest layer.** Frontend tests in `frontend/src/test`. Backend tests under `backend/tests/{api,unit,e2e,integration}`. For API changes, preserve `tests/api/test_error_payload_api.py`. For service rules, update the service-layer test. For repository behavior, prefer tests that exercise the JSON-backed layer (and acknowledge that JSON is now a fallback).
- **Don't bypass adapters.** Never bind raw API payloads into React state. Never spread env access, token storage, or fetch details across feature code.
- **Don't put business rules in routes** or persistence logic in service callers.
- **Frozen contracts are stable.** Do not silently change them; if a breaking change is required, bump the contract version and update `contracts-freeze-v1.md` and the guard tests.
- **Demo / preview guard.** Don't reintroduce demo credentials, preview sessions, localhost defaults, or demo copy into production paths. `VITE_ENABLE_DEMO_MODE` and `VITE_ENABLE_INTERNAL_MENTOR_SURFACE` must remain `false` in client envs.
- **Security headers** (in `frontend/vercel.json`): keep `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`, `Permissions-Policy`, and `Content-Security-Policy-Report-Only` in place. CSP stays in report-only mode; do not promote to enforcing until the Preview smoke set is clean. HSTS remains off until stable custom-domain HTTPS is verified on the live host.
- **Response pattern for tasks:** restate the change, list likely files, describe the smallest safe patch, apply it, run the smallest relevant validation, then summarize what changed and any follow-ups.

## Pointers

- Project overview, mockup index, and admin preview route: `README.md`.
- Workspace rules and response pattern: `AGENTS.md`.
- Platform / multi-client architecture: `docs/architecture/platform_architecture_operational_model.md`.
- Frozen API contract and guard tests: `docs/mvp-mentoria/contracts-freeze-v1.md`.
- Frontend integration architecture: `docs/mvp-mentoria/frontend-integration-architecture.md`.
- Deployment / Vercel / Railway contract: `DEPLOY.md` and `frontend/vercel.json` / `backend/railway.json`.
- **Deploy contract source of truth.** `DEPLOY.md` is the single source of truth for the hosted Vercel + Railway contract: env vars (Vercel project + Railway service), security headers (`X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`, `Permissions-Policy`, `Content-Security-Policy-Report-Only`, no HSTS until the custom-domain HTTPS gate is signed off), `trailingSlash=false`, base path `/`, and the CSP/HSTS rollout policy. `frontend/vercel.json` and `backend/railway.json` must remain consistent with it.
- Release gate: `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`.
- Admin panel mockups and content: `docs/admin-mockups/admin-{provider,client,database,api}-view.md`.
- Operating model and loop selection: `docs/01_OPERATING_MODEL.md`, `docs/02_LOOP_MAP.md`, `docs/03_TROUBLESHOOTING.md`, `docs/04_TEST_MATRIX.md`.
- BMAD harness: `Makefile` + `ops/run_bmad_*.py` + `.agents/skills/bmad-*`.
