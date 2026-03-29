# Batch F (CSP And HSTS) - Current State (Brownfield)

Date: 2026-03-27
Scope: document only the current repo state relevant to Batch F:

- add CSP carefully
- enable HSTS only after stable custom-domain HTTPS

This is intentionally narrow and does not attempt to document the full project.

## 1) Current external assets, scripts, frames, and integrations that affect CSP

Current frontend CSP-relevant surface in repo:

- Same-origin module bootstrap only:
  - [index.html](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/index.html) loads one module script: `/src/main.tsx`
- Same-origin public branding assets:
  - [public](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/public) contains branding images under `branding/`
  - [env.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/shared/config/env.ts) builds branding URLs from same-origin public paths by default
- One real third-party style dependency:
  - [hub.css](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/hub/hub.css) imports Google Fonts from `https://fonts.googleapis.com/...`
  - Inference: if this import remains, browsers will also fetch font files from `https://fonts.gstatic.com`
- Backend API connectivity:
  - [httpClient.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/shared/api/httpClient.ts) uses `fetch(...)`
  - [env.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/shared/config/env.ts) sources the backend origin from `VITE_API_BASE_URL`
  - Implication: a future CSP will need `connect-src` to include the configured backend origin explicitly
- Runtime theme/branding style assignment:
  - [main.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/main.tsx) sets CSS custom properties on `document.documentElement.style`, including the login hero background URL
  - This is not a third-party source, but it is the main area to re-test when tightening style-related CSP behavior

What was not found in the frontend source tree:

- no iframe/embed/object usage
- no analytics SDKs or tags such as Google Analytics, Hotjar, PostHog, Mixpanel, Segment, Intercom, Sentry, Stripe, Clerk, or Auth0
- no extra third-party script tags in `index.html`

## 2) Does a CSP already exist?

Yes, in report-only mode.

Current repo evidence:

- [vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json) defines:
  - canonical-host redirect
  - baseline security headers from Batch E
  - `Content-Security-Policy-Report-Only`
  - SPA rewrite
- The report-only policy starts from the requested baseline directives and adds the current justified allowances for:
  - backend HTTPS `connect-src`
  - Google Fonts
  - same-origin branding images
- [index.html](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/index.html) does not define a CSP meta tag
- No frontend runtime middleware/server layer exists in this Vite SPA repo that would inject CSP dynamically

Current implication:

- CSP is now versioned in repo as `Content-Security-Policy-Report-Only`
- Enforcing `Content-Security-Policy` still remains a future promotion step after Preview validation proves the current source list is clean

## 3) Current HTTPS and domain status relevant to HSTS

Current versioned host contract:

- [vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json) does not version a host redirect for the app; the current contract uses the single production app host `https://accmed.innovai-solutions.com.br`
- [DEPLOY.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/DEPLOY.md) treats `https://accmed.innovai-solutions.com.br` as the production custom domain for the AccMed app

Current operational status is not yet proven from repo evidence:

- [DEPLOY.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/DEPLOY.md) still treats custom-domain TLS as a hosted validation step, not a completed repo fact
- [frontend-deployment-readiness-checklist.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/frontend-deployment-readiness-checklist.md) still marks custom-domain TLS validation as pending host validation

Current implication:

- The repo defines the intended HTTPS host contract
- The repo does not prove that custom-domain HTTPS is already stable in production
- HSTS should remain deferred until the custom domain is attached, TLS is healthy, and the canonical host behavior is stable on the live deployment

## 4) Is HSTS already present anywhere?

No committed HSTS header was found.

Current repo evidence:

- [vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json) does not define `Strict-Transport-Security`
- No frontend meta-equivalent exists for HSTS
- Current docs mention HSTS only as future/out-of-scope work, not as an active header

Current implication:

- HSTS is not repo-versioned today
- Batch F keeps HSTS intentionally disabled until live HTTPS/domain stability is confirmed

## 5) Exact files likely affected by Batch F

Primary deploy config:

- [vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json)

Operator-facing docs likely needing alignment if the contract changes:

- [DEPLOY.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/DEPLOY.md)
- [client-launch-runbook.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md)
- [frontend-deployment-readiness-checklist.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/frontend-deployment-readiness-checklist.md)

Files that may be affected only if CSP is tightened beyond the current external dependencies:

- [hub.css](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/hub/hub.css) if Google Fonts is removed or self-hosted to avoid external `style-src` / font fetch allowances
- [main.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/main.tsx) only if CSP testing shows the runtime theme/style assignment needs adjustment

Files not expected for this batch:

- frontend business/runtime feature logic unrelated to asset loading
- backend CORS/runtime code
- unrelated security headers already handled in Batch E

## 6) Exact validation steps needed for Batch F

Config validation:

1. Confirm `frontend/vercel.json` remains valid JSON after CSP/HSTS changes:
   - `Get-Content frontend/vercel.json | ConvertFrom-Json | Out-Null`

Local/build sanity:

1. From `frontend/`, run:
   - `npm run test`
   - `VITE_DEPLOY_TARGET=client VITE_CLIENT_CODE=accmed VITE_API_BASE_URL=https://api-accmed.innovai-solutions.com.br VITE_APP_BASE_PATH=/ npm run build`
2. Confirm no new build or route-smoke regressions appear.

Preview validation before Production:

1. Deploy to Vercel Preview first.
2. Inspect the HTML response headers for:
   - `/`
   - `/login`
   - one deep route such as `/app/admin`
3. Confirm `Content-Security-Policy-Report-Only` is present and does not produce console violations for:
   - same-origin module bootstrap
   - branding images from `/branding/*`
   - backend API requests to the configured `VITE_API_BASE_URL`
   - the hub page font loading path if Google Fonts is still allowed
4. Visit the main route set and confirm no CSP-related console errors on:
   - `/`
   - `/login`
   - `/dashboard`
   - `/app/admin`
   - `/app/matriz-renovacao`
   - `/app/aluno`
5. If Google Fonts remains in use, confirm text on the hub page renders with the intended web fonts; if the font import is blocked, adjust CSP or remove the dependency before production
6. Confirm no frame/embed regressions are introduced, even though no frame integrations are currently expected

HSTS go-live validation:

1. Do not enable HSTS until:
   - `accmed.innovai-solutions.com.br` is attached and serving valid TLS
   - operators have validated the chosen app host on the live deployment
2. After those checks pass, confirm `Strict-Transport-Security` is present only on the live HTTPS custom domain response
3. Validate the final HSTS value carefully before any preload-style posture; this repo does not yet show evidence that such a posture is safe

Notes:

- Batch F has now introduced CSP carefully in report-only mode, starting from the actual current source list above rather than a generic template
- HSTS should remain off until the custom-domain HTTPS path is proven stable on the live host
