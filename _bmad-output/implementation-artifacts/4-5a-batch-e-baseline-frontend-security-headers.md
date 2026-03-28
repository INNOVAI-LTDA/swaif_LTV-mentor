# Story 4.5a: batch-e-baseline-frontend-security-headers

Status: review

## Story

As a release operator,
I want baseline frontend security headers versioned in `frontend/vercel.json`,
so that the first stable Vercel deployment has a minimal hardening layer without mixing in CSP or HSTS.

## Requirements

1. Enable baseline frontend security headers in `frontend/vercel.json`:
   - `X-Content-Type-Options: nosniff`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `X-Frame-Options: DENY`
   - `Permissions-Policy` denying unused capabilities
2. Keep the change narrow and deployment-focused.
3. Do not mix CSP or HSTS into this batch.
4. Update operator-facing docs only where the deployment contract changes.

## Acceptance Criteria

1. Baseline headers are active in Production via `frontend/vercel.json`.
2. Header behavior is documented where needed for the operator.
3. No unrelated security hardening is mixed in.

## Files Likely Touched

- `frontend/vercel.json`
- `DEPLOY.md`

## Tasks / Subtasks

### Task 1: Add Baseline Headers To Vercel Config (AC: 1, 3)

- [x] Add a `headers` block to `frontend/vercel.json`.
- [x] Include `X-Content-Type-Options: nosniff`.
- [x] Include `Referrer-Policy: strict-origin-when-cross-origin`.
- [x] Include `X-Frame-Options: DENY`.
- [x] Include a minimal `Permissions-Policy` denying unused capabilities.
- [x] Keep CSP and HSTS out of the config.

### Task 2: Update Operator Contract (AC: 2)

- [x] Update `DEPLOY.md` so the hosted smoke checklist reflects that baseline headers are now expected from repo-configured deploy behavior.

## Validation Steps

1. `Get-Content frontend/vercel.json | ConvertFrom-Json | Out-Null`
2. `cd frontend`
3. `VITE_DEPLOY_TARGET=client VITE_CLIENT_CODE=accmed VITE_API_BASE_URL=https://api.example.com VITE_APP_BASE_PATH=/ npm run build`

## Dev Agent Record

### Completion Notes

- Added a narrow baseline `headers` block to `frontend/vercel.json`.
- Updated `DEPLOY.md` so the operator smoke checklist expects the repo-configured baseline headers.
- Kept CSP and HSTS out of scope.

## File List

- `frontend/vercel.json`
- `DEPLOY.md`
- `_bmad-output/implementation-artifacts/4-5a-batch-e-baseline-frontend-security-headers.md`

## Change Log

- Added baseline frontend security headers in `frontend/vercel.json`.
- Updated deployment smoke guidance for Batch E.
