# Vercel Batch B Current State (Targeted Snapshot)

Date: 2026-03-26

Scope: document only the current repo state relevant to Batch B:

- fix SPA routing explicitly (deep-link refresh behavior on host)
- separate Preview and Production environments (operator contract)
- set `VITE_API_BASE_URL` explicitly (no accidental localhost usage in hosted builds)

## Current Deep-Link / Refresh Behavior

### What works today (local dev / local preview)

- Local `vite dev` and `vite preview` typically serve `index.html` for unknown paths (history fallback), so refreshing a nested route such as `/app/admin` will still load the SPA shell and let React Router resolve the route.
- This local behavior is not proof that the hosted environment will handle deep-link refreshes correctly.

### What is expected to fail today (Vercel without rewrites)

- The current Vercel configuration does **not** include a catch-all rewrite to `/index.html`.
- Without an explicit SPA rewrite, a browser refresh on deep routes (examples: `/login`, `/app/admin`, `/app/matriz-renovacao`, `/app/aluno`) is expected to return a host-level `404` because the host will look for a static file at that path rather than serving `index.html`.

## SPA Rewrites (Current State)

- `frontend/vercel.json` exists but contains **no** `rewrites` rules.
- `DEPLOY.md` documents the intended next-step rewrite snippet for Batch B:
  - `rewrites: [{ source: "/(.*)", destination: "/index.html" }]`
- Repo scan shows no other host rewrite mechanisms committed for Vercel (no root `vercel.json`, no `frontend/public/_redirects`, no equivalent).

## Router + Nested Routes (Current State)

### Router configuration

- React Router is created via `createBrowserRouter(...)` with `basename: env.routerBasePath` in `frontend/src/app/routes.tsx`.
- `env.routerBasePath` is derived from `VITE_APP_BASE_PATH` (and falls back to `import.meta.env.BASE_URL`) in `frontend/src/shared/config/env.ts`.

### Route shape relevant to deep linking

- Top-level shell route: `/` renders `AppLayout`.
- Public: `/login`.
- Protected area: `/app/*` is nested under `RequireAuth`, with nested routes such as:
  - `/app/admin` (admin-only)
  - `/app/hub-interno`, `/app/centro-comando`, `/app/radar`, `/app/matriz-renovacao` (mentor-only workspace)
  - `/app/aluno` (authenticated user)
- Unknown paths within the SPA resolve to a `NotFoundPage` via `path: "*"` under the layout route, but that only works if the host serves `index.html` for the URL first (rewrite).

## Preview vs Production Environment Separation (Current State)

- The frontend env contract recognizes only `VITE_DEPLOY_TARGET=local` or `VITE_DEPLOY_TARGET=client` (`frontend/src/shared/config/envContract.ts`).
  - There is no first-class `preview` deploy target in the app config. (Tests currently assert that `preview` is invalid.)
- As documented in `DEPLOY.md` and `frontend/README.md`, Vercel Preview and Production separation currently exists only operationally:
  - operators must configure the same set of required `VITE_*` vars in both Vercel `Preview` and `Production`
  - differing values between Preview and Production (for example different API base URLs) must be done via Vercel's environment-scoped variables, not via a distinct `VITE_DEPLOY_TARGET`
- The repo currently has no committed `.env.production`, `.env.preview`, or similar environment files for hosted builds; local-only `.env` exists under `frontend/`.

## `VITE_API_BASE_URL` Explicitness (Current State)

### Fallback behavior

- `VITE_API_BASE_URL` is **fallback-based** only when `VITE_DEPLOY_TARGET=local`:
  - if unset, it normalizes to `http://127.0.0.1:8000` (`frontend/src/shared/config/envContract.ts`).

### Hosted/client behavior

- For `VITE_DEPLOY_TARGET=client`, `VITE_API_BASE_URL` is required and validated:
  - `frontend/vite.config.ts` fails the build if `VITE_API_BASE_URL` is missing for `client` builds
  - `frontend/src/shared/config/env.ts` also normalizes at runtime import time, so missing/invalid values will hard-fail the client bundle
- The current operator docs already treat `VITE_API_BASE_URL` as required for hosted builds, but the contract does not yet explicitly differentiate Preview vs Production values beyond "set vars in both environments".

## `VITE_CLIENT_CODE` Separation (Current State)

- `VITE_CLIENT_CODE` is required for `VITE_DEPLOY_TARGET=client` and optional for `local` (`frontend/src/shared/config/envContract.ts`).
- There is no repo-level separation or naming convention for Preview vs Production `VITE_CLIENT_CODE`. If Preview needs a different code, it must be set via Vercel environment-scoped variables.

## Files Likely Affected By Batch B

SPA rewrite + explicit routing fixes:

- `frontend/vercel.json` (add `rewrites` for SPA deep-link refresh; keep changes scoped to Batch B)
- `DEPLOY.md` (keep the "next snippet" aligned with the actual committed rewrite once applied)

Preview vs Production separation contract:

- `DEPLOY.md` (operator instructions for setting vars distinctly in Vercel Preview vs Production)
- `frontend/README.md` (frontend operator contract summary)
- Optionally, if introducing a first-class notion of preview channel inside the app: `frontend/src/shared/config/envContract.ts` and `frontend/src/shared/config/env.ts` (but that is a behavioral change and should be justified explicitly)

API base explicitness and no-localhost guarantees:

- `frontend/src/shared/config/envContract.ts` (only if changing fallback policy; currently local-only fallback is intentional)
- `frontend/vite.config.ts` (only if strengthening build-time validation further)

## Validation Steps Needed For Batch B

### Local validation (fast)

From `frontend/`:

- `npm run test`
- `VITE_DEPLOY_TARGET=client VITE_CLIENT_CODE=accmed VITE_API_BASE_URL=https://api.example.com VITE_APP_BASE_PATH=/ npm run build`
- `VITE_DEPLOY_TARGET=client VITE_CLIENT_CODE=accmed VITE_API_BASE_URL=https://api.example.com VITE_APP_BASE_PATH=/ npm run build && npm run preview`
  - manually refresh deep routes in the browser:
    - `/login`
    - `/app/admin`
    - `/app/matriz-renovacao`
    - `/app/aluno`

Note: local `vite preview` may still mask missing host rewrites; treat local refresh as a sanity check only.

### Hosted validation (Vercel Preview and Production)

After applying the SPA rewrite and setting envs explicitly:

- Confirm Vercel Preview build has `VITE_DEPLOY_TARGET=client`, `VITE_CLIENT_CODE`, and an explicit `VITE_API_BASE_URL` (Preview-specific if applicable).
- Confirm Vercel Production build has `VITE_DEPLOY_TARGET=client`, `VITE_CLIENT_CODE`, and an explicit `VITE_API_BASE_URL` (Production URL).
- On each environment, open and hard-refresh:
  - `/login`
  - `/app/admin`
  - `/app/matriz-renovacao`
  - `/app/aluno`
  Expected: SPA loads (no host `404`), then React Router handles auth redirects/guards.
- In browser devtools network, confirm no request targets `127.0.0.1` or `localhost` in hosted environments.
