# Story 4.4b: batch-d-domain-contract-correction (Batch D Follow-up)

Status: review

## Story

As a release operator,
I want the Batch D production-domain contract to use the real Vercel app domain (`innovai-solutions.com.br`) instead of the client's own site domain,
so that canonical-host redirects, smoke checks, and deploy instructions point to the correct production host.

## Background (Why This Exists)

Batch D versioned a canonical-host policy and deploy smoke checklist, but it mistakenly assumed the production domain was:

- `https://aceleradormedico.com.br`
- `https://www.aceleradormedico.com.br`

That domain belongs to the client site and must not be treated as the hosted Vercel app domain.

The correct canonical production domain for the Vercel deployment is:

- apex: `https://innovai-solutions.com.br`
- canonical host: `https://www.innovai-solutions.com.br`

The only repo source that mentions `aceleradormedico.com.br` is the client branding reference in `docs/branding/design-system-acelerador-medico.md`, which should be treated as a branding/site reference only, not as deploy-host truth.

## Requirements

1. Replace the mistaken production-domain assumption in:
   - `frontend/vercel.json`
   - `DEPLOY.md`
   - `docs/client-launch-runbook.md`
2. Update all apex-to-www smoke URLs to:
   - `https://innovai-solutions.com.br`
   - `https://www.innovai-solutions.com.br`
3. Add one explicit operator-facing note that `docs/branding/design-system-acelerador-medico.md` is a client-site branding reference only, not the deploy-host source of truth.
4. Keep the correction narrow and do not mix in CSP/HSTS or unrelated deploy changes.

## Acceptance Criteria

1. `frontend/vercel.json` redirects apex `innovai-solutions.com.br` to canonical `www.innovai-solutions.com.br` with a permanent redirect and preserved path/query string.
2. `DEPLOY.md` uses only the `innovai-solutions.com.br` / `www.innovai-solutions.com.br` pair for Batch D production-domain examples and smoke steps.
3. `docs/client-launch-runbook.md` uses only the corrected Batch D production-domain assumption in its canonical-host validation section.
4. At least one operator-facing doc explicitly says `docs/branding/design-system-acelerador-medico.md` is not the deploy-host source of truth.
5. No CSP/HSTS or unrelated Batch E/F work is introduced in this correction.

## Files Likely Touched

- `frontend/vercel.json`
- `DEPLOY.md`
- `docs/client-launch-runbook.md`

Optional, only if the implementation needs one extra explicit note outside the deploy docs:

- `docs/branding/design-system-acelerador-medico.md`

## Tasks / Subtasks

### Task 1: Correct the Versioned Redirect Contract (AC: 1)

- [x] Update `frontend/vercel.json` so the host matcher uses `innovai-solutions.com.br`.
- [x] Update the redirect destination to `https://www.innovai-solutions.com.br/:path*`.
- [x] Keep the existing SPA rewrite intact.
- [x] Keep `trailingSlash=false` unchanged unless a separate issue is found.

### Task 2: Correct the Deploy Contract Docs (AC: 2, 3)

- [x] Update `DEPLOY.md` to replace all Batch D production-domain examples and smoke URLs from the AccMed domain to the InnovAI Solutions domain.
- [x] Update `docs/client-launch-runbook.md` to replace the Batch D canonical-host section and its apex-to-www validation URLs with the InnovAI Solutions domain.

### Task 3: Clarify the Branding Reference Boundary (AC: 4)

- [x] Add one explicit note in the deploy contract docs that `docs/branding/design-system-acelerador-medico.md` is a branding/site reference only.
- [x] Make it clear that production-domain truth for Batch D comes from the deployment contract, not from branding references.

## Non-Goals / Guardrails

- Do not add CSP, HSTS, or broader security-header changes.
- Do not change backend CORS behavior in this correction.
- Do not refactor unrelated docs or runtime config.
- Do not change Preview-domain behavior; this correction is only about the production custom-domain assumption.

## Validation Steps

1. Confirm `frontend/vercel.json` remains valid JSON.
2. Grep for stale references:
   - `rg -n "aceleradormedico\\.com\\.br|www\\.aceleradormedico\\.com\\.br" frontend/vercel.json DEPLOY.md docs/client-launch-runbook.md`
3. Confirm the corrected references exist:
   - `rg -n "innovai-solutions\\.com\\.br|www\\.innovai-solutions\\.com\\.br" frontend/vercel.json DEPLOY.md docs/client-launch-runbook.md`

## Dev Agent Record

### Completion Notes

- Corrected the Batch D production-domain contract from the client site domain to the Vercel app domain in `frontend/vercel.json`, `DEPLOY.md`, and `docs/client-launch-runbook.md`.
- Preserved the existing SPA rewrite and kept `trailingSlash=false` unchanged.
- Added operator-facing notes clarifying that `docs/branding/design-system-acelerador-medico.md` is a branding reference only, not deploy-host truth.

## File List

- `frontend/vercel.json`
- `DEPLOY.md`
- `docs/client-launch-runbook.md`
- `_bmad-output/implementation-artifacts/4-4b-batch-d-domain-contract-correction.md`

## Change Log

- Replaced the mistaken Batch D production-domain assumption with `innovai-solutions.com.br` / `www.innovai-solutions.com.br`.
- Updated apex-to-www validation URLs and canonical-host wording in operator docs.
