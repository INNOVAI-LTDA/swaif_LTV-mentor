# Story 4.2a: vercel-root-project-setup (Batch A)

Status: ready-for-dev

## Story

As a release operator,
I want the frontend SPA deployed from `frontend/` as the Vercel project root with an explicit root-path base (`VITE_APP_BASE_PATH=/`) and versioned deploy configuration,
so that the first stable Vercel deployment is reproducible and does not accidentally inherit the current subpath-oriented local baseline.

## Acceptance Criteria

1. `frontend/` is the explicit Vercel Root Directory (documented as an operator setting and treated as the deployable unit of the repo).
2. Root-path deployment is explicit via `VITE_APP_BASE_PATH=/` (documented as an operator setting).
3. `frontend/vercel.json` exists and is committed to Git to version the intended Vercel build/output behavior.
4. `DEPLOY.md` documents the exact Vercel settings:
   - Root Directory = `frontend`
   - Framework Preset = `Vite`
   - Build Command = `npm run build`
   - Output Directory = `dist`
5. No subpath deployment is assumed for the Vercel deployment unless explicitly justified in `DEPLOY.md`.

## Tasks / Subtasks

- [ ] Task 1 (AC: 3)
  - [ ] Add `frontend/vercel.json` with the minimal project-level build configuration to be versioned in Git.
  - [ ] Keep `vercel.json` scoped to Batch A only:
    - Do not add SPA rewrite rules here (handled in Batch B).
    - Do not add security headers here (handled in later batches).
    - Do not change app runtime behavior.
- [ ] Task 2 (AC: 1, 2, 4, 5)
  - [ ] Add repo-root `DEPLOY.md` documenting the exact Vercel configuration for Batch A (root directory, framework preset, build/output dirs).
  - [ ] In `DEPLOY.md`, document the required environment variables for a Vercel build to succeed in this repo, including:
    - `VITE_DEPLOY_TARGET=client` (required by frontend env contract)
    - `VITE_APP_BASE_PATH=/` (Batch A requirement)
    - placeholders for `VITE_API_BASE_URL` and `VITE_CLIENT_CODE` (required by the frontend build contract; detailed separation/values are handled in Batch B)
  - [ ] In `DEPLOY.md`, explicitly call out that existing docs reference `/accmed/` and `/cliente/` as local baseline/examples and must not be copied into the Vercel root deployment unintentionally.
- [ ] Task 3 (AC: 2, 3)
  - [ ] Validate locally from `frontend/` that the root-path base is respected and tests still pass:
    - `npm run test`
    - `VITE_DEPLOY_TARGET=local VITE_APP_BASE_PATH=/ npm run build`
  - [ ] Validate the client-safe build contract does not break when `VITE_APP_BASE_PATH=/` is used (use placeholder values if needed):
    - `VITE_DEPLOY_TARGET=client VITE_CLIENT_CODE=accmed VITE_API_BASE_URL=https://api.example.com VITE_APP_BASE_PATH=/ npm run build`

## Dev Notes

### Scope guardrails (do not expand)

- This story is **Batch A only** (project-root directory + base path + versioned config + deploy doc).
- Do not fix deep-link SPA refresh behavior or rewrites here (Batch B).
- Do not split Preview vs Production envs here (Batch B).
- Do not change backend CORS here (Batch C).
- Do not add security headers/CSP/HSTS here (Batches E/F).

### Why this story exists

The repo is structured as a monorepo with `frontend/` and `backend/`. The repo root has no `package.json`, so Vercel must be configured to treat `frontend/` as the project root. Separately, the current operator baseline in docs validates under a subpath (`/accmed/`), but Batch A explicitly targets root-path deployment (`/`) and must be written down to avoid accidental subpath carryover.

### Relevant Files

- `frontend/vite.config.ts` (Vite `base` derives from `VITE_APP_BASE_PATH`)
- `frontend/src/shared/config/envContract.ts` (base-path normalization + required env contract)
- `frontend/src/shared/config/env.ts` (router/public asset base path behavior)
- `frontend/src/app/routes.tsx` (router basename uses `env.routerBasePath`)
- `frontend/README.md` (current env contract and subpath notes)
- `docs/mvp-mentoria/vercel-batch-a-current-state.md` (Batch A state snapshot)
- `docs/client-launch-runbook.md` (subpath-oriented baseline and examples)
- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` (routing/hosting readiness gates)

### Testing standards summary

- Frontend build contract is `tsc --noEmit && vite build` (see `frontend/package.json`).
- Keep TypeScript strict constraints intact; avoid unrelated refactors.
- Prefer validating base-path behavior via existing env tests (`frontend/src/shared/config/env.test.ts`) plus route smoke tests (`frontend/src/test/routes.smoke.test.tsx`).

### References

- [Source: docs/mvp-mentoria/vercel-batch-a-current-state.md]
- [Source: frontend/vite.config.ts]
- [Source: frontend/src/shared/config/envContract.ts]
- [Source: frontend/src/shared/config/env.ts]
- [Source: frontend/src/app/routes.tsx]
- [Source: frontend/README.md]
- [Source: docs/client-launch-runbook.md]
- [Source: docs/mvp-mentoria/frontend-deployment-readiness-checklist.md]

## Dev Agent Record

### Agent Model Used

gpt-5.2

### Debug Log References

TBD (populate during implementation)

### Completion Notes List

TBD (populate during implementation)

### File List

TBD (populate during implementation)

