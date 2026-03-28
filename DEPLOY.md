# Vercel Deploy (Batch F)

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
- The current production-domain contract is explicit: apex `https://innovai-solutions.com.br` redirects to canonical `https://www.innovai-solutions.com.br`.
- `docs/branding/design-system-acelerador-medico.md` is a client-site branding reference only; it is not the deploy-host source of truth.
- Canonical host redirect is versioned in `frontend/vercel.json`.
- Trailing slash policy is explicit: `trailingSlash=false` with no extra application-route slash redirects.
- If the final production app host changes from `innovai-solutions.com.br`, update `frontend/vercel.json` before deploy.

## Hosted Smoke Checklist
Run on both:
- Vercel Preview URL for the PR
- Production custom domain `https://www.innovai-solutions.com.br`

Checks:
- Home page loads.
- Browser console has no `404` asset errors.
- API base URL points to the intended backend; no requests target `127.0.0.1` or `localhost`.
- Nested route refresh works for `/`, `/login`, `/dashboard`, `/app/admin`, `/app/matriz-renovacao`, and `/app/aluno`.
- Login/auth flow works and protected navigation behaves as expected.
- Custom domain works with valid TLS and correct host in the address bar.
- Apex to www redirect works from `https://innovai-solutions.com.br` to `https://www.innovai-solutions.com.br`, preserving path and query string.
- Baseline security headers exist on the HTML response:
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `X-Frame-Options: DENY`
  - `Permissions-Policy` denying unused capabilities
- CSP rollout is active in report-only mode on the HTML response:
  - `Content-Security-Policy-Report-Only`
  - no console CSP violations on `/`, `/login`, `/dashboard`, `/app/admin`, `/app/matriz-renovacao`, and `/app/aluno`
- HSTS is still intentionally absent until stable custom-domain HTTPS is verified on the live host.
- Preview deploy works from the PR URL with Preview-scoped environment values.

## CSP And HSTS Rollout (Batch F)
- Current Batch F posture is `Content-Security-Policy-Report-Only`, not enforcing CSP yet.
- Baseline directives start from:
  - `default-src 'self'`
  - `base-uri 'self'`
  - `form-action 'self'`
  - `object-src 'none'`
  - `frame-ancestors 'none'`
  - `upgrade-insecure-requests`
- Current justified allowances are limited to:
  - `connect-src 'self' https:` so the hosted SPA can reach the intended HTTPS backend while the exact production backend host remains operator-supplied
  - `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com` because the frontend currently imports Google Fonts and sets runtime CSS variables on `document.documentElement.style`
  - `font-src 'self' https://fonts.gstatic.com data:`
  - `img-src 'self' data:`
- Do not promote this to enforcing `Content-Security-Policy` until Preview validation shows no real violations on the active route set.
- `Strict-Transport-Security` remains disabled in repo for now.
- Enable HSTS only after all of the following are true on the live deployment:
  - `https://www.innovai-solutions.com.br` serves valid TLS
  - `https://innovai-solutions.com.br` redirects cleanly to the canonical `www` host
  - operators have validated the canonical host behavior on the live domain
- Do not add `preload` in this batch.

## Minimal Validation (local)
Run from `frontend/`:
- `npm run test`
- `VITE_DEPLOY_TARGET=local VITE_APP_BASE_PATH=/ npm run build`
- `VITE_DEPLOY_TARGET=client VITE_CLIENT_CODE=accmed VITE_API_BASE_URL=https://api.example.com VITE_APP_BASE_PATH=/ npm run build`

## Validation After Production Deploy
- Confirm Vercel lists `www.innovai-solutions.com.br` as the assigned production domain and TLS is healthy.
- Visit `https://innovai-solutions.com.br/login?next=%2Fapp%2Fadmin` and confirm it lands on `https://www.innovai-solutions.com.br/login?next=%2Fapp%2Fadmin` without a redirect loop.
- Hard-refresh the smoke routes on the canonical host and confirm the SPA rewrite still serves `index.html`.
- Confirm `Content-Security-Policy-Report-Only` is present on the HTML response and no route in the smoke set logs CSP violations in the browser console.
- Confirm `Strict-Transport-Security` is still absent unless the custom-domain HTTPS gate above has been explicitly completed and approved.

## Out of Scope (other batches)
- CORS alignment (Batch C)
- Cache strategy (Batch G)
