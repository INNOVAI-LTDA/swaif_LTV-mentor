# Story 4.2d: batch-b-spa-rewrite-and-env-separation (Batch B)

Status: review

## Story

As a release operator,
I want the Vercel-hosted Vite SPA to support deep links and hard refreshes on all published routes, and I want explicit, environment-scoped Preview vs Production examples for required `VITE_*` variables,
so that first hosted validation is reproducible and does not accidentally rely on localhost defaults or ambiguous operator knowledge.

## Background (Current State Snapshot)

- The router uses `createBrowserRouter(..., { basename: env.routerBasePath })` in `frontend/src/app/routes.tsx`.
- `env.routerBasePath` is derived from `VITE_APP_BASE_PATH` in `frontend/src/shared/config/env.ts`.
- `frontend/vercel.json` now includes the SPA rewrite needed for deep-link refresh on Vercel.
- `VITE_API_BASE_URL` is required for `VITE_DEPLOY_TARGET=client` and fallback-based only for `local` (`frontend/src/shared/config/envContract.ts`).
- There is no first-class `preview` deploy target; Preview/Production separation must be done via Vercel environment-scoped variables.

Source: `docs/mvp-mentoria/vercel-batch-b-current-state.md`.

## Requirements (Batch B)

1. Add SPA rewrite to `index.html` for Vercel.
2. Ensure deep links and refreshes work for:
   - `/`
   - `/login`
   - `/dashboard` (route alias; see notes below)
   - nested routes under the published app surface
3. Add `frontend/.env.production.example`.
4. Add `frontend/.env.preview.example`.
5. Ensure `VITE_API_BASE_URL` is explicit for hosted builds (no silent localhost dependency).
6. Ensure Preview and Production values are separable for:
   - `VITE_API_BASE_URL`
   - `VITE_CLIENT_CODE`
   - feature flags (only if applicable to hosted/client builds)

## Acceptance Criteria

1. Vercel deep-link refresh works (no host `404`) for:
   - `/`
   - `/login`
   - `/dashboard`
   - representative nested routes: `/app/admin`, `/app/matriz-renovacao`, `/app/aluno`
2. `frontend/.env.preview.example` exists and includes explicit `VITE_API_BASE_URL` and `VITE_CLIENT_CODE`.
3. `frontend/.env.production.example` exists and includes explicit `VITE_API_BASE_URL` and `VITE_CLIENT_CODE`.
4. No secrets are placed in `VITE_*` variables in the committed examples or docs.
5. Validation steps are documented (local + hosted).

## Tasks / Subtasks

### Task 1: Add Vercel SPA Rewrite (AC: 1)

- [x] Update `frontend/vercel.json` to add a rewrite so all non-file requests resolve to `/index.html`:
  - `rewrites: [{ "source": "/(.*)", "destination": "/index.html" }]`
- [x] Keep the change scoped to Batch B (do not add headers/CSP/HSTS here).
- [x] Ensure this is placed under `frontend/` since Vercel Root Directory is `frontend` (Batch A).

### Task 2: Ensure `/dashboard` Deep Link Works (AC: 1)

Notes:
- The current route tree does not include `/dashboard`. This story adds a minimal alias route that preserves existing behavior and avoids a route refactor.
- Recommended smallest behavior: `/dashboard` redirects to the existing authenticated entrypoint (currently `/app`), letting existing role-based logic take over.

- [x] Add a `path: "dashboard"` route in `frontend/src/app/routes.tsx` that redirects to `/app` (or to the existing role home redirect if already present).
- [x] Update or add a route smoke test in `frontend/src/test/routes.smoke.test.tsx` to cover the `/dashboard` alias (including under a configured basename).

### Task 3: Add Preview/Production Env Examples (AC: 2, 3, 4, 5)

- [x] Add `frontend/.env.preview.example` with explicit values or placeholders:
  - `VITE_DEPLOY_TARGET=client`
  - `VITE_APP_BASE_PATH=/`
  - `VITE_API_BASE_URL=https://api-preview.example.com` (placeholder)
  - `VITE_CLIENT_CODE=client_preview` (placeholder)
  - Branding fields (optional; keep minimal)
  - Ensure any feature flags included are safe and non-secret (and do not re-enable demo flows in client builds)
- [x] Add `frontend/.env.production.example` similarly, but with production placeholders:
  - `VITE_API_BASE_URL=https://api.example.com`
  - `VITE_CLIENT_CODE=client_prod`
- [x] Update `DEPLOY.md` to reference these example files and state the operator contract:
  - Vercel Preview uses the Preview-scoped values
  - Vercel Production uses the Production-scoped values
  - `VITE_API_BASE_URL` must be explicit in hosted environments

### Task 4: Validation Checklist (AC: 1, 5)

- [x] Document and perform local validation:
  - From `frontend/`: `npm run test -- routes.smoke.test.tsx`
- [x] Document hosted validation steps for BOTH Vercel Preview and Production:
  - Confirm environment-scoped vars are set (`VITE_DEPLOY_TARGET`, `VITE_APP_BASE_PATH`, `VITE_API_BASE_URL`, `VITE_CLIENT_CODE`)
  - Hard-refresh routes:
    - `/`
    - `/login`
    - `/dashboard`
    - `/app/admin`
    - `/app/matriz-renovacao`
    - `/app/aluno`
  - Confirm no requests target `127.0.0.1` or `localhost` in hosted browser network logs.

## Dev Notes / Guardrails

- Keep diffs narrow and deployment-focused.
- Do not introduce new fallback URLs in the client/hosted path.
  - Current behavior permits a localhost fallback only for `VITE_DEPLOY_TARGET=local`; do not expand fallback behavior.
- Do not place any secrets in `VITE_*` variables or example files.
- Keep routing centralized in `frontend/src/app/routes.tsx`.
- Avoid unrelated refactors or route reshaping; prefer an alias redirect for `/dashboard`.
- Do not change backend CORS here (Batch C).
- Do not add security headers/CSP/HSTS here (Batches E/F).

## Likely Files

- `frontend/vercel.json`
- `frontend/src/app/routes.tsx`
- `frontend/src/test/routes.smoke.test.tsx`
- `frontend/.env.preview.example`
- `frontend/.env.production.example`
- `DEPLOY.md`

## References

- `docs/mvp-mentoria/vercel-batch-b-current-state.md`
- `frontend/src/shared/config/envContract.ts`
- `frontend/src/shared/config/env.ts`
- `frontend/vite.config.ts`

## Dev Agent Record

### Agent Model Used

gpt-5.2

### Debug Log References

- `cd frontend; npm run test -- routes.smoke.test.tsx`

### Completion Notes List

- Added SPA rewrite to `frontend/vercel.json` for Vercel deep-link refresh.
- Added `/dashboard` alias redirecting to `/app` plus smoke coverage for default and basename scenarios.
- Added scoped env templates: `frontend/.env.preview.example` and `frontend/.env.production.example`.
- Updated `DEPLOY.md` to point operators to the Preview/Production env examples.
- Ran targeted test: `npm run test -- routes.smoke.test.tsx` (frontend).
- Hosted validation on Vercel Preview/Production remains pending and must be executed by the operator.

### File List

- `frontend/vercel.json`
- `frontend/src/app/routes.tsx`
- `frontend/src/test/routes.smoke.test.tsx`
- `frontend/.env.preview.example`
- `frontend/.env.production.example`
- `DEPLOY.md`
