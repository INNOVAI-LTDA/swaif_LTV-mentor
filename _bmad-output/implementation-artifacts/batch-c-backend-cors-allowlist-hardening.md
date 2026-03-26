# Story: Batch C - Backend CORS Allowlist Hardening (Deployment-Aligned)

Status: review
Owner: dmene
Date: 2026-03-26

## Problem Statement

As we move from local validation to a real hosted frontend (Vercel), the backend must enforce a CORS allowlist that matches the actual deployment origins:

- production custom domain (canonical `https://www.yourdomain.com`)
- preview origins (if used)
- local dev origins for developer workflows

The backend already has centralized CORS configuration, but it currently allows `*` via `CORS_ALLOW_ORIGINS="*"` and toggles `allow_credentials` based on whether `*` is present. We need to harden the operational contract so that wildcard CORS is not used in unsafe postures and so that the allowlist is clearly documented for operators.

This is a brownfield hardening step: make the smallest safe change that prevents common misconfiguration and clarifies the operator contract.

## Goal (Batch C Only)

1. Align backend CORS configuration with deployment reality (Vercel-hosted SPA + custom domain).
2. Allow only necessary origins:
   - `https://www.yourdomain.com` (canonical production)
   - preview domain pattern, only if needed and explicitly supported
   - localhost dev origins (existing local defaults)
3. Avoid wildcard CORS where unsafe (especially when credentials/cookies are involved).
4. Document the backend CORS allowlist contract clearly for operators.

## Constraints / Guardrails (Binding)

- Keep diffs narrow; avoid unrelated backend cleanup.
- Keep FastAPI route handlers thin (no route changes expected).
- Preserve standardized backend error envelope (this story should not touch error shaping).
- Keep backend runtime/config rules under `backend/app/config` and app startup in `backend/app/main.py`.

## Current State (Evidence)

### CORS config location and behavior

- CORS env var: `CORS_ALLOW_ORIGINS` (comma-separated list)
- Parsing + validation: `backend/app/config/runtime.py`
  - `normalize_cors_origin()`:
    - allows `"*"`
    - rejects non-absolute origins, credentials, and any path/query/fragment
  - `resolve_cors_origins()`:
    - returns explicit env list if set
    - requires explicit `CORS_ALLOW_ORIGINS` when `APP_ENV` is production-like
    - otherwise falls back to `LOCAL_CORS_ORIGINS`
- Middleware wiring: `backend/app/main.py`
  - `allow_origins=["*"] if "*" in cors_origins else cors_origins`
  - `allow_credentials=not allow_all_origins`

### Credentials / cookies involvement (current posture)

- Frontend uses Bearer tokens in `Authorization` header (not cookies) in `frontend/src/shared/api/httpClient.ts`.
- Backend sets `allow_credentials=True` whenever allowlist is explicit (non-`*`). (`backend/app/main.py:87`)
- If wildcard `*` is used, backend forces `allow_credentials=False`, which is safer, but wildcard still expands origin exposure.

### Operator templates

- `backend/.env.example` already documents `CORS_ALLOW_ORIGINS` as required in production-like env and gives an example with a single https origin.

## Scope

### In Scope (Exact Changes)

1. Harden runtime CORS origin resolution to discourage/forbid wildcard in production-like environments:
   - If `APP_ENV` is production-like and `CORS_ALLOW_ORIGINS` contains `"*"`, fail fast at startup with a clear error message.
   - Keep `"*"` as an optional local-only escape hatch if the team still wants it for certain dev tooling, but require explicit intent (documented).
2. Add explicit support for Preview origins if needed:
   - Smallest safe path: do **not** introduce regex/pattern matching in this batch unless strictly necessary.
   - Prefer explicit allowlisting via `CORS_ALLOW_ORIGINS` for the preview origins actually used.
   - If a preview “pattern” is required, implement it as a separate, explicitly tested normalization function under `backend/app/config/runtime.py` with strict constraints.
3. Update operator-facing docs/templates to clearly state:
   - the canonical production origin to allow (www)
   - whether preview origins are allowed and how to configure them
   - local dev defaults and when they apply
   Files:
   - `backend/.env.example`
   - (Optionally) `docs/client-launch-runbook.md` and/or `docs/production-release-tracker.md` if they are the active operator sources for deploy posture.

### Out of Scope (Explicit)

- Backend auth/session changes; cookies or session middleware additions.
- Any changes to endpoints, routers, or error envelope.
- Custom domain and redirect enforcement (Batch D).
- Frontend security headers/CSP/HSTS (Batches E/F).

## Acceptance Criteria (Must Pass)

1. Backend CORS allowlist matches deployment reality:
   - Operators can configure `CORS_ALLOW_ORIGINS` to include exactly the frontend origin(s) required (production and optionally preview).
2. Wildcard usage is not used where unsafe:
   - In production-like `APP_ENV`, startup fails if `CORS_ALLOW_ORIGINS` includes `"*"`.
3. Allowed origins are documented clearly:
   - `backend/.env.example` includes a canonical example for production (`https://www.yourdomain.com`) and clear guidance for preview/local.
4. Tests cover the hardening at the nearest relevant layer:
   - Add/update unit tests for `resolve_cors_origins()` behavior regarding `"*"` in production-like env.

## Implementation Notes (Smallest Safe Patch)

- Keep origin validation strict (no paths/credentials).
- Prefer fail-fast errors with actionable messages (operator-friendly).
- Keep changes confined to:
  - `backend/app/config/runtime.py` (policy)
  - `backend/tests/test_cors_config.py` (coverage)
  - docs/templates (`backend/.env.example`, optionally runbook/tracker)

## Files / Modules Likely Affected

- Update: `backend/app/config/runtime.py`
- Update: `backend/app/main.py` (only if middleware wiring needs a small adjustment; prefer leaving it as-is if policy is handled in runtime config)
- Update: `backend/.env.example`
- Update: `backend/tests/test_cors_config.py`
- Optional update (docs as active inputs):
  - `docs/client-launch-runbook.md`
  - `docs/production-release-tracker.md`

## Tests / Validation

### Automated

- `cd backend && pytest -q`
  - Ensure `test_cors_config.py` includes a case:
    - `APP_ENV=production` + `CORS_ALLOW_ORIGINS=*` -> raises with the new explicit error.

### Manual (post-deploy sanity)

1. Start backend in production-like mode with explicit allowlist:
   - `APP_ENV=production CORS_ALLOW_ORIGINS=https://www.yourdomain.com ...`
2. From the deployed frontend origin, verify:
   - preflight (OPTIONS) succeeds
   - subsequent API requests succeed
3. Confirm that using `CORS_ALLOW_ORIGINS=*` in production-like env fails at startup (operator guardrail).

## Release Risks If Not Implemented

- Operators may configure wildcard CORS in a hosted environment, unnecessarily expanding origin exposure.
- Preview deployments may break intermittently due to unclear allowlist requirements.
- CORS misconfiguration becomes a deployment blocker late in the release process instead of failing fast with a clear contract.

## Dev Agent Record

### Debug Log
- 2026-03-26: `cd backend; py -m pytest tests/test_cors_config.py -q`

### Completion Notes
- Hardened CORS resolution to fail fast when `CORS_ALLOW_ORIGINS` includes `"*"` in production-like environments; local still supports existing defaults.
- Documented the canonical production and preview origin examples and the no-wildcard rule in `backend/.env.example`.
- Updated operator docs to highlight that production-like CORS cannot use `"*"`.

## File List
- `backend/app/config/runtime.py`
- `backend/tests/test_cors_config.py`
- `backend/.env.example`
- `docs/client-launch-runbook.md`
- `docs/production-release-tracker.md`
- `_bmad-output/implementation-artifacts/batch-c-backend-cors-allowlist-hardening.md`

## Change Log
- 2026-03-26: Batch C backend CORS allowlist hardening implemented and documented.
