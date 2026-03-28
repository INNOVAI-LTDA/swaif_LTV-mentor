# Batch E (Frontend Security Headers) - Current State (Brownfield)

Date: 2026-03-27
Scope: document only the current repo state relevant to Batch E:

- enable baseline frontend security headers

This is intentionally narrow and does not attempt to document the full project.

## 1) Does `frontend/vercel.json` already define headers?

Yes.

Current [frontend/vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json) defines only:

- framework/build/output settings
- `trailingSlash=false`
- apex-to-`www` redirect
- baseline frontend security headers
- SPA rewrite to `/index.html`

The committed `headers` block currently sets:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-Frame-Options: DENY`
- `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()`

## 2) Are baseline frontend security headers partially present?

Yes, as versioned frontend deploy config.

Current repo evidence:

- [frontend/vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json) includes a committed Vercel `headers` block for the baseline Batch E header set.
- [DEPLOY.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/DEPLOY.md) now expects those headers during hosted smoke validation on Preview and Production.
- No frontend-side middleware, proxy, or server layer exists in this Vite SPA repo that would inject response headers at runtime.

Implication:

- The baseline Batch E headers are now version-controlled in the repo.
- The hosting platform may still add extra headers, but the baseline header contract no longer depends on external-only defaults.

## 3) Is there any apparent conflict with current asset loading or browser behavior?

No direct conflict is visible for Batch E baseline headers.

Current frontend behavior relevant to header safety:

- Static assets are served from the Vite build output under `dist/`.
- The app is a client-side React SPA with a Vercel rewrite to `/index.html`.
- API calls are made cross-origin to the backend, but baseline response headers on the frontend host do not change that request model.

For Batch E, the low-risk header set is expected to be things like:

- `X-Content-Type-Options`
- `X-Frame-Options`
- `Referrer-Policy`
- a minimal `Permissions-Policy`

These do not inherently conflict with:

- Vite module asset loading
- the current SPA rewrite
- browser refresh on nested routes

Known caution:

- CSP is not part of Batch E and should not be mixed in here; that is the first header family likely to affect script/style/image loading.
- HSTS is also out of scope for Batch E and should remain deferred.

## 4) Exact files likely affected by Batch E

Direct config:

- [frontend/vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json)

Operator-facing docs aligned to the current contract:

- [DEPLOY.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/DEPLOY.md)

Files not expected for this batch:

- frontend runtime code
- backend CORS/runtime code
- CSP/HSTS-specific docs or config

## 5) Exact validation steps needed for Batch E

Config validation:

1. Confirm `frontend/vercel.json` remains valid JSON after adding headers:
   - `Get-Content frontend/vercel.json | ConvertFrom-Json | Out-Null`

Local/build sanity:

1. From `frontend/`, run:
   - `npm run test`
   - `VITE_DEPLOY_TARGET=client VITE_CLIENT_CODE=accmed VITE_API_BASE_URL=https://api.example.com VITE_APP_BASE_PATH=/ npm run build`
2. Confirm no new asset-loading or route-smoke regressions appear during the build/test pass.

Hosted validation:

1. Deploy to Vercel Preview first.
2. On both Preview and Production, inspect the response headers for:
   - `/`
   - `/login`
   - one rewritten deep route such as `/app/admin`
3. Confirm the expected baseline headers are present on the HTML response.
4. Confirm browser console shows no new asset, script, or frame-related errors.
5. Confirm SPA refresh still works on:
   - `/`
   - `/login`
   - `/dashboard`
   - `/app/admin`
   - `/app/matriz-renovacao`
   - `/app/aluno`
6. Confirm API requests still target the intended backend and are unaffected by the frontend-host header change.

Notes:

- Batch E should stop at baseline headers only.
- CSP belongs to Batch F.
- HSTS should remain deferred until domain stability is confirmed.
