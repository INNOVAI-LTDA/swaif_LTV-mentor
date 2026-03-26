# Story: Batch E - Baseline Frontend Security Headers (Vercel)

Status: review
Owner: dmene
Date: 2026-03-26

## Problem Statement

The frontend is a Vite SPA intended for stable deployment on Vercel. Today there is no committed `frontend/vercel.json`, and therefore no versioned, environment-independent security header baseline. This creates avoidable risk: browsers may accept risky defaults (MIME sniffing, permissive referrer behavior, unwanted feature permissions) unless we explicitly set a safe baseline.

Batch E adds only the baseline security headers requested, without mixing in CSP or HSTS.

## Goal (Batch E Only)

Enable baseline frontend security headers via `frontend/vercel.json`:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-Frame-Options: DENY`
- `Permissions-Policy` denying unused capabilities

## Constraints / Guardrails (Binding)

- Keep diffs narrow; no opportunistic refactors.
- Do not mix in CSP or HSTS (Batch F).
- Do not change routing, env contract, rewrites, redirects, or cache strategy in this batch.
- Preserve app behavior outside header configuration.

## Current State (Evidence)

- No `frontend/vercel.json` exists today; headers are not versioned in repo.
- No other header-config mechanism exists for the frontend build artifacts in this repo.

## Scope

### In Scope (Exact Changes)

1. Update `frontend/vercel.json` (created in Batch A) to define `headers` rules that apply to:
   - the SPA shell (`/` and deep routes served as `index.html`)
   - static assets under the deployed base path (ensure the rule matches the deployed structure)
2. Add a short operator-facing note (only if needed) in `DEPLOY.md`:
   - how to verify headers via `curl -I`
   - expected header values

### Out of Scope (Explicit)

- `Content-Security-Policy` (Batch F).
- `Strict-Transport-Security` / HSTS (Batch F; only after stable custom domain HTTPS).
- Cross-origin isolation headers (COOP/COEP/CORP) unless explicitly requested.
- Any redirect/rewrite changes (Batches B/D).
- Any cache header policy (Batch G).

## Acceptance Criteria (Must Pass)

1. Baseline headers are active in Production via `frontend/vercel.json`:
   - `X-Content-Type-Options: nosniff`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `X-Frame-Options: DENY`
   - `Permissions-Policy` present and denies unused capabilities
2. Header behavior is documented if needed:
   - `DEPLOY.md` includes a short verification snippet/commands (or references a stable place if already documented).
3. No unrelated security hardening is mixed in:
   - No CSP.
   - No HSTS.
   - No other header additions beyond the baseline list above.

## Implementation Notes (Smallest Safe Patch)

- Apply headers broadly (typically `source: "/(.*)"`) so they cover both `index.html` and static assets consistently under Vercel.
- Use a conservative `Permissions-Policy` that disables capabilities we do not use. Example policy (to confirm during implementation):
  - `camera=()`, `microphone=()`, `geolocation=()`, `payment=()`, `usb=()`, `bluetooth=()`, `serial=()`, `hid=()`, `fullscreen=(self)` (only if needed), etc.
- Note: `X-Frame-Options: DENY` will prevent embedding in iframes. If the product requires embedding later, this must be revisited as an explicit requirement.

## Files / Modules Likely Affected

- Update: `frontend/vercel.json`
- Optional update: `DEPLOY.md`

## Tests / Validation

No unit tests expected (host config). Validate operationally:

1. Deploy to Vercel Production.
2. Verify headers:
   - `curl -I https://www.yourdomain.com/`
   - `curl -I https://www.yourdomain.com/assets/<some-hash>.js`
3. Browser sanity:
   - Load the app and confirm no console errors caused by headers.

## Release Risks If Not Implemented

- Missing baseline hardening leaves room for content-type sniffing and unnecessary browser feature permissions.
- Unversioned header configuration increases drift risk between Preview and Production deployments.

## Dev Agent Record

### Debug Log
- 2026-03-26: security headers configured via `frontend/vercel.json`.

### Completion Notes
- Added baseline security headers (nosniff, strict referrer, DENY framing, restrictive Permissions-Policy) to `frontend/vercel.json` applying to all routes/assets.
- Documented header verification steps in `DEPLOY.md`.

## File List
- `frontend/vercel.json`
- `DEPLOY.md`
- `_bmad-output/implementation-artifacts/batch-e-baseline-security-headers.md`

## Change Log
- 2026-03-26: Batch E baseline security headers documented and configured.
