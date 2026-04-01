# Vercel Deploy (Batch F)

Purpose: keep the SPA deploy rooted at `frontend/`, publish it at `/`, and version the host behavior needed for the first stable Vercel deployment.

## Vercel Project Settings
- Root Directory: `frontend`
- Framework Preset: `Vite`
- Build Command: `npm run build`
- Output Directory: `dist`

## Railway Backend Settings
- Root Directory: `backend`
- Start Command: your standard FastAPI/Uvicorn entrypoint for `backend/app/main.py`
- Mount the persistent volume at `/app/data`
- Keep the JSON store-path overrides unset unless you intentionally want a non-default layout

## Railway Required Environment Variables
- `APP_ENV=production`
- `CLIENT_CODE=accmed`
- `CORS_ALLOW_ORIGINS=https://accmed.innovai-solutions.com.br`
- `APP_AUTH_SECRET=<strong-random-secret>`
- `STORAGE_BACKUP_DIR=/app/data/backups`

Optional:
- `CORS_ALLOW_ORIGIN_REGEX=^https://.*\.vercel\.app$` to allow Preview deployments
- `ENABLE_MENTOR_ROUTES=true` only if you want to force the published mentor surface on explicitly; current runtime defaults to enabled

## Required Environment Variables (build time)
- `VITE_DEPLOY_TARGET=client` (frontend contract requires this)
- `VITE_APP_BASE_PATH=/` (root-path deploy)
- `VITE_API_BASE_URL` = **absolute** `https://` URL (no credentials, no query/hash)
- `VITE_CLIENT_CODE` = client identifier (letters/numbers/hyphen/underscore)
- `VITE_CLIENT_NAME=Grupo Acelerador Médico`
- `VITE_APP_NAME=Gamma`
- `VITE_APP_TAGLINE=Acompanhamento com visão operacional`
- `VITE_SHELL_SUBTITLE=Operação, acompanhamento e governança`
- Do **not** place secrets in `VITE_*`; keep secrets in backend/env or Vercel project secrets.
- Use the example files for environment scoping:
  - `frontend/.env.preview.example` for Vercel Preview values
  - `frontend/.env.production.example` for Vercel Production values
- Keep hosted flags disabled:
  - `VITE_ENABLE_DEMO_MODE=false`
  - `VITE_ENABLE_INTERNAL_MENTOR_SURFACE=false`

## Notes on Base Path
- Code supports subpaths, but the current hosted contract sets the production deploy to `/`.
- Existing docs include subpath examples (`/accmed/`, `/cliente/`) for local/staging; do not reuse them for the Vercel root deploy unless explicitly justified.

## Custom Domain Contract (Batch D)
- Custom domain attachment and DNS remain Vercel/dashboard work; they are not created from Git.
- The current production app host is explicit: `https://accmed.innovai-solutions.com.br`.
- `docs/branding/design-system-acelerador-medico.md` is a client-site branding reference only; it is not the deploy-host source of truth.
- No app-host redirect is versioned in `frontend/vercel.json`; the current AccMed contract uses a single production hostname.
- Trailing slash policy is explicit: `trailingSlash=false` with no extra application-route slash redirects.
- If the final production app host changes from `accmed.innovai-solutions.com.br`, update `frontend/vercel.json` before deploy.

## Hosted Smoke Checklist
Run on both:
- Vercel Preview URL for the PR
- Production custom domain `https://accmed.innovai-solutions.com.br`

Checks:
- Home page loads.
- Browser console has no `404` asset errors.
- API base URL points to the intended backend; no requests target `127.0.0.1` or `localhost`.
- Backend OpenAPI on the published API host contains `/mentor/matriz-renovacao`, `/mentor/radar`, and `/mentor/centro-comando`.
- Nested route refresh works for `/`, `/login`, `/dashboard`, `/app/admin`, `/app/matriz-renovacao`, and `/app/aluno`.
- Login/auth flow works and protected navigation behaves as expected.
- Custom domain works with valid TLS and the address bar stays on `https://accmed.innovai-solutions.com.br`.
- No unexpected host redirect or redirect loop occurs on the published app host.
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
  - `connect-src 'self' https:` so the hosted SPA can reach `https://api-accmed.innovai-solutions.com.br` and Preview backends while CSP remains report-only
  - `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com` because the frontend currently imports Google Fonts and sets runtime CSS variables on `document.documentElement.style`
  - `font-src 'self' https://fonts.gstatic.com data:`
  - `img-src 'self' data:`
- Do not promote this to enforcing `Content-Security-Policy` until Preview validation shows no real violations on the active route set.
- `Strict-Transport-Security` remains disabled in repo for now.
- Enable HSTS only after all of the following are true on the live deployment:
  - `https://accmed.innovai-solutions.com.br` serves valid TLS
  - operators have validated the chosen app host behavior on the live domain
- Do not add `preload` in this batch.

## Minimal Validation (local)
Run from `frontend/`:
- `npm run test`
- `VITE_DEPLOY_TARGET=local VITE_APP_BASE_PATH=/ npm run build`
- `VITE_DEPLOY_TARGET=client VITE_CLIENT_CODE=accmed VITE_API_BASE_URL=https://api-accmed.innovai-solutions.com.br VITE_APP_BASE_PATH=/ npm run build`

## Validation After Production Deploy
- Confirm Vercel lists `accmed.innovai-solutions.com.br` as the assigned production domain and TLS is healthy.
- Visit `https://accmed.innovai-solutions.com.br/login?next=%2Fapp%2Fadmin` and confirm it stays on `https://accmed.innovai-solutions.com.br/login?next=%2Fapp%2Fadmin` without a redirect loop.
- Hard-refresh the smoke routes on the canonical host and confirm the SPA rewrite still serves `index.html`.
- Confirm `Content-Security-Policy-Report-Only` is present on the HTML response and no route in the smoke set logs CSP violations in the browser console.
- Confirm `Strict-Transport-Security` is still absent unless the custom-domain HTTPS gate above has been explicitly completed and approved.

## Out of Scope (other batches)
- CORS alignment (Batch C)
- Cache strategy (Batch G)
