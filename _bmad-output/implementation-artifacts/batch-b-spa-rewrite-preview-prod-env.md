# Story: Batch B - SPA Rewrite + Preview/Production Env Examples (Frontend)

Status: review
Owner: dmene
Date: 2026-03-26

## Problem Statement

The frontend is a Vite SPA hosted as static assets. Without an explicit host rewrite rule, deep links and browser refreshes on nested routes (for example `/login` or `/app/radar`) can return a host 404 instead of the SPA shell (`index.html`).

In addition, the current environment posture still allows a local fallback API URL in code (`http://127.0.0.1:8000`) when `VITE_API_BASE_URL` is absent, which is a deployment hardening risk: production/preview builds should never rely on implicit fallback URLs.

Batch B hardens SPA hosting behavior and environment contracts without changing unrelated UI/layout behavior.

## Goal (Batch B Only)

1. Add a Vercel SPA rewrite so all non-file routes resolve to `index.html`.
2. Ensure deep links and refreshes work for:
   - `/`
   - `/login`
   - “dashboard” entrypoint (see notes below)
   - nested routes under `/app/*`
3. Introduce explicit example env files for Vercel Preview and Production:
   - `frontend/.env.preview.example`
   - `frontend/.env.production.example`
4. Make `VITE_API_BASE_URL` explicit (no fallback URLs in code).
5. Keep Preview vs Production values explicitly separated in examples for:
   - `VITE_API_BASE_URL`
   - `VITE_CLIENT_CODE`
   - feature flags, if applicable
6. Document the validation steps for this batch (operator-facing).

## Constraints / Guardrails (Binding)

- Keep diffs narrow; no opportunistic refactors.
- Do not change routing structure beyond what is necessary for deep-link behavior and/or a minimal `/dashboard` alias if required.
- Do not introduce secrets via `VITE_*` variables.
- Do not mix in backend CORS (Batch C), domains/redirects (Batch D), headers/CSP/HSTS (Batches E/F), cache strategy / Vercel CLI parity (Batch G).

## Current State (Evidence)

- There is no `vercel.json` today (Batch A story introduces it); therefore no SPA rewrites exist yet.
- Frontend routes are defined under `frontend/src/app/routes.tsx`:
  - Public: `/` (redirect to `/login`), `/login`
  - Authenticated: `/app/*` including mentor/admin/student shells
  - There is no `/dashboard` route today.
- API base URL contract currently allows a local fallback when `VITE_DEPLOY_TARGET=local` and `VITE_API_BASE_URL` is empty (`frontend/src/shared/config/envContract.ts:22`).

## Scope

### In Scope (Exact Changes)

1. Update `frontend/vercel.json` (created in Batch A) to add an SPA rewrite:
   - Static assets must keep working (do not rewrite `/assets/*`, `/branding/*`, etc.).
   - Prefer the minimal Vercel pattern that preserves filesystem handling then rewrites everything else to `/index.html`.
2. (Minimal routing support) Ensure the “dashboard entrypoint” deep-link/refresh requirement is met:
   - Preferred: treat `/app` as the dashboard entrypoint (role-based redirect already happens at `/app`).
   - If an explicit `/dashboard` path is required for operator checks, add a minimal alias route to redirect `/dashboard` -> `/app` without changing shells or auth behavior.
3. Add env example files:
   - `frontend/.env.preview.example`
   - `frontend/.env.production.example`
   Both must include explicit `VITE_API_BASE_URL` and `VITE_CLIENT_CODE` placeholders and keep feature flags explicit.
4. Remove fallback URLs in code by tightening the env contract:
   - `normalizeApiBaseUrl()` should not silently default to `http://127.0.0.1:8000` when `VITE_API_BASE_URL` is missing.
   - Local development remains supported by `.env` / `.env.example` providing an explicit local URL.
5. Document Batch B validation steps in an operator-facing place:
   - Prefer appending a short “Batch B validation” section to root `DEPLOY.md` added in Batch A (keep docs consolidated).

### Out of Scope (Explicit)

- Any API endpoint changes or backend CORS configuration.
- Auth behavior changes (login/logout/role gating) beyond any minimal `/dashboard` alias redirect.
- Preview vs Production “mode” build command changes (no change to `npm run build` in Batch A posture).
- Adding security headers, CSP, HSTS, redirects, or cache headers.

## Acceptance Criteria (Must Pass)

1. Deep links and refreshes work (host-level):
   - Refreshing `/`, `/login`, `/app`, and at least two nested routes under `/app/*` returns the SPA shell and loads normally.
   - If `/dashboard` is supported, refreshing `/dashboard` behaves deterministically (redirects to `/app`).
2. Env examples exist:
   - `frontend/.env.preview.example` is committed.
   - `frontend/.env.production.example` is committed.
3. `VITE_API_BASE_URL` is explicit:
   - Build/runtime no longer depends on a hardcoded fallback URL in code when the env var is missing.
4. No secrets are placed in `VITE_*` variables:
   - Example env files contain only public runtime configuration values (no passwords, tokens, or private keys).
5. Validation steps are documented:
   - `DEPLOY.md` includes a short checklist for verifying SPA rewrite + deep refresh behavior and env configuration.

## Implementation Notes (Smallest Safe Patch)

- Vercel rewrite:
  - Use the minimal config that preserves static files (assets/branding) and rewrites all other paths to `/index.html`.
  - Keep config changes scoped to SPA rewrite only (do not add redirects/headers yet).
- Env examples:
  - Preview example should use preview-style placeholders, e.g. `VITE_API_BASE_URL=https://api-preview.example.com` and a preview-safe `VITE_CLIENT_CODE` placeholder.
  - Production example should use production placeholders, e.g. `VITE_API_BASE_URL=https://api.example.com`.
  - Keep `VITE_ENABLE_DEMO_MODE=false` and `VITE_ENABLE_INTERNAL_MENTOR_DEMO=false` explicit in both.
- Fallback removal:
  - Update `frontend/src/shared/config/envContract.ts` to require `VITE_API_BASE_URL` whenever `env.apiBaseUrl` is built, regardless of deploy target.
  - Update any existing unit tests that assert the fallback behavior (nearest layer: `frontend/src/shared/config/env.test.ts`).

## Files / Modules Likely Affected

- Update: `frontend/vercel.json`
- Add: `frontend/.env.preview.example`
- Add: `frontend/.env.production.example`
- Update: `frontend/src/shared/config/envContract.ts`
- Update: `frontend/src/shared/config/env.test.ts`
- Update (optional): `frontend/src/app/routes.tsx` (only if adding `/dashboard` alias)
- Update: `DEPLOY.md` (append Batch B validation steps)

## Tests / Validation

### Automated (nearest relevant layer)

- `cd frontend && npm run test`
  - Ensure updated env-contract tests cover “missing VITE_API_BASE_URL fails” rather than fallback.

### Build

- `cd frontend && npm run build`
  - Confirm build still succeeds with explicit `VITE_API_BASE_URL` set via `.env` (local) or env vars (CI/Vercel).

### Manual (host behavior)

On the deployed Vercel Preview/Production URLs (or equivalent host):

1. Open `/` and confirm it redirects to `/login` and renders.
2. Refresh `/login` and confirm no 404.
3. Open `/app`, confirm the role-based landing works after auth.
4. Refresh a protected nested route (example: `/app/radar` and `/app/matriz-renovacao`) and confirm the SPA shell loads and routing + guards behave as expected.
5. Confirm no network request targets `127.0.0.1` / `localhost` in Preview/Production.

## Release Risks If Not Implemented

- Nested-route refresh breaks on Vercel (host 404s) even if in-app navigation works.
- Preview/Production deployments risk pointing at localhost due to implicit fallback behavior.
- Operator confusion due to lack of explicit Preview vs Production env examples and validation checklist.

## Dev Agent Record

### Debug Log
- 2026-03-26: `cd frontend; npm run test`
- 2026-03-26: `cd frontend; npm run build`

### Completion Notes
- Added SPA rewrite in `frontend/vercel.json` so Vercel deep links refresh to `index.html` while keeping static assets intact.
- Introduced preview and production env templates with explicit `VITE_API_BASE_URL` / `VITE_CLIENT_CODE` and disabled demo flags.
- Tightened env contract to require `VITE_API_BASE_URL` for all deploy targets and updated tests accordingly.
- Added `/dashboard` redirect to `/app` to satisfy dashboard entrypoint refresh expectation.
- Documented Batch B validation steps in `DEPLOY.md` for operators.

## File List
- `frontend/vercel.json`
- `frontend/.env.preview.example`
- `frontend/.env.production.example`
- `frontend/src/shared/config/envContract.ts`
- `frontend/src/shared/config/env.test.ts`
- `frontend/src/test/mentor-shell-actions.test.tsx`
- `frontend/src/app/routes.tsx`
- `DEPLOY.md`
- `_bmad-output/implementation-artifacts/batch-b-spa-rewrite-preview-prod-env.md`

## Change Log
- 2026-03-26: Batch B SPA rewrite + preview/production env posture implemented and documented.
