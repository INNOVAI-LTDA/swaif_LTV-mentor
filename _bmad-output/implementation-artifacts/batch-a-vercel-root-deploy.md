# Story: Batch A - Vercel Root Deployment Baseline (Frontend)

Status: review
Owner: dmene
Date: 2026-03-26

## Problem Statement

We are preparing the existing Vite + React + TypeScript SPA for a first stable deployment on Vercel. The repository is a brownfield monorepo (`backend/`, `frontend/`, `scripts/`) and currently has **no Vercel configuration committed** and **no DEPLOY.md** documenting the exact Vercel project settings.

This creates deployment drift risk: Vercel settings can be configured in the UI but not versioned, and the app may implicitly assume subpath deployment (client templates/documentation reference `/accmed/`) even when the first Vercel deployment should be root-path (`/`).

## Goal (Batch A Only)

Establish the smallest, versioned baseline for Vercel that:

1. Treats `frontend/` as the Vercel project Root Directory (operator-configured).
2. Makes root-path deployment explicit (`VITE_APP_BASE_PATH=/` for the Vercel deployment posture).
3. Commits `frontend/vercel.json` so deploy behavior is versioned in Git.
4. Adds a root `DEPLOY.md` documenting the exact Vercel settings:
   - Root Directory = `frontend`
   - Framework Preset = `Vite`
   - Build Command = `npm run build`
   - Output Directory = `dist`

## Constraints / Guardrails (Binding)

- This repo is in final stabilization / final adjustment mode: smallest safe change, no opportunistic refactors.
- Preserve app behavior outside deployment scope.
- Do not introduce SPA rewrites, env splitting, CORS changes, security headers, CSP, HSTS, redirects, or cache policy in this story (those are later batches).

## Current State (Evidence)

- No `vercel.json` exists today at repo root or under `frontend/`.
- No `DEPLOY.md` exists at repo root or under `frontend/`.
- Frontend base path is env-driven and already supports `/`:
  - `normalizeBasePath()` returns `/` when configured as `/` or empty. (`frontend/src/shared/config/envContract.ts:14`)
  - Vite build `base` uses `normalizeBasePath(VITE_APP_BASE_PATH)`. (`frontend/vite.config.ts:18`)
  - `frontend/.env.example` already sets `VITE_APP_BASE_PATH=/` (root). (`frontend/.env.example:8`)

## Scope

### In Scope (Exact Changes)

1. Add `frontend/vercel.json` with explicit Vercel build output settings (minimal; no rewrites/headers/redirects yet).
2. Add repository-root `DEPLOY.md` that documents the exact Vercel project settings listed in the Goal section.
3. Ensure the documentation states that root-path deployment is the default for Vercel and that subpath deployment is not assumed.

### Out of Scope (Explicit)

- SPA deep-link rewrites / routing fixes (Batch B).
- Preview vs Production env separation (Batch B).
- `VITE_API_BASE_URL` hardening beyond existing contract (Batch B).
- Backend CORS alignment (Batch C).
- Custom domain + canonical www + redirects (Batch D).
- Security headers (Batch E) and CSP/HSTS (Batch F).
- Cache strategy review or Vercel CLI parity workflow (Batch G).
- Any refactors to routing, shells, adapters, services, or UI.

## Acceptance Criteria (Must Pass)

1. `frontend/` is the explicit deploy root:
   - `DEPLOY.md` states Vercel Root Directory must be `frontend`.
   - `frontend/vercel.json` exists (so config is colocated with the Root Directory).
2. Root-path deployment is explicit:
   - `DEPLOY.md` states `VITE_APP_BASE_PATH=/` for the Vercel deployment posture (root deployment).
   - `DEPLOY.md` states that subpath deployment is not assumed unless explicitly justified and configured.
3. `frontend/vercel.json` is committed and contains only the minimal baseline needed for Batch A (no SPA rewrites/redirects/headers yet).
4. `DEPLOY.md` documents the exact Vercel settings:
   - Framework Preset = Vite
   - Build Command = npm run build
   - Output Directory = dist

## Implementation Notes (Smallest Safe Patch)

- Place `vercel.json` under `frontend/` because Root Directory will be `frontend`.
- Keep `vercel.json` limited to build/output configuration to avoid mixing batches.
- `DEPLOY.md` is an operator-facing contract; keep it short and unambiguous, including:
  - the exact Vercel UI settings to apply
  - the required env var for root deploy posture: `VITE_APP_BASE_PATH=/`
  - a reminder that SPA rewrites are intentionally not part of Batch A (they belong to Batch B)

## Files / Modules Likely Affected

- Add: `frontend/vercel.json`
- Add: `DEPLOY.md`

## Tests / Validation (Nearest Relevant Layer)

No test changes are expected (config/docs only), but validate the build still works:

1. `cd frontend && npm run build`
2. (Optional but low-cost) `cd frontend && npm run test`

## Release / Deployment Risks If Not Implemented

- Vercel UI settings drift from repo state (unversioned deploy behavior).
- Operators follow stale subpath assumptions (e.g., `/accmed/`) when the first Vercel deployment should be root (`/`).
- Harder to coordinate subsequent batches (B-G) without a stable, committed deployment baseline.

## Dev Agent Record

### Debug Log
- 2026-03-26: `cd frontend && npm run build`

### Completion Notes
- Added `frontend/vercel.json` with minimal Vercel build/output settings scoped to Batch A (no rewrites/headers).
- Added root `DEPLOY.md` documenting Vercel Root Directory `frontend`, Framework Preset `Vite`, Build Command `npm run build`, Output Directory `dist`, and root-path posture `VITE_APP_BASE_PATH=/`.
- Documented that subpath deployment is not assumed for Batch A; future batches will cover rewrites and alternate base paths.

## File List
- `DEPLOY.md`
- `frontend/vercel.json`
- `_bmad-output/implementation-artifacts/batch-a-vercel-root-deploy.md`

## Change Log
- 2026-03-26: Batch A Vercel root deployment baseline implemented and documented.
