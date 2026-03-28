# Story 4.6a: batch-f-csp-report-only-and-hsts-gating (Batch F)

Status: review

## Story

As a release operator,
I want Batch F to introduce a careful Content Security Policy rollout and defer HSTS until the custom domain is proven stable over HTTPS,
so that browser hardening improves without breaking the deployed SPA or prematurely locking the domain into an unsafe transport policy.

## Background (Current State Snapshot)

- [frontend/vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json) currently includes:
  - canonical-host redirect
  - baseline security headers from Batch E
  - `Content-Security-Policy-Report-Only` from Batch F
  - SPA rewrite
- `Content-Security-Policy-Report-Only` is now committed in `frontend/vercel.json`; `Strict-Transport-Security` remains intentionally absent pending live HTTPS/domain verification.
- The current frontend CSP-relevant source list is narrow:
  - same-origin module bootstrap from [index.html](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/index.html)
  - same-origin branding assets from [public](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/public)
  - backend API requests driven by `VITE_API_BASE_URL` via [httpClient.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/shared/api/httpClient.ts)
  - Google Fonts CSS import in [hub.css](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/hub/hub.css)
- The custom-domain contract is versioned for `https://www.innovai-solutions.com.br`, but current docs still treat live TLS/domain stability as a hosted validation step, not a proven fact.

Source: [batch-f-csp-and-hsts-current-state.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md).

## Requirements (Batch F)

1. Add Content Security Policy carefully.
2. Start with report-only mode if needed.
3. Use this baseline direction unless the repo requires a justified adjustment:
   - `default-src 'self';`
   - `base-uri 'self';`
   - `form-action 'self';`
   - `object-src 'none';`
   - `frame-ancestors 'none';`
   - `upgrade-insecure-requests`
4. Enable HSTS only after verifying stable HTTPS deployment on the custom domain.
5. Do not rush into preload.

## Acceptance Criteria

1. CSP is drafted, tested, and rolled out without breaking app behavior.
2. Any deviation from the baseline direction is explicitly justified by current repo dependencies.
3. HSTS is enabled only after stable HTTPS/domain verification is complete.
4. Policy rollout is operationally clear in the operator docs.

## Decisions (Lock Before Implementing)

- Recommended rollout posture:
  - Start with `Content-Security-Policy-Report-Only` if the team has not yet validated the current source list on Vercel Preview.
  - Promote to enforcing `Content-Security-Policy` only after Preview validation shows no real violations for the active routes.
- Current justified CSP adjustments already implied by the repo:
  - `connect-src` must allow the configured backend origin from `VITE_API_BASE_URL`
  - `style-src` / font-related allowances may be needed while [hub.css](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/hub/hub.css) still imports Google Fonts
  - `img-src` should continue to allow same-origin branding assets
- HSTS must remain out of the first CSP rollout unless live custom-domain HTTPS has already been verified by the operator.
- Do not add `preload` in this batch.

## Tasks / Subtasks

### Task 1: Add A Careful CSP Rollout In `frontend/vercel.json` (AC: 1, 2)

- [x] Update [frontend/vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json) to add a CSP header entry.
- [x] Prefer `Content-Security-Policy-Report-Only` first if Preview safety is not yet proven.
- [x] Start from the requested baseline directives:
  - `default-src 'self'`
  - `base-uri 'self'`
  - `form-action 'self'`
  - `object-src 'none'`
  - `frame-ancestors 'none'`
  - `upgrade-insecure-requests`
- [x] Add only the smallest justified extra directives/sources required by the current repo:
  - backend API origin for `connect-src`
  - Google Fonts allowances only if the existing font import is kept
  - same-origin branding/image/module behavior
- [x] Keep the SPA rewrite, redirect rules, and Batch E headers intact.

Notes:
- Do not paste a generic CSP template without reconciling it to the current source list.
- If the developer chooses to avoid external font allowances, the justified alternative is to remove or replace the Google Fonts dependency in scope, not to loosen unrelated directives.

### Task 2: Keep HSTS Explicitly Gated (AC: 3)

- [x] Do not enable `Strict-Transport-Security` unless live hosted verification confirms:
  - custom domain is attached
  - TLS is healthy on `https://www.innovai-solutions.com.br`
  - apex-to-`www` redirect is stable
- [x] If those hosted checks are not available during implementation, document HSTS as pending and leave it disabled in repo.
- [x] If those hosted checks are not available, do not add `preload`.

### Task 3: Update Operator Docs For Rollout Clarity (AC: 4)

- [x] Update [DEPLOY.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/DEPLOY.md) with:
  - whether CSP is currently report-only or enforced
  - which routes/responses must be checked for violations
  - the explicit gate before HSTS can be turned on
- [x] Update [docs/client-launch-runbook.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md) because it remains the operator source of truth for hosted validation.
- [x] Keep cache strategy and unrelated security work out of this batch.

## Non-Goals / Guardrails

- Do not mix cache work into this batch.
- Do not broaden the change into backend CORS, routing, or branding cleanup.
- Do not introduce CSP `preload` assumptions or HSTS preload submission steps.
- Do not weaken existing Batch E headers while adding CSP/HSTS.

## Files Likely Touched

- [frontend/vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json)
- [DEPLOY.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/DEPLOY.md)
- [docs/client-launch-runbook.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md) only if needed for operator clarity

Potentially touched only if CSP tightening requires removing the one current external dependency:

- [hub.css](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/hub/hub.css)

## Validation Steps

Repo-level:

1. Confirm [frontend/vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json) remains valid JSON:
   - `Get-Content frontend/vercel.json | ConvertFrom-Json | Out-Null`
2. From `frontend/`, run:
   - `npm run test`
   - `VITE_DEPLOY_TARGET=client VITE_CLIENT_CODE=accmed VITE_API_BASE_URL=https://api.example.com VITE_APP_BASE_PATH=/ npm run build`

Preview validation:

1. Deploy to Vercel Preview first.
2. Inspect response headers for:
   - `/`
   - `/login`
   - `/app/admin`
3. Confirm CSP is present in the expected mode:
   - `Content-Security-Policy-Report-Only` if starting in report-only
   - or `Content-Security-Policy` if enforcement is justified and already validated
4. Check browser console for CSP violations on:
   - `/`
   - `/login`
   - `/dashboard`
   - `/app/admin`
   - `/app/matriz-renovacao`
   - `/app/aluno`
5. Confirm:
   - same-origin branding assets still load
   - backend API calls to the configured origin still work
   - the hub page fonts still render correctly, or the external font dependency was intentionally removed

Production / HSTS gate:

1. Validate the custom domain on the live host:
   - `https://www.innovai-solutions.com.br` serves valid TLS
   - `https://innovai-solutions.com.br` redirects cleanly to `https://www.innovai-solutions.com.br`
2. Only after that, decide whether enabling `Strict-Transport-Security` is safe.
3. If enabled, confirm:
   - it appears only on the live HTTPS custom domain response
   - the value is conservative
   - `preload` is absent

Current release-readiness note:

- Batch F is implemented, but it is not deployment-ready while `npm run test` remains red in the frontend release gate.
- Resolve that gate in a separate narrow batch, or record an explicit waiver outside this story in the release tracker before presenting Batch F as ready to deploy.

## Dev Agent Record

### Completion Notes

- Added `Content-Security-Policy-Report-Only` to `frontend/vercel.json` using the requested baseline directives plus only the current repo-justified allowances for backend HTTPS connectivity, Google Fonts, runtime inline style usage, and same-origin assets.
- Left `Strict-Transport-Security` disabled and documented the live HTTPS/domain gate before any future HSTS enablement.
- Updated the operator-facing deploy docs and refreshed the Batch F current-state snapshot so the repo documentation now matches the implemented rollout posture.
- Batch F remains blocked for deploy-readiness until the frontend `npm run test` gate is fixed in a separate narrow batch or explicitly waived outside this story.

## File List

- `frontend/vercel.json`
- `DEPLOY.md`
- `docs/client-launch-runbook.md`
- `docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md`
- `_bmad-output/implementation-artifacts/4-6a-batch-f-csp-report-only-and-hsts-gating.md`

## Change Log

- Added Batch F CSP rollout in report-only mode.
- Kept HSTS disabled and explicitly gated behind live custom-domain HTTPS verification.
- Updated operator docs to reflect the new CSP validation contract.
