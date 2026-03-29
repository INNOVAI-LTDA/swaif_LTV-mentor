# Batch D (Custom Domain, Canonical Host, Redirects, Smoke Checks) - Current State

Scope: document only what is true in the repo today that impacts Batch D (custom domain, canonical host policy, redirects, trailing slash behavior, and smoke-test checklist posture).

## Custom Domain Connection (Current)

There is no versioned artifact in this repo that proves `accmed.innovai-solutions.com.br` is already connected in Vercel (domain attachment, DNS, and TLS are Vercel/DNS-side configuration).

What is versioned today:

- `frontend/vercel.json` exists and is the only committed Vercel config file.
- No root `vercel.json` exists at repo root (Vercel Root Directory is expected to be `frontend` per `DEPLOY.md`).
- `DEPLOY.md` and `docs/client-launch-runbook.md` treat `https://accmed.innovai-solutions.com.br` as the intended production app host.

Implication: whether the AccMed app subdomain is connected must currently be verified in the Vercel dashboard and in DNS, not in Git.

## Canonical Host Policy (Current)

The current app-host contract is explicit as `https://accmed.innovai-solutions.com.br`.

No host-level redirect is versioned for the app because the chosen AccMed contract uses a single production hostname.

Implication: the root domain `innovai-solutions.com.br` is not part of the AccMed app-host contract or app smoke tests.

## Redirect Rules (Current)

`frontend/vercel.json` contains no host-level redirects for the AccMed deployment.

What remains versioned:

- SPA rewrite: `rewrites: [{ "source": "/(.*)", "destination": "/index.html" }]`
- Security headers and CSP report-only headers from Batches E/F

## Trailing Slash Behavior (Current)

Trailing slash behavior is standardized in repo: `frontend/vercel.json` sets `trailingSlash=false`.

Implication: the published app should remain rooted at `/` with no extra slash-normalization rules added in app config.

## `DEPLOY.md` Status (Current)

`DEPLOY.md` exists and documents the current frontend Vercel settings:

- Root Directory: `frontend`
- Framework Preset: Vite
- Build Command: `npm run build`
- Output Directory: `dist`

`DEPLOY.md` also contains hosted smoke checks for:

- the chosen production app host `https://accmed.innovai-solutions.com.br`
- valid TLS on the published app host
- no unexpected host redirects or redirect loops
- SPA refresh on the route set
- baseline security headers and CSP report-only posture
- HSTS still absent until the HTTPS gate is explicitly closed

## Files Likely Affected By Batch D

- `frontend/vercel.json`
  - keep the single-host contract explicit and preserve SPA rewrite / headers
- `DEPLOY.md`
  - keep the AccMed subdomain contract and hosted smoke checklist aligned
- `docs/client-launch-runbook.md`
  - keep operator procedure aligned to the chosen app host and backend pair
- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
  - if this remains a release gate, keep domain/TLS/host-validation items aligned with the single-host contract

## Validation Steps Needed For Batch D (Current Contract)

DNS / Vercel:

1. Confirm `accmed.innovai-solutions.com.br` is added to the Vercel project (Production) and has a valid TLS certificate.
2. Confirm Preview behavior expectations (Preview URLs usually remain `*.vercel.app`; custom preview domains are optional).

Hosted app-host validation:

1. Verify the chosen app host loads directly:
   - `https://accmed.innovai-solutions.com.br/`
2. Verify path preservation on the same host:
   - `https://accmed.innovai-solutions.com.br/login?next=%2Fapp%2Fadmin`
3. Verify no unexpected host redirect or loop occurs.
4. Verify trailing slash posture:
   - `/login` and `/login/` behave consistently with `trailingSlash=false`.

Hosted SPA smoke (must remain valid after host validation):

1. Hard-refresh these routes on the final app host:
   - `/`
   - `/login`
   - `/dashboard`
   - `/app/admin`
   - `/app/matriz-renovacao`
   - `/app/aluno`
2. Confirm each refresh returns the SPA shell (no host `404`) and the app loads.
