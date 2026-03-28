# Story 4.5b: batch-e-current-state-doc-refresh-after-review

Status: review

## Story

As a release operator,
I want the Batch E current-state documentation to match the now-implemented frontend security-header config,
so that the brownfield reference doc no longer contradicts the repo state after Batch E landed.

## Background (Why This Exists)

Batch E is now implemented in repo:

- `frontend/vercel.json` contains a committed `headers` block
- baseline frontend security headers are versioned in Git
- `DEPLOY.md` expects those headers during hosted smoke validation

However, `docs/mvp-mentoria/batch-e-frontend-security-headers-current-state.md` still describes the pre-implementation state:

- it says `frontend/vercel.json` does not define headers
- it says no committed `headers` section exists
- it says any current headers are external/platform-provided only

That makes the current-state reference doc inaccurate and creates operator confusion during the release-hardening workflow.

## Requirements

1. Refresh `docs/mvp-mentoria/batch-e-frontend-security-headers-current-state.md` so it reflects the implemented Batch E state:
   - `frontend/vercel.json` now has a committed `headers` block
   - baseline headers are repo-versioned, not only platform-provided
   - `DEPLOY.md` now expects those headers in hosted smoke validation
2. Keep the change documentation-only.
3. Do not modify runtime code, frontend config, or broader security policy in this follow-up.

## Acceptance Criteria

1. `docs/mvp-mentoria/batch-e-frontend-security-headers-current-state.md` no longer claims that `frontend/vercel.json` lacks headers.
2. The same doc no longer claims baseline headers are only external/platform-provided.
3. The same doc explicitly reflects that `DEPLOY.md` now treats the baseline headers as expected hosted smoke behavior.
4. No runtime or config changes are introduced beyond the doc correction.

## Implementation Notes (Keep Diffs Narrow)

- Treat this as a brownfield doc refresh only.
- Preserve the existing scope boundaries:
  - Batch E = baseline headers
  - Batch F = CSP/HSTS
- Keep the validation section aligned with the already-implemented repo state.

## Files Likely Touched

- `docs/mvp-mentoria/batch-e-frontend-security-headers-current-state.md`

## Tasks / Subtasks

### Task 1: Refresh Batch E Current-State Snapshot (AC: 1, 2, 3)

- [x] Update `docs/mvp-mentoria/batch-e-frontend-security-headers-current-state.md` so it reflects the implemented `headers` block in `frontend/vercel.json`.
- [x] Replace the stale wording that says baseline headers are only platform-provided.
- [x] Note that `DEPLOY.md` now expects those headers as part of hosted smoke validation.

### Task 2: Preserve Scope Discipline (AC: 4)

- [x] Keep the follow-up documentation-only.
- [x] Do not change `frontend/vercel.json`, runtime code, or broader security configuration.

## Validation Steps

1. `rg -n "does not define headers|There is no committed `headers` section yet|platform-provided only|if already configured on the deployment" docs/mvp-mentoria/batch-e-frontend-security-headers-current-state.md`
2. Review the updated doc and confirm it matches:
   - `frontend/vercel.json`
   - `DEPLOY.md`
3. Confirm no files outside the Batch E current-state doc were changed.

## Dev Agent Record

### Completion Notes

- Refreshed the Batch E current-state doc so it now reflects the committed `headers` block in `frontend/vercel.json`.
- Updated the doc to state that baseline headers are repo-versioned and expected during hosted smoke validation via `DEPLOY.md`.
- Kept the follow-up documentation-only with no runtime or config changes.

## File List

- `docs/mvp-mentoria/batch-e-frontend-security-headers-current-state.md`
- `_bmad-output/implementation-artifacts/4-5b-batch-e-current-state-doc-refresh-after-review.md`

## Change Log

- Corrected the Batch E current-state snapshot to match the implemented frontend security-header contract.
