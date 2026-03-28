# Batch A (Vercel) - Current State Snapshot (Targeted)

Date: 2026-03-27
Scope: Document only the current repo state relevant to Batch A:

- lock `frontend/` as the Vercel project root
- set `VITE_APP_BASE_PATH=/`
- add `frontend/vercel.json`

This is intentionally narrow and does not attempt to document the full project.

## 1) Is `frontend/` already the real deployable root?

Yes, by structure:

- Repo root does not contain a `package.json`.
- `frontend/package.json` exists and contains the Vite/React build pipeline:
  - `build`: `tsc --noEmit && vite build`
  - `test`: `vitest run`
- A Vercel project configured at repo root would still need `frontend/` set as Root Directory to find the frontend build entrypoint.

Implication for Batch A:

- `frontend/` is the real deployable unit and that contract is already the intended hosted posture.

## 2) Current Vite base-path behavior

### Build-time base (`vite.config.ts`)

`frontend/vite.config.ts` resolves:

- `env = loadEnv(mode, process.cwd(), "")`
- `appBasePath = normalizeBasePath(env.VITE_APP_BASE_PATH)`
- Vite `base` is set to `appBasePath`

`normalizeBasePath()` in `frontend/src/shared/config/envContract.ts`:

- missing/empty or `/` -> `/`
- any other value -> `/<trimmed>/`

So, for the current hosted contract, `VITE_APP_BASE_PATH=/` produces a root-path build.

### Runtime routing base (`src/shared/config/env.ts` + `src/app/routes.tsx`)

`frontend/src/shared/config/env.ts`:

- `appBasePath = normalizeBasePath(import.meta.env.VITE_APP_BASE_PATH || import.meta.env.BASE_URL)`
- `routerBasePath = appBasePath === "/" ? "/" : appBasePath.replace(/\/$/, "")`

`frontend/src/app/routes.tsx`:

- `createBrowserRouter(..., { basename: env.routerBasePath })`

Static public asset URLs for branding are also base-path-aware through `buildPublicAssetUrl()`.

## 3) Is a subpath deployment currently assumed?

Code: subpath deployment is still supported and first-class.

Operational contract:

- The hosted Vercel contract is now explicit root-path deploy: `VITE_APP_BASE_PATH=/`.
- Local validation docs still retain `/accmed/` as a local-only baseline in some places, but that is no longer the hosted deploy assumption.

Implication for Batch A:

- Root-path deployment is now the active hosted contract.
- Subpath examples should be treated as local-only or legacy validation context unless a later batch reintroduces them explicitly.

## 4) Does `vercel.json` already exist?

Yes:

- Repo root does not carry its own `vercel.json`.
- `frontend/vercel.json` exists and version-controls the current Vercel deploy behavior for the frontend project root.

## 5) Does `DEPLOY.md` exist?

Yes. `DEPLOY.md` now exists and serves as the versioned operator contract for the current Vercel deployment posture.

Other deployment-adjacent docs still serving as operator guidance:

- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- `docs/client-launch-runbook.md`
- `frontend/README.md`

## 6) Exact files likely affected by Batch A

Batch A artifacts already in repo:

- `frontend/vercel.json`
- `DEPLOY.md`

Batch A configuration outside git:

- Vercel Project setting: Root Directory = `frontend/`
- Vercel Environment Variable: `VITE_APP_BASE_PATH=/`

Files that still carry related local-only or follow-up deployment context:

- `docs/client-launch-runbook.md`
- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`

## 7) Exact validation steps needed for Batch A

This repo's frontend build currently hard-requires `VITE_DEPLOY_TARGET`.

### Local validation (fastest)

From `frontend/`:

1. Build with explicit root base path:
   - `VITE_DEPLOY_TARGET=local VITE_APP_BASE_PATH=/ npm run build`
2. Run tests:
   - `npm run test`
3. Optional sanity check:
   - `VITE_DEPLOY_TARGET=local VITE_APP_BASE_PATH=/ npm run preview`

Expected:

- build succeeds
- asset paths assume `/` as base
- env/base-path tests remain green

### Client-safe build validation (hosted posture)

From `frontend/`:

- `VITE_DEPLOY_TARGET=client VITE_CLIENT_CODE=accmed VITE_API_BASE_URL=https://api.example.com VITE_APP_BASE_PATH=/ npm run build`

Expected:

- build succeeds with explicit client envs

### Vercel validation (Batch A acceptance)

In Vercel project settings:

1. Set Root Directory to `frontend/`.
2. Ensure build command is `npm run build`.
3. Set `VITE_APP_BASE_PATH=/` for the relevant environment(s).

Expected:

- Vercel build runs in `frontend/`
- the app is served from domain root (`/`)

Notes:

- Deep-link SPA refresh behavior and Preview vs Production env separation were handled in later batches. This Batch A snapshot should now be read only as the root-directory and base-path foundation already implemented in repo.
