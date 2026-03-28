# Story 4.3d: batch-c-canonical-cors-and-preview-evidence-fix

Status: review

## Story

As a release operator,
I want the Batch C docs and backend startup evidence to align with the canonical production host and the implemented Preview-regex contract,
so that the backend/frontend origin contract is both minimal and verifiable during deployment.

## Background (Why This Exists)

The current deploy docs are closer to the intended contract, but two concrete gaps remain:

1. Production CORS examples still allow both:
   - `https://www.innovai-solutions.com.br`
   - `https://innovai-solutions.com.br`

That no longer matches the current Batch D deployment reality, where:

- `https://www.innovai-solutions.com.br` is the canonical frontend host
- `https://innovai-solutions.com.br` is only the redirecting apex

For Batch C operator examples, apex should remain part of redirect validation, not part of the backend CORS allowlist examples.

2. Preview CORS guidance is documented, but backend startup evidence still does not expose `cors_origin_regex`, which means operators cannot prove from startup logs/runtime summary that the Preview regex was actually loaded.

The smallest coherent fix is to:

- standardize production CORS examples to the canonical `www` origin only
- add one normal Preview backend startup example that is separate from the mentor-demo approval posture
- surface `cors_origin_regex` in backend runtime summary and startup logging

This keeps the docs strong and makes the verification path real instead of softening the wording.

## Requirements

1. Standardize production CORS examples to canonical `https://www.innovai-solutions.com.br` only in:
   - `docs/mvp-mentoria/batch-c-backend-cors-current-state.md`
   - `frontend/README.md`
   - `docs/client-launch-runbook.md`
2. Keep apex `https://innovai-solutions.com.br` only in redirect/canonical-host checks, not in backend CORS allowlist examples.
3. In `docs/client-launch-runbook.md`, add one normal Preview backend startup example using:
   - `ENABLE_MENTOR_DEMO_ROUTES=false`
   - `CORS_ALLOW_ORIGINS=https://www.innovai-solutions.com.br`
   - `CORS_ALLOW_ORIGIN_REGEX=^https://.*\\.vercel\\.app$`
4. Keep the existing mentor-demo approval example separate from the normal Preview example.
5. Implement the runtime-summary evidence fix in `backend/app/main.py` so `cors_origin_regex` is surfaced in:
   - `app.state.runtime_summary`
   - `backend_runtime_configured` log line
   - `backend_startup_complete` log line
6. Extend backend runtime tests so the regex is asserted in surfaced runtime evidence.

## Acceptance Criteria

1. Production CORS examples in the three operator/docs files use only `https://www.innovai-solutions.com.br` for backend allowlist examples.
2. Apex `https://innovai-solutions.com.br` remains present only in redirect/canonical-host checks, not as a required backend browser origin.
3. `docs/client-launch-runbook.md` contains:
   - one normal Preview backend startup example with `ENABLE_MENTOR_DEMO_ROUTES=false`
   - one separate mentor-demo approval example
4. `backend/app/main.py` exposes `cors_origin_regex` in `app.state.runtime_summary`.
5. Both startup log lines include the regex value (or an explicit empty/none representation).
6. `backend/tests/test_runtime_config.py` asserts the surfaced regex value.
7. No frontend runtime behavior, Vercel routing, or CORS enforcement semantics change beyond evidence/doc alignment.

## Implementation Notes (Keep Diffs Narrow)

- Prefer the runtime-summary fix over softening the docs. The docs already assume deploy verification; make the runtime evidence catch up.
- Do not change `frontend/vercel.json` in this follow-up.
- Do not expand or tighten backend origin-matching logic beyond what already exists.
- Keep Preview regex examples tied to normal hosted Preview behavior, not to mentor-demo exceptions.
- Use ASCII in new/rewritten prose unless the target file already uses Portuguese diacritics consistently.

## Files Likely Touched

- `docs/mvp-mentoria/batch-c-backend-cors-current-state.md`
- `frontend/README.md`
- `docs/client-launch-runbook.md`
- `backend/app/main.py`
- `backend/tests/test_runtime_config.py`

## Tasks / Subtasks

### Task 1: Canonicalize Production CORS Examples (AC: 1, 2)

- [x] Update `docs/mvp-mentoria/batch-c-backend-cors-current-state.md` so production CORS examples use only `https://www.innovai-solutions.com.br`.
- [x] Update `frontend/README.md` so production-facing backend/CORS examples use only `https://www.innovai-solutions.com.br`.
- [x] Update `docs/client-launch-runbook.md` so production backend/CORS examples use only `https://www.innovai-solutions.com.br`.
- [x] Keep apex `https://innovai-solutions.com.br` only in redirect/canonical-host checks.

### Task 2: Separate Normal Preview From Mentor-Demo Approval (AC: 3)

- [x] In `docs/client-launch-runbook.md`, add one normal Preview backend startup example using:
  - `APP_ENV=production`
  - `CORS_ALLOW_ORIGINS=https://www.innovai-solutions.com.br`
  - `CORS_ALLOW_ORIGIN_REGEX=^https://.*\\.vercel\\.app$`
  - `ENABLE_MENTOR_DEMO_ROUTES=false`
  - `ALLOW_REMOTE_MENTOR_DEMO_ROUTES=false`
- [x] Keep the existing mentor-demo approval example as a separate exceptional posture, not the default Preview example.

### Task 3: Surface Preview Regex In Backend Runtime Evidence (AC: 4, 5, 6)

- [x] In `backend/app/main.py`, add `cors_origin_regex` to `app.state.runtime_summary`.
- [x] Include `cors_origin_regex` in the `backend_runtime_configured` log line.
- [x] Include `cors_origin_regex` in the `backend_startup_complete` log line.
- [x] In `backend/tests/test_runtime_config.py`, extend the existing runtime test coverage to assert the surfaced regex value.

## Validation Steps

1. `cd backend`
2. `python -m pytest tests/test_runtime_config.py -q`
3. `rg -n "innovai-solutions\\.com\\.br,https://innovai-solutions\\.com\\.br|CORS_ALLOW_ORIGIN_REGEX|cors_origin_regex" docs/mvp-mentoria/batch-c-backend-cors-current-state.md frontend/README.md docs/client-launch-runbook.md backend/app/main.py backend/tests/test_runtime_config.py`
4. Review the touched docs and confirm apex remains in redirect checks only, not in backend CORS allowlist examples.

## Dev Agent Record

### Completion Notes

- Canonicalized production CORS examples to the `www` host only while leaving apex references only in redirect validation.
- Added a normal Preview backend startup example separate from the mentor-demo exception posture in the runbook.
- Surfaced `cors_origin_regex` in backend runtime summary and startup logging, and extended runtime test coverage to assert it.

## File List

- `docs/mvp-mentoria/batch-c-backend-cors-current-state.md`
- `frontend/README.md`
- `docs/client-launch-runbook.md`
- `backend/app/main.py`
- `backend/tests/test_runtime_config.py`
- `_bmad-output/implementation-artifacts/4-3d-batch-c-canonical-cors-and-preview-evidence-fix.md`

## Change Log

- Standardized production CORS examples to canonical `www` only.
- Added separate normal Preview and mentor-demo approval backend examples.
- Added `cors_origin_regex` to runtime summary and startup logs.
