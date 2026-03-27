# Story 4.3b: batch-c-operator-docs-and-runtime-summary-alignment (Batch C Follow-up)

Status: ready-for-dev

## Story

As a release operator,
I want the backend CORS contract to be documented consistently across the operator runbook, frontend README, and release gate checklist, and I want backend startup evidence to include the configured preview-origin regex,
so that Preview vs Production CORS configuration is reproducible and verifiable during real deployments.

## Background (Why This Exists)

Batch C introduced `CORS_ALLOW_ORIGIN_REGEX` to support dynamic preview origins (e.g., Vercel preview URLs) without using wildcard `*`, and also expanded local default CORS origins to include `:4173`.

However, operator-facing docs still largely describe only exact `CORS_ALLOW_ORIGINS` matching and do not explain Preview configuration, and backend startup logs/runtime summary do not expose the regex value. This makes deploy verification ambiguous even though the runtime supports the desired contract.

## Requirements

1. Update `docs/client-launch-runbook.md` and `frontend/README.md` so the backend contract explicitly covers `CORS_ALLOW_ORIGIN_REGEX`, explains when exact `CORS_ALLOW_ORIGINS` is sufficient, and provides:
   - one Preview example
   - one Production example
2. If `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` remains the release gate, update its CORS wording so Preview can be validated via explicit origin plus regex (not "exact-origin-only").
3. Fix `docs/mvp-mentoria/batch-c-backend-cors-current-state.md` to match the implemented runtime:
   - include `:4173` in local defaults
   - remove stale statements implying no preview pattern support
   - remove the stale statement that `:4173` requires explicit `CORS_ALLOW_ORIGINS`
   - stop implying `*` is part of the production-like validation path
4. Add `cors_origin_regex` to backend runtime evidence:
   - include it in `app.state.runtime_summary` in `backend/app/main.py`
   - emit it in startup logging
   - extend a backend runtime test to assert it is surfaced

## Acceptance Criteria

1. Operator docs explicitly define:
   - `CORS_ALLOW_ORIGINS` for Production (explicit allowlist)
   - `CORS_ALLOW_ORIGIN_REGEX` for Preview (pattern allowlist)
   - when regex is unnecessary (single stable hosted origin)
2. The release gate checklist no longer requires "exact-only" matching for Preview scenarios and clearly allows "explicit origin(s) + regex" as the validation contract.
3. `docs/mvp-mentoria/batch-c-backend-cors-current-state.md` contains no contradictions with:
   - `backend/app/config/runtime.py` local defaults (`:4173` included)
   - `backend/app/main.py` middleware wiring (`allow_origin_regex`)
   - wildcard rejection in production-like envs
4. Backend runtime evidence contains the configured regex:
   - `app.state.runtime_summary["cors_origin_regex"]` exists (string or `None`)
   - startup logs include the value (or `none`)
5. `backend/tests/test_runtime_config.py` asserts the runtime summary surfaces the regex value.

## Implementation Notes (Keep Diffs Narrow)

- Do not change CORS enforcement semantics beyond surfacing evidence (no new allow/deny logic).
- Do not refactor unrelated release docs.
- Do not change frontend runtime code or `frontend/vercel.json` in this follow-up.
- Use ASCII for docs unless the file already uses Portuguese diacritics consistently.

## Files Likely Touched

- `docs/client-launch-runbook.md`
- `frontend/README.md`
- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- `docs/mvp-mentoria/batch-c-backend-cors-current-state.md`
- `backend/app/main.py`
- `backend/tests/test_runtime_config.py`

## Tasks / Subtasks

### Task 1: Operator Contract Updates (Docs + README) (AC: 1)

- [ ] In `docs/client-launch-runbook.md`, update the Backend startup section to:
  - state that `CORS_ALLOW_ORIGINS` must list production hosted origin(s) (no `*`)
  - introduce `CORS_ALLOW_ORIGIN_REGEX` for Preview dynamic origins
  - add one Preview example and one Production example (minimal, copy/paste safe)
- [ ] In `frontend/README.md`, add one concise paragraph under backend pairing that:
  - references `CORS_ALLOW_ORIGIN_REGEX`
  - clarifies when exact `CORS_ALLOW_ORIGINS` is sufficient (single stable origin)

### Task 2: Release Gate Wording (If Still Gate) (AC: 2)

- [ ] In `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`, update the CORS validation row(s) so Preview validation allows:
  - `CORS_ALLOW_ORIGINS` includes the stable production origin(s)
  - `CORS_ALLOW_ORIGIN_REGEX` covers preview origins when needed

### Task 3: Fix Batch C Current-State Doc (AC: 3)

- [ ] Update `docs/mvp-mentoria/batch-c-backend-cors-current-state.md` to:
  - list `:4173` in `LOCAL_CORS_ORIGINS`
  - remove any stale "no preview pattern support" phrasing
  - remove the stale note about needing explicit CORS for `:4173`
  - make it explicit that wildcard `*` is rejected for production-like envs

### Task 4: Surface Regex In Startup Evidence (Backend) (AC: 4)

- [ ] In `backend/app/main.py`:
  - add `cors_origin_regex` to `app.state.runtime_summary`
  - include it in `backend_runtime_configured` and `backend_startup_complete` log lines
- [ ] In `backend/tests/test_runtime_config.py`:
  - extend the existing regex test (or add a new one) to assert:
    - `app.state.runtime_summary["cors_origin_regex"]` equals the configured value

## Validation Steps (Must Run)

1. `cd backend`
2. `python -m pytest tests/test_runtime_config.py -q`
3. Optional docs sanity:
   - `rg -n "CORS_ALLOW_ORIGIN_REGEX" docs frontend/README.md`

