# Story 4.4c: batch-d-accmed-subdomain-domain-contract-alignment (Batch D Follow-up)

Status: review

## Story

As a release operator,
I want the Vercel/app domain contract corrected from the current root-domain app assumption to the chosen AccMed client subdomain,
so that the versioned Vercel config, deploy docs, backend-origin examples, and smoke checks all point to the real target deployment model.

## Background (Why This Exists)

The current repo still assumes the hosted frontend app lives on the root domain contract introduced in the earlier Batch D correction:

- app host: `https://www.innovai-solutions.com.br`
- root-domain redirect: `https://innovai-solutions.com.br` -> `https://www.innovai-solutions.com.br`

That is no longer the chosen deployment model.

The confirmed AccMed target contract is now:

- frontend production host: `https://accmed.innovai-solutions.com.br`
- backend production API: `https://api-accmed.innovai-solutions.com.br`
- `VITE_APP_BASE_PATH=/`
- `VITE_CLIENT_CODE=accmed`

This means the current repo has stale domain guidance in multiple places:

1. [frontend/vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json) still version-controls a host redirect for the root domain app model (`innovai-solutions.com.br` -> `www.innovai-solutions.com.br`).
2. [DEPLOY.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/DEPLOY.md), [docs/client-launch-runbook.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md), and [frontend/README.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/README.md) still present the root-domain app host and generic backend API examples as the current operator-facing production contract.
3. Relevant current-state docs still reinforce the old root-domain or backend example posture:
   - [batch-c-backend-cors-current-state.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/batch-c-backend-cors-current-state.md)
   - [batch-d-custom-domain-redirects-current-state.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/batch-d-custom-domain-redirects-current-state.md)
   - [batch-f-csp-and-hsts-current-state.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md)

The smallest valid correction is still config/docs-only. No frontend runtime routing change, CSP/HSTS redesign, or backend CORS code change is required by this contract shift.

## Requirements

1. Update [frontend/vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json) so it no longer assumes the app is hosted at `innovai-solutions.com.br` -> `www.innovai-solutions.com.br`.
2. Keep the following unchanged in [frontend/vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json):
   - SPA rewrite
   - `trailingSlash=false`
   - existing Batch E security headers
   - existing Batch F `Content-Security-Policy-Report-Only`
3. Update operator-facing production examples so they use:
   - frontend production host: `https://accmed.innovai-solutions.com.br`
   - backend production API: `https://api-accmed.innovai-solutions.com.br`
   - backend `CORS_ALLOW_ORIGINS=https://accmed.innovai-solutions.com.br`
4. Remove or rewrite app-specific apex-to-`www` smoke checks so they no longer assume the app lives on the root domain.
5. Keep this config/docs-only unless implementation reveals a real runtime bug.

## Acceptance Criteria

1. The app canonical host is explicit as `https://accmed.innovai-solutions.com.br`.
2. The backend production API contract is explicit as `https://api-accmed.innovai-solutions.com.br`.
3. No stale operator guidance still points production app traffic to `https://www.innovai-solutions.com.br`.
4. Backend origin examples for production-like deploys use `CORS_ALLOW_ORIGINS=https://accmed.innovai-solutions.com.br`.
5. [frontend/vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json) no longer contains the old root-domain app redirect, while SPA rewrite and security-header behavior remain unchanged.
6. Diffs stay narrow and do not introduce runtime multi-tenant work, path-based tenanting, or unrelated security changes.

## Decision Lock (Do Not Reopen In Implementation)

- The target app host for this story is `https://accmed.innovai-solutions.com.br`, not the root domain and not `/app/accmed`.
- `VITE_APP_BASE_PATH` remains `/`; this is not a subpath deployment story.
- The root registered domain `innovai-solutions.com.br` may still exist for other uses, but it is no longer the app production host contract for AccMed.
- Unless a second app hostname is explicitly chosen later, do not replace the old root-domain redirect with a new `www`-style redirect for the subdomain. The safe immediate correction is to remove the old app-host redirect block that no longer matches the chosen deployment model.
- Preview behavior remains unchanged:
  - Preview frontend stays on `*.vercel.app`
  - Preview backend-origin guidance stays explicit via `CORS_ALLOW_ORIGIN_REGEX`

## Files Likely Touched

- [frontend/vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json)
- [DEPLOY.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/DEPLOY.md)
- [client-launch-runbook.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md)
- [README.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/README.md)
- [batch-c-backend-cors-current-state.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/batch-c-backend-cors-current-state.md)
- [batch-d-custom-domain-redirects-current-state.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/batch-d-custom-domain-redirects-current-state.md)
- [batch-f-csp-and-hsts-current-state.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md)

Potentially touched only if implementation finds they are still operator-facing and would mislead deployment setup:

- `frontend/.env.production.example`
- `frontend/.env.preview.example`

## Tasks / Subtasks

### Task 1: Remove The Old Root-Domain App Redirect From Vercel Config (AC: 1, 5)

- [x] Update [frontend/vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json) so it no longer contains the app redirect for `innovai-solutions.com.br` -> `www.innovai-solutions.com.br`.
- [x] Preserve:
  - `framework`
  - `buildCommand`
  - `outputDirectory`
  - `trailingSlash=false`
  - `headers`
  - `rewrites`
- [x] Do not invent a new canonical redirect unless a second app hostname is explicitly part of the chosen contract.

### Task 2: Align The Operator-Facing Deploy Contract (AC: 1, 2, 3, 4)

- [x] Update [DEPLOY.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/DEPLOY.md) so:
  - production frontend host examples use `https://accmed.innovai-solutions.com.br`
  - backend API examples use `https://api-accmed.innovai-solutions.com.br`
  - production-like backend origin examples use `CORS_ALLOW_ORIGINS=https://accmed.innovai-solutions.com.br`
  - app-specific apex-to-`www` checks are removed or rewritten for the subdomain model
- [x] Update [docs/client-launch-runbook.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md) with the same contract:
  - frontend origin
  - backend API URL
  - backend `CORS_ALLOW_ORIGINS`
  - hosted validation URLs
- [x] Update [frontend/README.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/README.md) so operator-facing examples no longer describe the root domain as the current production app host.

### Task 3: Align The Relevant Current-State Docs (AC: 2, 3, 4)

- [x] Update [batch-c-backend-cors-current-state.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/batch-c-backend-cors-current-state.md) so production and preview examples use the AccMed app subdomain as the stable frontend origin.
- [x] Update [batch-d-custom-domain-redirects-current-state.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/batch-d-custom-domain-redirects-current-state.md) so it no longer presents the root domain as the current app canonical-host contract.
- [x] Update [batch-f-csp-and-hsts-current-state.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md) so hosted-domain and HSTS-gate references use the AccMed subdomain contract.
- [x] If any additional current-state doc remains clearly release-facing and still points operators to the old root-domain app host, align it as part of this same narrow pass.

## Non-Goals / Guardrails

- Do not change frontend runtime routing or route definitions.
- Do not change `VITE_APP_BASE_PATH` away from `/`.
- Do not introduce path-based tenanting such as `/app/accmed`.
- Do not implement runtime multi-tenant branding.
- Do not change backend CORS code; this story is about config/docs alignment only.
- Do not redesign CSP, HSTS, cache strategy, or Preview architecture.

## Validation Steps

1. Confirm [frontend/vercel.json](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vercel.json) remains valid JSON:
   - `Get-Content frontend/vercel.json | ConvertFrom-Json | Out-Null`
2. Grep for stale root-domain app references in the touched deploy/operator docs:
   - `rg -n "www\\.innovai-solutions\\.com\\.br|innovai-solutions\\.com\\.br" frontend/vercel.json DEPLOY.md frontend/README.md docs/client-launch-runbook.md docs/mvp-mentoria`
3. Confirm the new AccMed contract is present:
   - `rg -n "accmed\\.innovai-solutions\\.com\\.br|api-accmed\\.innovai-solutions\\.com\\.br|CORS_ALLOW_ORIGINS=https://accmed\\.innovai-solutions\\.com\\.br" DEPLOY.md frontend/README.md docs/client-launch-runbook.md docs/mvp-mentoria`
4. Confirm no runtime or deploy-security files changed outside the intended config/docs scope.

## Developer Context / Guardrails

- Respect the existing production-hardening path already versioned in:
  - [DEPLOY.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/DEPLOY.md)
  - [frontend-deployment-readiness-checklist.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/frontend-deployment-readiness-checklist.md)
  - [batch-f-csp-and-hsts-current-state.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md)
- Keep Preview guidance intact where it already uses `*.vercel.app` plus regex-capable backend CORS.
- Treat the backend as a separate stateful host contract. The frontend app subdomain should point to Vercel, while the backend API contract points to `https://api-accmed.innovai-solutions.com.br`.
- If the implementation finds that operator-facing example env files are still misleading and are clearly part of the deploy contract, align them only as a minimal extension of this story and record that decision explicitly.

## Dev Agent Record

### Completion Notes

- Removed the obsolete root-domain app redirect from `frontend/vercel.json` and kept SPA rewrite, `trailingSlash=false`, baseline headers, and CSP report-only unchanged.
- Updated deploy/operator docs to make `https://accmed.innovai-solutions.com.br` the explicit production app host and `https://api-accmed.innovai-solutions.com.br` the explicit production backend API.
- Rewrote app-host smoke checks so they validate the chosen AccMed subdomain directly instead of assuming root-domain apex-to-`www` behavior.
- Extended the patch narrowly to `frontend/.env.production.example` because it remained an operator-facing production template with stale `api.example.com` guidance.

## File List

- `frontend/vercel.json`
- `DEPLOY.md`
- `docs/client-launch-runbook.md`
- `frontend/README.md`
- `docs/mvp-mentoria/batch-c-backend-cors-current-state.md`
- `docs/mvp-mentoria/batch-d-custom-domain-redirects-current-state.md`
- `docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md`
- `frontend/.env.production.example`
- `_bmad-output/implementation-artifacts/4-4c-batch-d-accmed-subdomain-domain-contract-alignment.md`

## Change Log

- Created follow-up story to move the app domain contract from the root-domain model to the AccMed client subdomain model without reopening runtime architecture.
- Implemented the config/docs-only alignment for the AccMed subdomain production contract.
