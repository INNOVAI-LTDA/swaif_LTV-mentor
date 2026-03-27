# Vercel Deploy (Batch D)

Purpose: keep the SPA deploy rooted at `frontend/`, publish it at `/`, and version the host behavior needed for the first stable Vercel deployment.

## Vercel Project Settings
- Root Directory: `frontend`
- Framework Preset: `Vite`
- Build Command: `npm run build`
- Output Directory: `dist`

## Required Environment Variables (build time)
- `VITE_DEPLOY_TARGET=client` (frontend contract requires this)
- `VITE_APP_BASE_PATH=/` (root-path deploy)
- `VITE_API_BASE_URL` = **absolute** `https://` URL (no credentials, no query/hash)
- `VITE_CLIENT_CODE` = client identifier (letters/numbers/hyphen/underscore)
- Do **not** place secrets in `VITE_*`; keep secrets in backend/env or Vercel project secrets.
- Use the example files for environment scoping:
  - `frontend/.env.preview.example` for Vercel Preview values
  - `frontend/.env.production.example` for Vercel Production values

## Notes on Base Path
- Code supports subpaths, but the current hosted contract sets the production deploy to `/`.
- Existing docs include subpath examples (`/accmed/`, `/cliente/`) for local/staging; do not reuse them for the Vercel root deploy unless explicitly justified.

## Custom Domain Contract (Batch D)
- Custom domain attachment and DNS remain Vercel/dashboard work; they are not created from Git.
- The current production-domain assumption comes from the AccMed branding reference: apex `https://aceleradormedico.com.br` redirects to canonical `https://www.aceleradormedico.com.br`.
- Canonical host redirect is versioned in `frontend/vercel.json`.
- Trailing slash policy is explicit: `trailingSlash=false` with no extra application-route slash redirects.
- If the final production app host is not `aceleradormedico.com.br`, update `frontend/vercel.json` before deploy.

## Hosted Smoke Checklist
Run on both:
- Vercel Preview URL for the PR
- Production custom domain `https://www.aceleradormedico.com.br`

Checks:
- Home page loads.
- Browser console has no `404` asset errors.
- API base URL points to the intended backend; no requests target `127.0.0.1` or `localhost`.
- Nested route refresh works for `/`, `/login`, `/dashboard`, `/app/admin`, `/app/matriz-renovacao`, and `/app/aluno`.
- Login/auth flow works and protected navigation behaves as expected.
- Custom domain works with valid TLS and correct host in the address bar.
- Apex to www redirect works from `https://aceleradormedico.com.br` to `https://www.aceleradormedico.com.br`, preserving path and query string.
- Baseline security headers exist if already configured on the deployment.
- Preview deploy works from the PR URL with Preview-scoped environment values.

## Minimal Validation (local)
Run from `frontend/`:
- `npm run test`
- `VITE_DEPLOY_TARGET=local VITE_APP_BASE_PATH=/ npm run build`
- `VITE_DEPLOY_TARGET=client VITE_CLIENT_CODE=accmed VITE_API_BASE_URL=https://api.example.com VITE_APP_BASE_PATH=/ npm run build`

## Validation After Production Deploy
- Confirm Vercel lists `www.aceleradormedico.com.br` as the assigned production domain and TLS is healthy.
- Visit `https://aceleradormedico.com.br/login?next=%2Fapp%2Fadmin` and confirm it lands on `https://www.aceleradormedico.com.br/login?next=%2Fapp%2Fadmin` without a redirect loop.
- Hard-refresh the smoke routes on the canonical host and confirm the SPA rewrite still serves `index.html`.

## Out of Scope (other batches)
- CORS alignment (Batch C)
- Security headers/CSP/HSTS (Batches E/F)
- Cache strategy (Batch G)
