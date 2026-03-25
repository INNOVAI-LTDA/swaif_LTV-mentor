# Current State: client_code Runtime Parameterization (Frontend + Backend)

Date: 2026-03-25
Scope: ADJ-016 (env-config/authless-runtime)

This document is intentionally narrow: it captures only the current state relevant to hardening a single `client_code` contract so frontend and backend resolve the same active client.

## Binding Constraints (project-context.md)

- Frontend must keep environment access centralized in `frontend/src/shared/config/env.ts`.
- Feature code must not read `import.meta.env` directly.
- Backend runtime/config lives under `backend/app/config` and services/storage boundaries.
- Avoid demo/default/localhost fallbacks in production-oriented paths.

Note: there is no `project-context.md` at repo root; the binding file currently lives at `_bmad-output/project-context.md`.

## Frontend: Env Ingress and Usage

### Single ingress point

- Environment values are read only in `frontend/src/shared/config/env.ts`.
- `frontend/src/shared/config/env.ts` reads `import.meta.env` and exports a normalized `env` object.

### Contract/normalization

- `frontend/src/shared/config/envContract.ts` enforces:
  - `VITE_DEPLOY_TARGET` must be `local` or `client` (required).
  - `VITE_API_BASE_URL`:
    - allowed to default to `http://127.0.0.1:8000` only when deploy target is `local`
    - required (non-empty) for deploy target `client`
    - must be absolute http(s) URL without credentials/query/hash
  - `VITE_APP_BASE_PATH` normalized to `/` or `/<subpath>/` with trailing slash.
- `frontend/vite.config.ts` uses `loadEnv()` and the same normalizers to validate early:
  - it will fail to start dev server if `VITE_DEPLOY_TARGET` is missing/invalid
  - in `build` + `deployTarget=client`, it validates `VITE_API_BASE_URL`

### Branding/showable client data selection

`frontend/src/shared/config/env.ts` selects client-facing identity purely from `VITE_*` variables (build/dev-server env):

- `VITE_CLIENT_NAME`, `VITE_APP_NAME`, `VITE_APP_TAGLINE`, `VITE_SHELL_SUBTITLE`
- Branding assets:
  - `VITE_BRANDING_ICON_PATH`, `VITE_BRANDING_LOGO_PATH`, `VITE_BRANDING_LOGIN_HERO_PATH`
  - resolved via `buildPublicAssetUrl()` using the normalized base path
- Theme tokens: `VITE_THEME_*`

There is no first-class `VITE_CLIENT_CODE` in the current frontend env contract or `env` export.

### import.meta.env usage outside shared config

- Current scan shows `import.meta.env` usage only in `frontend/src/shared/config/env.ts`.
  - This matches the project-context constraint (no `import.meta.env` usage in feature code).

## Frontend: Client-Specific Env Files and Bootstrap Behavior

### Client-specific env templates exist

- `frontend/.env.example` (generic template)
- `frontend/.env.client.accmed.example` (client-specific template)

`frontend/.env.client.accmed.example` is labeled as `client` deploy target but uses a local API URL (`http://127.0.0.1:8000`) as part of the local baseline; operators must replace this for real hosted environments.

### Bootstrap selects env by client_code

- `scripts/mvp_bootstrap.py` supports `--client-code <code>` (also defaulting from `CLIENT_CODE` env var).
- For frontend and backend, it resolves:
  - `.env.client.<client_code>` or `.env.client.<client_code>.example`
- It parses the chosen env file and injects the key/value pairs into the process environment for the spawned service.
- It also sets `CLIENT_CODE=<client_code>` into both environments (unless already present) when `--client-code` is used.

Important: Vite only exposes `VITE_*` variables to `import.meta.env` at runtime; `CLIENT_CODE` is not currently used by frontend code and is not part of the exported `env` object.

## Backend: Runtime/Config Loading Path

### What the backend reads today

- `backend/app/config/runtime.py` reads configuration strictly from OS environment:
  - `APP_ENV` is required and drives "production-like" behavior.
  - `CORS_ALLOW_ORIGINS` is required when `APP_ENV` is production-like; local defaults exist only for `APP_ENV` in `{local,development,dev,test}`.
  - Mentor demo routes are governed by `ENABLE_MENTOR_DEMO_ROUTES` and the remote approval gate `ALLOW_REMOTE_MENTOR_DEMO_ROUTES`.
- `backend/app/main.py`:
  - constructs an `app.state.runtime_summary` used for startup logging (app_env, cors origins, mentor demo policy, storage root, backup dir).
  - does not currently read or log any `CLIENT_CODE`/client identity.

### Storage selection is per-store env vars, not client_code

- `backend/app/storage/store_registry.py` selects JSON store paths via env vars like:
  - `USER_STORE_PATH`, `CLIENT_STORE_PATH`, `STUDENT_STORE_PATH`, etc.
  - defaults to `backend/app/data/<file>.json` when those env vars are absent.
- `backend/app/storage/catalog.py` derives `storage_root` from the common parent of the configured store paths.

There is no current backend behavior that uses `CLIENT_CODE` to:

- pick a storage root
- pick store paths
- pick client identity
- validate that the backend is running for the same "active client" as the frontend

### Backend client-specific env template exists but is currently informational

- `backend/.env.client.accmed.example` contains `CLIENT_CODE`, `CLIENT_NAME`, and `CLIENT_PRODUCT_NAME`.
- A scan of `backend/app` shows no current reads of those variables.

## Current client_code Propagation Map

Source of truth today is operational, not a runtime contract:

- Operator picks `client_code`:
  - via `scripts/mvp_bootstrap.bat --client-code accmed` (recommended local bootstrap)
  - or via manual selection of frontend/backend env vars when starting services
- Bootstrap uses `client_code` only to choose which `.env.client.<code>*` file to load for each service.
- Frontend runtime client identity is driven by `VITE_*` values injected by that env file.
- Backend runtime has no client identity concept today; it only enforces runtime posture (`APP_ENV`, CORS, mentor-demo policy, storage path configuration).

## Mismatch Risks (Frontend vs Backend)

These are the concrete mismatch failure modes for the proposed adjustment:

1. Frontend "client" is effectively `VITE_*` branding + base path, while backend has no comparable "active client" setting.
2. `CLIENT_CODE` is injected into both processes by bootstrap, but:
   - frontend does not export/consume it (not `VITE_CLIENT_CODE`)
   - backend does not consume it at all
3. Operator can start frontend with one client env file and backend with another (or generic defaults) without an explicit runtime check to catch it.
4. Local baseline templates include localhost URLs even under `VITE_DEPLOY_TARGET=client`; if an operator reuses them unchanged in hosted environments, "no localhost traffic" can be violated even though the code paths are behaving as configured.

## Demo/Default/Localhost Fallbacks in Production-Oriented Paths

Frontend:

- `normalizeApiBaseUrl("", "local")` intentionally falls back to `http://127.0.0.1:8000` for local development.
- For `deployTarget="client"`, missing `VITE_API_BASE_URL` throws, but it does not prevent configuring a localhost URL; avoiding localhost in hosted environments remains an operator responsibility today.

Backend:

- For production-like `APP_ENV`, `CORS_ALLOW_ORIGINS` is required (no silent localhost fallback).
- Mentor demo routes default enabled only for local/test; enabling in production-like environments requires explicit remote approval.
- `backend/app/services/mentor_demo_service.py` contains a hardcoded demo client name (`DEMO_CLIENT_NAME = "Grupo Acelerador Medico"`), but the route itself is controlled by the mentor-demo policy gates.

## Nearest Tests Likely to Need Updates for ADJ-016

Frontend:

- `frontend/src/shared/config/env.test.ts` (validates deploy target/base path/API URL rules; will likely need new cases if `VITE_CLIENT_CODE` is introduced/required).
- `frontend/src/test/*` files that mock `../shared/config/env` may need updates if the exported `env` shape changes (e.g., adding a required `clientCode` field).

Backend:

- `backend/tests/test_runtime_config.py` and `backend/tests/test_cors_config.py` cover runtime policy gating; they are the closest place to add tests if backend starts requiring/validating `CLIENT_CODE` for production-like environments, or if it begins logging/exposing client identity in `runtime_summary`.

Bootstrap tooling (currently no direct tests found):

- `scripts/mvp_bootstrap.py` is the current enforcement point for loading `.env.client.<code>*` files and injecting env vars consistently. If ADJ-016 changes the contract (e.g., requiring a variable or adding validation), this script is the nearest place to add a focused test (if/when script tests exist) or at least to harden runtime error messages.

## Exact Files/Modules Likely to Be Affected by ADJ-016

Frontend:

- `frontend/src/shared/config/env.ts` (introduce/export `clientCode` if it becomes a runtime contract, and keep all `import.meta.env` access centralized here)
- `frontend/src/shared/config/envContract.ts` (normalize/validate client_code if required)
- `frontend/vite.config.ts` (optional: validate presence/shape of client_code at build/dev start)
- `frontend/.env.client.*.example` templates (ensure the contract variables exist)
- `frontend/src/shared/config/env.test.ts` (contract tests)

Backend:

- `backend/app/config/runtime.py` (add any `CLIENT_CODE` parsing/validation rules if the backend becomes client-aware)
- `backend/app/main.py` (include active client details in `runtime_summary` logs if required for operator evidence)
- Potentially: `backend/app/storage/store_registry.py` (only if client_code becomes part of deterministic storage root selection; currently selection is via per-store env vars)
- `backend/tests/test_runtime_config.py` (new unit tests for client_code rules)

Bootstrap:

- `scripts/mvp_bootstrap.py` (validation to ensure frontend/backend receive a consistent client_code contract and/or consistent env shapes)

