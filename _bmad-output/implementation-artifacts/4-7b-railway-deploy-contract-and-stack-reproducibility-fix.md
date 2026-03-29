# Story 4.7b: railway-deploy-contract-and-stack-reproducibility-fix

Status: review

## Story

As a release operator,
I want the Railway backend deploy contract to be explicit and reproducible,
so that the hosted backend uses the versioned repo settings instead of silent dashboard drift and boots with the same runtime stack the repo currently documents and tests against.

## Background (Why This Exists)

Story 4.7a made the backend Railway-deployable in principle, but adversarial review found three remaining contract gaps:

1. The runbook documents Railway service root `backend` and versioned config file `backend/railway.json`, but it does not explicitly tell the operator to configure Railway's config-file path as `/backend/railway.json` for this monorepo service.
2. The new runtime dependency manifest pins only:
   - `fastapi==0.135.1`
   - `pydantic==2.12.5`
   - `uvicorn==0.41.0`
3. In a clean install from that manifest, `pip` can resolve a newer `Starlette` than the repo's documented/tested backend stack.
4. The backend env template currently presents `CORS_ALLOW_ORIGIN_REGEX=^https://.*\.vercel\.app$` inside the main published example, which over-broadens the default production posture even though Preview support is meant to remain a separate optional posture.

This is a narrow deploy-contract follow-up, not a persistence, auth, or routing redesign.

## Deployment Decision Lock

- Keep Railway service root `backend`.
- Keep the FastAPI entrypoint unchanged: `app.main:app`.
- Keep Railway volume guidance unchanged:
  - mount path `/app/data`
  - `STORAGE_BACKUP_DIR=/app/data/backups`
- Keep backend behavior unchanged outside deploy-prep.
- Do not redesign persistence, auth, routing, or infrastructure.

## Review Findings To Resolve

### 1. Railway config-file path clarity

Because this is a monorepo-style deployment with service root `backend`, the operator contract must explicitly say that Railway must be configured to use:

- config-file path: `/backend/railway.json`

Without that, the versioned `backend/railway.json` may be ignored and dashboard deploy settings can silently diverge.

### 2. Runtime-stack reproducibility

The repo currently records the backend stack in `_bmad-output/project-context.md`, including:

- FastAPI `0.135.1`
- Starlette `0.52.1`
- Pydantic `2.12.5`
- Uvicorn `0.41.0`

The Railway runtime manifest should pin at least the directly relied-on runtime pieces needed to keep the deployed environment aligned with that tested stack.

Smallest required correction:

- add `starlette==0.52.1` to `backend/requirements.txt`

### 3. Production vs Preview CORS example clarity

`backend/.env.example` should not present Preview regex CORS as the default production example.

It should clearly separate:

- production-only example:
  - `CORS_ALLOW_ORIGINS=https://accmed.innovai-solutions.com.br`
  - no regex by default
- optional preview-enabled example:
  - same canonical production origin
  - plus `CORS_ALLOW_ORIGIN_REGEX=^https://.*\.vercel\.app$`

That keeps the production backend example aligned with least-privilege CORS while preserving the Vercel Preview option.

## Requirements

1. Update `docs/client-launch-runbook.md` so the Railway operator contract explicitly says:
   - if the Railway service root is `backend`
   - and the repo config file lives at `/backend/railway.json`
   - then the Railway service must be configured to use config-file path `/backend/railway.json`
2. Update `backend/requirements.txt` so the backend runtime stack is pinned to the repo's tested versions, at minimum:
   - `fastapi==0.135.1`
   - `pydantic==2.12.5`
   - `uvicorn==0.41.0`
   - `starlette==0.52.1`
3. Update `backend/.env.example` so it no longer presents Preview regex CORS as the default production example.
4. Keep the patch narrow and deploy-prep only.
5. Do not redesign persistence, auth, routing, or infrastructure.

## Acceptance Criteria

1. The Railway config-file path requirement is operationally clear for the monorepo backend service.
2. The backend dependency manifest is reproducible to the repo's documented/tested runtime stack.
3. Production and Preview CORS examples are clearly separated in `backend/.env.example`.
4. The deploy contract remains aligned to:
   - frontend origin `https://accmed.innovai-solutions.com.br`
   - backend API `https://api-accmed.innovai-solutions.com.br`
   - Railway volume mount `/app/data`
5. Diffs stay narrow and deploy-prep only.

## Implementation Notes (Keep Diffs Narrow)

- Do not move `backend/railway.json`; just make the operator contract explicit.
- Do not add Docker, process managers, or infrastructure redesign.
- Do not broaden `backend/requirements.txt` into a full dev/test lockfile; keep it runtime-focused.
- Keep `starlette==0.52.1` as the smallest reproducibility pin required by review.
- Keep `CORS_ALLOW_ORIGIN_REGEX` available in examples, but only in a clearly separated optional Preview-enabled example block.

## Files Likely Touched

- `docs/client-launch-runbook.md`
- `backend/requirements.txt`
- `backend/.env.example`

Potentially touched only if needed to keep the story artifact aligned:

- `_bmad-output/implementation-artifacts/4-7a-railway-backend-deploy-with-persistent-storage.md`

Reference files to inspect before editing:

- [client-launch-runbook.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md)
- [requirements.txt](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/requirements.txt)
- [.env.example](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/.env.example)
- [railway.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/railway.json)
- [project-context.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/project-context.md)

## Tasks / Subtasks

### Task 1: Make Railway Config-File Path Explicit (AC: 1, 4)

- [x] Update `docs/client-launch-runbook.md` so the Railway contract explicitly tells the operator to configure config-file path `/backend/railway.json`.
- [x] Keep the documented service root `backend`.
- [x] Keep the documented volume mount `/app/data`.

### Task 2: Pin Runtime Stack Reproducibly (AC: 2)

- [x] Update `backend/requirements.txt` to include `starlette==0.52.1`.
- [x] Keep the existing FastAPI, Pydantic, and Uvicorn pins unchanged unless validation proves another minimal adjustment is required.
- [x] Keep the manifest runtime-focused.

### Task 3: Separate Production And Preview CORS Examples (AC: 3, 4)

- [x] Update `backend/.env.example` so the main production example uses only the canonical frontend origin.
- [x] Add or preserve a separate optional Preview-enabled example using `CORS_ALLOW_ORIGIN_REGEX=^https://.*\.vercel\.app$`.
- [x] Keep `APP_AUTH_SECRET` and `/app/data/backups` guidance intact.

### Task 4: Validation (AC: 1, 2, 3)

- [x] Reinstall from `backend/requirements.txt` in a clean environment or otherwise prove the updated manifest resolves.
- [x] Re-run the backend startup smoke check with the production-like env contract.
- [x] Confirm the docs/examples remain aligned to the AccMed frontend/backend host contract.

## Suggested Validation Steps

1. Validate `backend/requirements.txt` by installing into a clean environment.
2. Validate `backend/railway.json` remains syntactically correct.
3. Start locally with:
   - `APP_ENV=production`
   - `CLIENT_CODE=accmed`
   - `CORS_ALLOW_ORIGINS=https://accmed.innovai-solutions.com.br`
   - `APP_AUTH_SECRET=<test-secret>`
   - `STORAGE_BACKUP_DIR=<temp-or-local-backup-dir>`
4. Confirm:
   - `GET /health` returns `200`
   - startup logs still show the expected runtime summary
5. Grep the updated docs/examples to confirm:
   - `/backend/railway.json` is mentioned explicitly in the Railway operator contract
   - `starlette==0.52.1` is pinned in the runtime manifest
   - production and preview CORS examples are separated

## Non-Goals / Guardrails

- Do not change `backend/app/main.py`.
- Do not redesign JSON persistence.
- Do not add a database.
- Do not redesign auth or token handling.
- Do not broaden this into Railway DNS, TLS, or domain cutover work.
- Do not perform unrelated cleanup in backend docs or deployment docs.

## Dev Agent Record

### Completion Notes

- Added the missing Railway operator note that monorepo backend services must point Railway at `/backend/railway.json` explicitly when the service root is `backend`.
- Pinned `starlette==0.52.1` in the runtime dependency manifest so clean installs stay aligned with the repo's documented/tested backend stack.
- Split the backend env template into production-only and optional Preview-enabled CORS examples so the default published posture no longer over-broadens production CORS.
- Revalidated the backend with a clean install, a production-like startup smoke, and a `/health` check returning `200`.

## File List

- `_bmad-output/implementation-artifacts/4-7b-railway-deploy-contract-and-stack-reproducibility-fix.md`
- `backend/requirements.txt`
- `backend/.env.example`
- `docs/client-launch-runbook.md`

## Change Log

- Created a narrow fix story for the Railway backend deployment-preparation batch review findings.
- Implemented the Railway deploy-contract and stack-reproducibility follow-up patch.
