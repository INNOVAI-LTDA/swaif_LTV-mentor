# Story: Batch F - CSP (Careful Rollout) + HSTS (Gated on Stable HTTPS)

Status: review
Owner: dmene
Date: 2026-03-26

## Problem Statement

We need a Content Security Policy (CSP) to reduce XSS and content injection risk in the deployed SPA, but CSP can easily break brownfield apps if introduced abruptly (external fonts, inline styles, and unknown integrations).

We also want to enable HSTS, but only after verifying stable HTTPS on the final custom domain and canonical-host redirect behavior. Enabling HSTS too early can brick access if the domain configuration is still changing.

This batch introduces CSP carefully (report-only first if needed) and introduces HSTS only after explicit stability verification.

## Goal (Batch F Only)

1. Add a CSP with a safe rollout strategy:
   - Start in `Content-Security-Policy-Report-Only` mode if needed.
   - Iterate until the policy is compatible with current app behavior.
2. Use this baseline direction unless the repo requires a justified adjustment:
   - `default-src 'self';`
   - `base-uri 'self';`
   - `form-action 'self';`
   - `object-src 'none';`
   - `frame-ancestors 'none';`
   - `upgrade-insecure-requests`
3. Enable HSTS only after verifying stable HTTPS deployment on the custom domain:
   - Do not enable preload in this batch.

## Constraints / Guardrails (Binding)

- Keep diffs narrow; no opportunistic refactors.
- Do not mix cache work (Batch G).
- Preserve app behavior and existing architecture boundaries.
- Keep all frontend hosting headers centralized in `frontend/vercel.json` (as established in earlier batches).

## Current State (Evidence)

### CSP-relevant externals / behaviors

- External fonts: Google Fonts `@import` is present:
  - `frontend/src/features/hub/hub.css:1` imports `https://fonts.googleapis.com/...` and implies font loads from `https://fonts.gstatic.com`.
- Inline style usage exists in React components:
  - `frontend/src/shared/ui/ResourceStatePanel.tsx`
  - `frontend/src/features/student/pages/StudentPage.tsx`
  - `frontend/src/features/matrix/pages/MatrixPage.tsx`
  - `frontend/src/features/command-center/pages/CommandCenterPage.tsx`
  Strict `style-src` without `'unsafe-inline'` / nonces may break these.
- No iframe usage or analytics integrations were detected in a quick scan of `frontend/src`/`frontend/index.html`.

### Domain / HTTPS posture

- Domain/TLS confirmation is tracked as an operator decision (still pending in docs).
- No HSTS header is currently configured in repo.

## Scope

### In Scope (Exact Changes)

1. Add CSP headers in `frontend/vercel.json`:
   - Start with `Content-Security-Policy-Report-Only` to gather violations.
   - Add a controlled path to switch to enforced `Content-Security-Policy` once validated.
   - Include the baseline directives listed in the Goal.
2. Document the operational rollout in `DEPLOY.md`:
   - how to validate CSP report-only (where to look: browser console/devtools + any report endpoints if used)
   - when and how to switch from report-only to enforced
3. Add HSTS in `frontend/vercel.json` only after verification:
   - Document the exact verification prerequisites (custom domain, canonical host, stable HTTPS).
   - When enabling: use a conservative value (e.g., `max-age=15552000; includeSubDomains` only if appropriate), and explicitly avoid `preload`.

### Out of Scope (Explicit)

- Cache headers / cache strategy (Batch G).
- Any redirect/canonical host changes (Batch D).
- Backend CORS changes (Batch C).
- Major refactors to remove inline styles or external fonts unless required to meet CSP (prefer minimal adjustments; justify any change).
- CSP reporting endpoint implementation (only add if strictly needed and already supported by the platform; otherwise rely on console/devtools for first pass).

## Acceptance Criteria (Must Pass)

1. CSP is drafted, tested, and rolled out without breaking app behavior:
   - In report-only mode: no unexpected functional regressions; violations are identified and documented.
   - In enforce mode (when switched): core flows still work (login, protected navigation, data fetch, module pages).
2. HSTS is enabled only after stable HTTPS/domain verification:
   - `DEPLOY.md` contains an explicit checklist for “HSTS prerequisites satisfied”.
   - HSTS is not enabled prematurely.
3. Policy rollout is operationally clear:
   - `DEPLOY.md` tells the operator exactly how to validate and when to flip report-only -> enforce and when to enable HSTS.

## Implementation Notes (Smallest Safe Patch)

- CSP directives to consider beyond the baseline (only if needed by current app behavior):
  - `style-src`: may require `'self'` plus allowances for Google Fonts and/or inline styles.
  - `font-src`: may require `https://fonts.gstatic.com`.
  - `style-src` may require `https://fonts.googleapis.com`.
  - `connect-src`: must allow the backend API origin (`VITE_API_BASE_URL`) for deployed environments.
- Keep changes scoped to `frontend/vercel.json` + `DEPLOY.md` unless a concrete break requires a tiny code/css adjustment.
- If switching off Google Fonts is preferred to tighten CSP, do it as a separate explicitly scoped follow-up unless it is the smallest safe fix.

## Files / Modules Likely Affected

- Update: `frontend/vercel.json`
- Update: `DEPLOY.md`
- Optional (only if necessary to avoid breakage):
  - `frontend/src/features/hub/hub.css`
  - specific inline-style callsites listed above (replace with CSS classes)

## Tests / Validation

### Automated

- `cd frontend && npm run build`
- `cd frontend && npm run test`

### Manual (CSP)

1. Deploy with `Content-Security-Policy-Report-Only` enabled.
2. Open core flows:
   - `/login`
   - authenticate and open representative `/app/*` pages
3. Check for CSP violations:
   - browser console
   - DevTools Issues panel
4. Adjust policy (or minimal code) until violations are understood/acceptable.
5. Switch to enforced `Content-Security-Policy` and repeat checks.

### Manual (HSTS - gated)

Prerequisites:
- Custom domain connected and TLS active.
- Canonical host policy (www) verified with redirects.
- No mixed-content issues.

Verification:
- `curl -I https://www.yourdomain.com/` shows `Strict-Transport-Security: ...`
- Confirm no forced-HTTPS issues on apex -> www redirect path.

## Release Risks If Not Implemented

- Without CSP, the deployed SPA has a larger XSS/content injection blast radius.
- Enabling CSP without report-only iteration can break production unexpectedly (fonts/inline styles/connect-src).
- Enabling HSTS too early risks making the app inaccessible if domain/TLS/canonical redirect is still changing.

## Dev Agent Record

### Debug Log
- 2026-03-26: CSP report-only and HSTS gating documented in config/docs.

### Completion Notes
- Added CSP in report-only mode to `frontend/vercel.json` with allowances for Google Fonts, inline styles, and https connect targets; no HSTS header enabled by default.
- Documented in `DEPLOY.md` how to validate CSP, flip to enforcement, and when/how to add HSTS once domain/TLS is stable.

## File List
- `frontend/vercel.json`
- `DEPLOY.md`
- `_bmad-output/implementation-artifacts/batch-f-csp-report-only-and-hsts-gated.md`

## Change Log
- 2026-03-26: Batch F CSP (report-only) and gated HSTS instructions added.
