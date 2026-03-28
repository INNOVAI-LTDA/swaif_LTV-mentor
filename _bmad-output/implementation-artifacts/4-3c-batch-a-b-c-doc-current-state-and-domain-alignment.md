# Story 4.3c: batch-a-b-c-doc-current-state-and-domain-alignment

Status: review

## Story

As a release operator,
I want the Batch A/B/C documentation to reflect the current implemented Vercel and backend CORS contract,
so that brownfield deployment guidance no longer describes pre-implementation states or the wrong production host.

## Background (Why This Exists)

The implementation status of the deployment-hardening batches has moved forward, but several brownfield reference docs still describe older states:

- `docs/mvp-mentoria/vercel-batch-a-current-state.md` still says `frontend/vercel.json` does not exist.
- `docs/mvp-mentoria/vercel-batch-b-current-state.md` still says there is no SPA rewrite and that Vercel deep-link refreshes are expected to fail.
- `docs/client-launch-runbook.md` and `frontend/README.md` still contain operator-facing placeholder production origins such as `https://cliente.example.com`.
- `docs/mvp-mentoria/batch-c-backend-cors-current-state.md` is largely aligned with the current backend runtime, but it still uses generic hosted-domain examples rather than the real production domain contract now established for deploy docs.

These stale traces can mislead operators about current Vercel behavior, current CORS posture, and the real production hostname.

## Requirements

1. Refresh `docs/mvp-mentoria/vercel-batch-a-current-state.md` so it reflects the implemented Batch A contract:
   - `frontend/` is the deploy root
   - `VITE_APP_BASE_PATH=/` is the hosted contract
   - `frontend/vercel.json` exists
2. Refresh `docs/mvp-mentoria/vercel-batch-b-current-state.md` so it reflects the implemented Batch B contract:
   - SPA rewrites already exist in `frontend/vercel.json`
   - deep-link refresh is expected to work on Vercel for the documented routes
   - Preview/Production env examples now exist
   - `VITE_API_BASE_URL` is explicit for client builds
3. Align the production-facing documentation in:
   - `docs/mvp-mentoria/batch-c-backend-cors-current-state.md`
   - `frontend/README.md`
   - `docs/client-launch-runbook.md`
   to the real production domain contract:
   - apex: `https://innovai-solutions.com.br`
   - canonical host: `https://www.innovai-solutions.com.br`
4. Remove or rewrite wording that could mislead operators about the current Vercel/CORS state, especially wording that implies:
   - `frontend/vercel.json` is still missing
   - SPA rewrites are still pending
   - exact-origin-only CORS wording is the only valid deploy posture when regex support already exists
   - placeholder production domains are still the live operator contract

## Acceptance Criteria

1. `docs/mvp-mentoria/vercel-batch-a-current-state.md` no longer claims `frontend/vercel.json` is missing and clearly documents Batch A as implemented current state.
2. `docs/mvp-mentoria/vercel-batch-b-current-state.md` no longer claims SPA rewrites are absent or that deep-link refresh is expected to fail on Vercel.
3. `docs/mvp-mentoria/batch-c-backend-cors-current-state.md`, `frontend/README.md`, and `docs/client-launch-runbook.md` use `innovai-solutions.com.br` / `www.innovai-solutions.com.br` wherever they are describing the real production deploy contract rather than a generic placeholder.
4. Operator-facing CORS guidance no longer implies "exact-origin-only" as the sole valid posture when `CORS_ALLOW_ORIGIN_REGEX` is already part of the implemented runtime contract.
5. The change stays brownfield and documentation-only; no runtime code, `frontend/vercel.json`, or backend CORS logic is changed.

## Implementation Notes (Keep Diffs Narrow)

- Treat this as documentation correction, not a behavior change.
- Keep local-only examples if they are explicitly labeled as local-only.
- Generic examples are acceptable only when they are clearly marked as examples and not as the active production contract.
- Do not reopen Batch D redirect mechanics or Batch C runtime logic in this story.

## Files Likely Touched

- `docs/mvp-mentoria/vercel-batch-a-current-state.md`
- `docs/mvp-mentoria/vercel-batch-b-current-state.md`
- `docs/mvp-mentoria/batch-c-backend-cors-current-state.md`
- `frontend/README.md`
- `docs/client-launch-runbook.md`

## Tasks / Subtasks

### Task 1: Refresh Batch A Current-State Doc (AC: 1)

- [x] Update `docs/mvp-mentoria/vercel-batch-a-current-state.md` so it reflects the implemented Batch A repo state.
- [x] Remove stale wording that says `frontend/vercel.json` is absent.
- [x] Keep the scope limited to the current-state documentation for Batch A.

### Task 2: Refresh Batch B Current-State Doc (AC: 2)

- [x] Update `docs/mvp-mentoria/vercel-batch-b-current-state.md` so it reflects the implemented SPA rewrite and env-separation state.
- [x] Remove stale wording that says deep-link refreshes are expected to fail on Vercel.
- [x] Keep local `vite preview` caveats only if they still add value without contradicting the current hosted contract.

### Task 3: Align Production-Domain + CORS Operator Docs (AC: 3, 4)

- [x] Update `docs/mvp-mentoria/batch-c-backend-cors-current-state.md` to reference the real production domain where it is documenting the active hosted contract.
- [x] Update `frontend/README.md` so production-facing backend/CORS examples use the real production host or are explicitly marked generic.
- [x] Update `docs/client-launch-runbook.md` so production-facing backend/CORS examples align with the real deployed host and current regex-capable CORS contract.
- [x] Remove any wording that still implies exact-origin-only CORS is the only valid deploy posture when Preview regex support exists.

## Validation Steps

1. `rg -n "does not exist|no rewrites|expected to fail today|cliente\\.example\\.com|yourdomain\\.com" docs/mvp-mentoria/vercel-batch-a-current-state.md docs/mvp-mentoria/vercel-batch-b-current-state.md docs/mvp-mentoria/batch-c-backend-cors-current-state.md frontend/README.md docs/client-launch-runbook.md`
2. `rg -n "innovai-solutions\\.com\\.br|www\\.innovai-solutions\\.com\\.br|CORS_ALLOW_ORIGIN_REGEX" docs/mvp-mentoria/batch-c-backend-cors-current-state.md frontend/README.md docs/client-launch-runbook.md`
3. Review the updated Batch A/B current-state docs and confirm they describe the implemented repo state rather than a planned future state.

## Dev Agent Record

### Completion Notes

- Refreshed the stale Batch A and Batch B current-state docs so they describe the implemented Vercel root, SPA rewrite, and hosted env-example posture.
- Normalized production-facing frontend-origin and backend CORS examples to `innovai-solutions.com.br` where the docs are describing the active deploy contract.
- Kept the scope documentation-only; no runtime code, backend CORS logic, or `frontend/vercel.json` behavior changed.

## File List

- `docs/mvp-mentoria/vercel-batch-a-current-state.md`
- `docs/mvp-mentoria/vercel-batch-b-current-state.md`
- `docs/mvp-mentoria/batch-c-backend-cors-current-state.md`
- `frontend/README.md`
- `docs/client-launch-runbook.md`
- `_bmad-output/implementation-artifacts/4-3c-batch-a-b-c-doc-current-state-and-domain-alignment.md`

## Change Log

- Corrected stale pre-implementation Batch A/B snapshots.
- Aligned production-domain and CORS operator docs to the current hosted contract and preview-regex posture.
