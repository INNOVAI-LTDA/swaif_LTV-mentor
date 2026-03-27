# Batch A (Vercel) - Current State Snapshot (Targeted)

Date: 2026-03-26
Scope: Document only the current repo state relevant to Batch A:

- lock `frontend/` as the Vercel project root
- set `VITE_APP_BASE_PATH=/`
- add `frontend/vercel.json`

This is intentionally narrow and does not attempt to document the full project.

## 1) Is `frontend/` already the real deployable root?

Yes, by structure:

- Repo root does **not** contain a `package.json`.
- `frontend/package.json` exists and contains the Vite/React build pipeline:
  - `build`: `tsc --noEmit && vite build`
  - `test`: `vitest run`
- Therefore, a Vercel project configured at the repo root would have no obvious Node build entrypoint unless the Vercel project root directory is explicitly set to `frontend/`.

Implication for Batch A:

- “Lock frontend as the Vercel project root” is aligned with the current repo layout. Treat `frontend/` as the deployable unit.

## 2) Current Vite base-path behavior

### Build-time base (`vite.config.ts`)

`frontend/vite.config.ts` resolves:

- `env = loadEnv(mode, process.cwd(), "")` (reads `VITE_*` from the `frontend/` working directory)
- `appBasePath = normalizeBasePath(env.VITE_APP_BASE_PATH)`
- Vite `base` is set to `appBasePath`

`normalizeBasePath()` in `frontend/src/shared/config/envContract.ts`:

- missing/empty or `/` -> `/`
- any other value -> `/<trimmed>/` (forces leading + trailing slash)

So today, if `VITE_APP_BASE_PATH` is **unset**, the build base is `/`.

### Runtime routing base (`src/shared/config/env.ts` + `src/app/routes.tsx`)

`frontend/src/shared/config/env.ts`:

- `appBasePath = normalizeBasePath(import.meta.env.VITE_APP_BASE_PATH || import.meta.env.BASE_URL)`
- `routerBasePath = appBasePath === "/" ? "/" : appBasePath.replace(/\/$/, "")`

`frontend/src/app/routes.tsx`:

- `createBrowserRouter(..., { basename: env.routerBasePath })`

So the runtime router basename is:

- `/` when `VITE_APP_BASE_PATH=/`
- `/<subpath>` when `VITE_APP_BASE_PATH=/<subpath>/`

Static public asset URLs for branding are also base-path-aware:

- `buildPublicAssetUrl()` prefixes with `env.appBasePath`

## 3) Is a subpath deployment currently assumed?

Code: subpath deployment is supported and first-class (router basename + asset URL helper).

Docs/runbooks: the current operational baseline is explicitly subpath-oriented:

- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` lists `Base path alvo` as `/accmed/` for the local baseline.
- `docs/client-launch-runbook.md` uses `/accmed/` as “Current Local Baseline” and uses `/cliente/` as the example “Required Inputs”.

Implication for Batch A:

- Changing deployment to domain root (`/`) is supported by the code, but is a shift from the current documentation baseline that has been validating under `/accmed/`.

## 4) Does `vercel.json` already exist?

No:

- `vercel.json` does not exist at repo root.
- `frontend/vercel.json` does not exist.

## 5) Does `DEPLOY.md` exist?

No `DEPLOY.md` is present.

Existing deployment-adjacent docs currently serving as operator guidance:

- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- `docs/client-launch-runbook.md`
- `frontend/README.md`

## 6) Exact files likely affected by Batch A

Batch A changes (direct artifacts):

- `frontend/vercel.json` (new)

Batch A changes (configuration outside git):

- Vercel Project setting: Root Directory = `frontend/`
- Vercel Environment Variable: `VITE_APP_BASE_PATH=/`

Files that may need follow-up edits in later batches (not part of Batch A itself, but tightly coupled):

- `docs/client-launch-runbook.md` (currently assumes `/accmed/` baseline and `/cliente/` example)
- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` (currently records evidence around `/accmed/`)

## 7) Exact validation steps needed for Batch A

This repo’s frontend build currently hard-requires `VITE_DEPLOY_TARGET` (see `frontend/src/shared/config/envContract.ts` and `frontend/vite.config.ts`).

### Local validation (fastest)

From `frontend/`:

1. Build with explicit root base path:

   - `VITE_DEPLOY_TARGET=local VITE_APP_BASE_PATH=/ npm run build`

   Expected:
   - build succeeds
   - produced asset paths assume `/` as base (not `/accmed/` or `/cliente/`)

2. Run tests:

   - `npm run test`

   Expected:
   - env/base-path contract tests remain green (`frontend/src/shared/config/env.test.ts`)
   - route smoke tests that exercise basename remain green (`frontend/src/test/routes.smoke.test.tsx`)

Optional sanity check:

- `VITE_DEPLOY_TARGET=local VITE_APP_BASE_PATH=/ npm run preview`

### Client-safe build validation (to match hosted posture)

From `frontend/`:

- `VITE_DEPLOY_TARGET=client VITE_CLIENT_CODE=accmed VITE_API_BASE_URL=https://api.example.com VITE_APP_BASE_PATH=/ npm run build`

Expected:

- build succeeds (client deploy target requires `VITE_API_BASE_URL` and `VITE_CLIENT_CODE`)

### Vercel validation (Batch A acceptance)

In Vercel project settings:

1. Set Root Directory to `frontend/`.
2. Ensure build command is `npm run build` (defaults are fine if Vercel detects a Vite project).
3. Set environment variable `VITE_APP_BASE_PATH=/` for the relevant environment(s).

Expected:

- Vercel build runs in `frontend/` and does not fail due to missing root `package.json`.
- Built app is served from domain root (`/`), not a subpath.

Notes:

- Deep-link SPA refresh behavior and Preview vs Production env separation are intentionally deferred to later batches (Batch B+). Batch A’s validation is focused on root directory and base-path invariants only.

