# Story 4.7a: railway-backend-deploy-with-persistent-storage

Status: review

## Story

As a release operator,
I want the current FastAPI backend to be deployable on Railway with persistent volume storage,
so that the deployed Vercel frontend can call a durable backend without forcing a database migration or backend redesign in this first hosted release.

## Background (Why This Exists)

The frontend is now deployed and points to a hosted backend URL, but the backend host is not live yet.

Current backend characteristics:

1. Runtime entrypoint already exists at [main.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/main.py).
2. The backend already exposes a simple health endpoint at [health.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/api/routes/health.py).
3. Runtime startup already enforces the critical deploy env contract in [runtime.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/config/runtime.py):
   - `APP_ENV` required
   - `CLIENT_CODE` required
   - `CORS_ALLOW_ORIGINS` required in production-like environments
   - optional `CORS_ALLOW_ORIGIN_REGEX` for Preview origins
4. Persistence is still JSON-file backed under [store_registry.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/storage/store_registry.py), which means the backend needs a persistent filesystem target.

Fast inspection outcome:

- Railway is a viable interim host for this backend because it supports a mounted persistent volume.
- This is not a zero-config deploy from the current repo state because `backend/` does not yet contain:
  - a versioned Python dependency manifest
  - a versioned Railway deploy/start contract
  - explicit operator guidance for the Railway volume/storage mapping and required production envs

## Deployment Decision Lock

- Treat `backend/` as the Railway service root directory.
- Keep the FastAPI entrypoint unchanged: `app.main:app`.
- Keep backend behavior unchanged outside deployment prep.
- Do not redesign persistence, auth, or business logic in this story.
- Do not move to a real database in this story.
- Use Railway volume storage for the existing JSON store model.

## Key Railway Compatibility Insight

Because the Railway service root should be `backend/`, the deployed app code will live under `/app`.

That means the existing default JSON store paths already align naturally with a Railway volume mounted at `/app/data`:

- default store root resolves to `/app/data`
- default JSON files resolve to `/app/data/*.json`

The smallest safe storage contract is therefore:

- Railway volume mount path: `/app/data`
- leave `USER_STORE_PATH`, `CLIENT_STORE_PATH`, and the other `*_STORE_PATH` variables unset unless a custom path override is explicitly needed
- set `STORAGE_BACKUP_DIR=/app/data/backups` so backups live on the same mounted volume

This keeps runtime code changes optional and likely unnecessary.

Source notes:

- Railway volumes are mounted to the path chosen by the operator, and the mount is available only at runtime, not build time.
- Railway healthchecks can target `/health`.
- Railway config-as-code can version build/deploy settings such as `startCommand` and `healthcheckPath`.

## Requirements

1. Add the minimum versioned backend deploy artifacts required for Railway:
   - Python dependency manifest for `backend/`
   - Railway-compatible start contract
   - versioned Railway config only if needed for reliability/clarity
2. Preserve the current FastAPI app entrypoint:
   - `backend/app/main.py`
3. Keep backend behavior unchanged outside deployment prep.
4. Make the persistent storage contract operationally clear for Railway volume usage.
5. Update operator-facing docs/examples for:
   - `APP_ENV=production`
   - `CLIENT_CODE=accmed`
   - `CORS_ALLOW_ORIGINS=https://accmed.innovai-solutions.com.br`
   - `CORS_ALLOW_ORIGIN_REGEX=^https://.*\\.vercel\\.app$`
   - `APP_AUTH_SECRET` required
   - Railway volume mount path and backup directory
   - health check at `/health`
6. Keep the story deploy-prep only:
   - no backend business-logic refactor
   - no database migration
   - no auth redesign

## Acceptance Criteria

1. `backend/` contains a versioned Python dependency manifest sufficient for Railway to build the service.
2. The backend start contract is explicit and Railway-compatible, including listening on the injected `PORT`.
3. The backend can be started on Railway from versioned repo artifacts without changing the FastAPI entrypoint.
4. The persistent storage contract is operationally clear:
   - Railway service root = `backend`
   - Railway volume mount path = `/app/data`
   - `STORAGE_BACKUP_DIR=/app/data/backups`
   - default JSON store paths are either preserved intentionally or explicitly overridden and documented
5. Operator-facing docs clearly describe the required production envs, health endpoint, and CORS contract for the hosted frontend.
6. Diffs stay narrow and do not introduce database work, auth redesign, or unrelated backend cleanup.

## Implementation Notes (Keep Diffs Narrow)

- Prefer a versioned `backend/railway.toml` or `backend/railway.json` only if it materially improves reproducibility by locking:
  - start command
  - healthcheck path
  - optional builder selection if needed
- Because Railway config-as-code overrides dashboard build/deploy settings per deployment, versioning the deploy posture is useful here.
- Keep the dependency manifest runtime-focused; do not expand scope into a full backend packaging overhaul.
- Prefer documenting the volume mapping over introducing runtime auto-detection unless implementation proves documentation alone is too fragile.
- If the current backend defaults already persist correctly with Railway mounted at `/app/data`, avoid unnecessary runtime-path refactors.
- `APP_AUTH_SECRET` must be treated as required in operator docs even though the current route code has a development fallback.

## Files Likely Touched

- `backend/requirements.txt` or `backend/pyproject.toml`
- `backend/railway.toml` or `backend/railway.json`
- `backend/.env.example`
- `docs/client-launch-runbook.md`

Potentially touched only if implementation needs them to keep the deploy contract clear:

- `docs/mvp-mentoria/batch-c-backend-cors-current-state.md`
- `DEPLOY.md`
- `backend/.env.client.accmed.example`

Reference files to inspect before editing:

- [main.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/main.py)
- [runtime.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/config/runtime.py)
- [health.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/api/routes/health.py)
- [auth.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/api/routes/auth.py)
- [store_registry.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/storage/store_registry.py)
- [json_repository.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/storage/json_repository.py)
- [client-launch-runbook.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md)

## Tasks / Subtasks

### Task 1: Add Minimum Railway Build And Start Artifacts (AC: 1, 2, 3)

- [x] Add a versioned Python dependency manifest under `backend/` suitable for Railway builds.
- [x] Add a versioned Railway deploy contract if needed, preferring `backend/railway.toml` or `backend/railway.json`.
- [x] Make the start command explicit and Railway-compatible:
  - use `python -m uvicorn app.main:app`
  - bind `--host 0.0.0.0`
  - bind `--port $PORT` (or equivalent shell-expanded Railway `PORT`)
- [x] Configure a Railway healthcheck path of `/health` if versioned config is used.
- [x] Keep the app entrypoint unchanged: `backend/app/main.py`.

### Task 2: Lock The Railway Persistent Storage Contract (AC: 4)

- [x] Document Railway service root as `backend`.
- [x] Document Railway volume mount path as `/app/data`.
- [x] Confirm the existing default JSON store paths are intentionally compatible with that mount path when the service root is `backend`.
- [x] Set or document `STORAGE_BACKUP_DIR=/app/data/backups`.
- [x] Only if implementation proves necessary, add the smallest explicit path-wiring needed for JSON store files or backups.
- [x] Do not redesign repository/storage logic.

### Task 3: Align Operator-Facing Backend Deploy Guidance (AC: 4, 5)

- [x] Update `backend/.env.example` so it includes a production-like Railway example for:
  - `APP_ENV=production`
  - `CLIENT_CODE=accmed`
  - `CORS_ALLOW_ORIGINS=https://accmed.innovai-solutions.com.br`
  - `CORS_ALLOW_ORIGIN_REGEX=^https://.*\\.vercel\\.app$`
  - `ENABLE_MENTOR_DEMO_ROUTES=false`
  - `ALLOW_REMOTE_MENTOR_DEMO_ROUTES=false`
  - `APP_AUTH_SECRET=<required-secret>`
  - `STORAGE_BACKUP_DIR=/app/data/backups`
- [x] Update operator-facing docs so the Railway deploy contract is explicit:
  - backend public host example
  - `/health` smoke check
  - volume mount path
  - start contract
  - Preview vs Production CORS posture
- [x] Keep docs aligned to the deployed frontend origin:
  - `https://accmed.innovai-solutions.com.br`

### Task 4: Validation (AC: 1, 2, 3, 4, 5)

- [x] Validate the Python dependency manifest by creating or using a clean environment and installing from it.
- [x] Validate the backend still starts locally with the production-like env contract.
- [x] Validate `GET /health` returns `200`.
- [x] Validate startup logs still surface:
  - `app_env`
  - `client_code`
  - `cors_origins`
  - `cors_origin_regex`
  - `storage_root`
  - `backup_dir`
- [x] If versioned Railway config is added, validate it is syntactically correct and consistent with the documented deploy contract.

## Suggested Validation Steps

1. From `backend/`, install runtime dependencies from the new manifest in a clean environment.
2. Start locally with production-like envs, for example:
   - `APP_ENV=production`
   - `CLIENT_CODE=accmed`
   - `CORS_ALLOW_ORIGINS=https://accmed.innovai-solutions.com.br`
   - `CORS_ALLOW_ORIGIN_REGEX=^https://.*\\.vercel\\.app$`
   - `ENABLE_MENTOR_DEMO_ROUTES=false`
   - `ALLOW_REMOTE_MENTOR_DEMO_ROUTES=false`
   - `APP_AUTH_SECRET=<test-secret>`
   - `STORAGE_BACKUP_DIR=<temp-or-local-backup-dir>`
3. Run:
   - `python -m uvicorn app.main:app --host 127.0.0.1 --port 8001`
4. Verify:
   - `GET http://127.0.0.1:8001/health` returns `200`
   - startup logs show the expected runtime summary
5. If a Railway config file is added, confirm it matches the intended service root and start contract.

## Non-Goals / Guardrails

- Do not move the backend to a database.
- Do not redesign auth, token shape, or route contracts.
- Do not change service/business logic unrelated to deployment.
- Do not introduce Docker unless implementation proves Railway Railpack cannot support the backend cleanly with a narrow config.
- Do not broaden this into full backend observability, worker processes, or CI/CD work.

## Dev Agent Record

### Completion Notes

- Added a runtime-focused `backend/requirements.txt` for Railway builds and a versioned `backend/railway.json` that locks the start command, healthcheck path, and restart posture without changing the FastAPI entrypoint.
- Kept storage behavior unchanged in code and documented the smallest safe Railway volume contract instead: service root `backend`, volume mount `/app/data`, and `STORAGE_BACKUP_DIR=/app/data/backups`.
- Updated backend/operator examples so production-like startup now includes the required `CLIENT_CODE`, `APP_AUTH_SECRET`, hosted CORS values, and the `/health` smoke requirement.

## File List

- `backend/requirements.txt`
- `backend/railway.json`
- `backend/.env.example`
- `docs/client-launch-runbook.md`
- `_bmad-output/implementation-artifacts/4-7a-railway-backend-deploy-with-persistent-storage.md`

## Change Log

- Created a narrow Railway backend deployment-preparation story focused on build/start artifacts, persistent volume mapping, and operator deploy guidance.
- Implemented the Railway backend deployment-preparation batch with versioned build/start artifacts and operator-facing volume/env guidance.
