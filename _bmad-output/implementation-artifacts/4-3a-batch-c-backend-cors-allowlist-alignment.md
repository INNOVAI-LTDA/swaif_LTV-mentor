# Story 4.3a: batch-c-backend-cors-allowlist-alignment (Batch C)

Status: ready-for-dev

## Story

As a release operator,
I want the backend CORS configuration to match the hosted frontend deployment reality (production custom domain plus optional preview origins) without relying on unsafe wildcard behavior,
so that browser requests succeed reliably while the backend remains locked to only the necessary origins.

## Background (Current State Snapshot)

- CORS is configured in `backend/app/main.py` via `fastapi.middleware.cors.CORSMiddleware`.
- Allowed origins come from `resolve_cors_origins()` in `backend/app/config/runtime.py`:
  - `APP_ENV` is required.
  - In production-like environments (anything not in `{local, development, dev, test}`), `CORS_ALLOW_ORIGINS` is required (fails fast if missing).
  - In local-like environments, missing `CORS_ALLOW_ORIGINS` falls back to `LOCAL_CORS_ORIGINS` (`:5173` and `:3000` only).
- Wildcard support is currently only `"*"`:
  - If `"*"` is present in the origins list, middleware switches to `allow_origins=["*"]` and forces `allow_credentials=False`.
  - There is no preview domain pattern support (no `*.vercel.app` matching).
- Auth is Bearer token based (no cookies), but future cookie-based flows would conflict with wildcard origins.

Source: `docs/mvp-mentoria/batch-c-backend-cors-current-state.md`.

## Requirements (Batch C)

1. Align backend CORS with deployment reality.
2. Allow only necessary origins:
   - Production hosted origin(s): `https://www.yourdomain.com` (and optionally `https://yourdomain.com` if both are used)
   - Preview origin pattern if needed (example: Vercel preview domains)
   - Localhost dev origins
3. Avoid wildcard CORS (`*`) in production-like environments.
4. Document the backend CORS allowlist contract (operator-facing).

## Acceptance Criteria

1. Backend can be started in production-like `APP_ENV` with explicit allowlisted origins and will reject missing/invalid CORS config.
2. Backend supports a preview-domain pattern configuration without requiring `CORS_ALLOW_ORIGINS=*`.
3. Wildcard `"*"` is rejected (or otherwise prevented) in production-like environments by default.
4. Local dev origin defaults include the ports actually used by the repo’s frontend validation flows (including `:4173` when applicable).
5. Operator docs clearly state:
   - which env vars to set
   - what formats are accepted
   - recommended values/examples for production vs preview vs local

## Tasks / Subtasks

### Task 1: Add Preview Origin Pattern Support (AC: 2)

- [ ] Add a new optional env var in `backend/app/config/runtime.py`: `CORS_ALLOW_ORIGIN_REGEX`.
- [ ] Validate `CORS_ALLOW_ORIGIN_REGEX` is either empty/unset or a compilable regex (fail fast with a clear error message if invalid).
- [ ] Wire it into `CORSMiddleware` in `backend/app/main.py` via `allow_origin_regex=<value>` when configured.

Notes:
- Keep `CORS_ALLOW_ORIGINS` as the primary explicit allowlist (production custom domain(s)).
- The regex is intended for preview hosts (example: Vercel per-PR URLs) where enumerating origins is impractical.

### Task 2: Prevent Unsafe Wildcard In Production-Like Envs (AC: 3)

- [ ] Update `resolve_cors_origins()` to reject `"*"` when `APP_ENV` is production-like, with a concrete runtime error message.
- [ ] Keep `"*"` behavior allowed only for local-like envs if already used for ad hoc local testing.

### Task 3: Expand Local Default Origins To Match Local Validation Ports (AC: 4)

- [ ] Update `LOCAL_CORS_ORIGINS` to include `http://localhost:4173` and `http://127.0.0.1:4173` (Vite preview default).
- [ ] Keep the existing `:5173` and `:3000` entries.

### Task 4: Update Docs For The Backend CORS Allowlist Contract (AC: 5)

- [ ] Update `docs/mvp-mentoria/batch-c-backend-cors-current-state.md` to include:
  - explicit operator examples for:
    - production custom domain
    - preview regex
    - local defaults
  - a warning that wildcard `*` is not accepted in production-like environments
- [ ] Ensure docs state that `CORS_ALLOW_ORIGINS` entries must be bare origins (no paths, query strings, fragments, or credentials).

### Task 5: Tests (AC: 1, 2, 3, 4)

- [ ] Add/update tests in `backend/tests/test_cors_config.py` to cover:
  - wildcard rejection in production-like env
  - local defaults include `:4173`
  - regex env var validation (invalid regex fails fast)
- [ ] Add/update a test (likely in `backend/tests/test_runtime_config.py`) that `create_app()` includes `allow_origin_regex` when configured.

## Non-Goals / Guardrails

- Do not refactor unrelated runtime config or add new environment split systems beyond what is needed for CORS.
- Do not change auth behavior (no cookie migration).
- Do not loosen CORS normalization rules (keep rejecting paths/query/credentials in origin entries).

## Validation Steps (Must Be Executed)

1. `cd backend`
2. `python -m pytest tests/test_cors_config.py`
3. `python -m pytest tests/test_runtime_config.py`
4. Manual smoke (optional but recommended):
   - Start backend with:
     - `APP_ENV=production CLIENT_CODE=<client> CORS_ALLOW_ORIGINS=https://www.yourdomain.com CORS_ALLOW_ORIGIN_REGEX=<preview-regex>`
   - Confirm browser preflight from allowed production origin succeeds.
   - Confirm browser preflight from a non-matching origin fails (no `access-control-allow-origin` for the request origin).

