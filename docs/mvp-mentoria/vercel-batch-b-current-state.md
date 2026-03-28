# Vercel Batch B Current State (Targeted Snapshot)

Date: 2026-03-27

Scope: document only the current repo state relevant to Batch B:

- fix SPA routing explicitly (deep-link refresh behavior on host)
- separate Preview and Production environments (operator contract)
- set `VITE_API_BASE_URL` explicitly (no accidental localhost usage in hosted builds)

## Current Deep-Link / Refresh Behavior

### What works today (local dev / local preview)

- Local `vite dev` and `vite preview` typically serve `index.html` for unknown paths, so refreshing a nested route such as `/app/admin` still loads the SPA shell.
- This local behavior is still only a sanity check; hosted validation remains necessary.

### What is expected to work today (hosted Vercel contract)

- The current Vercel configuration includes a catch-all SPA rewrite to `/index.html`.
- With that rewrite in place, a browser refresh on deep routes such as `/`, `/login`, `/dashboard`, `/app/admin`, `/app/matriz-renovacao`, and `/app/aluno` is expected to return the SPA shell first, then let React Router resolve the route and auth guards.

## SPA Rewrites (Current State)

- `frontend/vercel.json` exists and contains the committed catch-all SPA rewrite:
  - `rewrites: [{ source: "/(.*)", destination: "/index.html" }]`
- `DEPLOY.md` documents hosted validation against the active rewrite contract.
- No additional Vercel host rewrite mechanism is required for the current frontend deployment contract.

## Router + Nested Routes (Current State)

### Router configuration

- React Router is created via `createBrowserRouter(...)` with `basename: env.routerBasePath` in `frontend/src/app/routes.tsx`.
- `env.routerBasePath` is derived from `VITE_APP_BASE_PATH` in `frontend/src/shared/config/env.ts`.

### Route shape relevant to deep linking

- Top-level shell route: `/`
- Public: `/login`
- Protected area: `/app/*`
- Hosted validation now explicitly includes `/dashboard`, `/app/admin`, `/app/matriz-renovacao`, and `/app/aluno`
- Unknown paths within the SPA resolve to `NotFoundPage` once the host rewrite serves `index.html`

## Preview vs Production Environment Separation (Current State)

- The frontend env contract still recognizes only `VITE_DEPLOY_TARGET=local` or `VITE_DEPLOY_TARGET=client`.
- There is still no first-class `preview` deploy target inside app runtime config, and that remains intentional.
- Preview vs Production separation exists operationally through Vercel environment-scoped variables, not through a distinct deploy target.
- The repo now includes committed hosted env examples:
  - `frontend/.env.preview.example`
  - `frontend/.env.production.example`

## `VITE_API_BASE_URL` Explicitness (Current State)

### Fallback behavior

- `VITE_API_BASE_URL` is fallback-based only when `VITE_DEPLOY_TARGET=local`.
- In that local-only case, it can normalize to `http://127.0.0.1:8000`.

### Hosted/client behavior

- For `VITE_DEPLOY_TARGET=client`, `VITE_API_BASE_URL` is required and validated.
- Hosted Preview and Production values are expected to be explicit and environment-scoped in Vercel.
- Current operator docs already treat hosted builds as invalid if `VITE_API_BASE_URL` is absent.

## `VITE_CLIENT_CODE` Separation (Current State)

- `VITE_CLIENT_CODE` is required for `VITE_DEPLOY_TARGET=client`.
- If Preview and Production need different values, that separation is handled through Vercel environment-scoped variables.

## Files Likely Affected By Batch B

Hosted routing + env contract artifacts already in repo:

- `frontend/vercel.json`
- `DEPLOY.md`
- `frontend/.env.preview.example`
- `frontend/.env.production.example`
- `frontend/README.md`

Optional behavioral files only if the deploy-target model changes in the future:

- `frontend/src/shared/config/envContract.ts`
- `frontend/src/shared/config/env.ts`

## Validation Steps Needed For Batch B

### Local validation (fast)

From `frontend/`:

- `npm run test`
- `VITE_DEPLOY_TARGET=client VITE_CLIENT_CODE=accmed VITE_API_BASE_URL=https://api.example.com VITE_APP_BASE_PATH=/ npm run build`
- `VITE_DEPLOY_TARGET=client VITE_CLIENT_CODE=accmed VITE_API_BASE_URL=https://api.example.com VITE_APP_BASE_PATH=/ npm run build && npm run preview`

Local refresh sanity routes:

- `/`
- `/login`
- `/dashboard`
- `/app/admin`
- `/app/matriz-renovacao`
- `/app/aluno`

Note: local `vite preview` may still mask host-specific issues; treat it as a sanity check only.

### Hosted validation (Vercel Preview and Production)

With the committed SPA rewrite and explicit envs in place:

- Confirm Vercel Preview has `VITE_DEPLOY_TARGET=client`, `VITE_CLIENT_CODE`, and explicit Preview-scoped `VITE_API_BASE_URL`.
- Confirm Vercel Production has `VITE_DEPLOY_TARGET=client`, `VITE_CLIENT_CODE`, and explicit Production-scoped `VITE_API_BASE_URL`.
- On each environment, hard-refresh:
  - `/`
  - `/login`
  - `/dashboard`
  - `/app/admin`
  - `/app/matriz-renovacao`
  - `/app/aluno`
- Expected: the SPA loads with no host `404`, then React Router handles auth redirects and guards.
- In browser devtools network, confirm no request targets `127.0.0.1` or `localhost` in hosted environments.
