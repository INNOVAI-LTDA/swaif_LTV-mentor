# Story ADJ-016: client_code Contract Hardening (Frontend + Backend)

Status: ready-for-dev

## 1) Problem Statement

Today, `client_code` is primarily an operator/bootstrap selector for choosing `.env.client.<code>*` files, but it is not a hardened runtime contract shared by both services:

- Frontend resolves the active client identity (branding + base path) from `VITE_*` variables in `frontend/src/shared/config/env.ts`.
- Backend has no comparable "active client" setting; `CLIENT_CODE`/`CLIENT_NAME`/`CLIENT_PRODUCT_NAME` exist in client env templates but are not consumed by backend runtime config or startup logging.

This allows a release-risk mismatch where:

- the frontend is built/served for one client (branding/base path), while
- the backend is started with a different client profile (or generic defaults),

without an explicit, deterministic runtime signal to catch it early.

Goal: harden a single `client_code` contract so both frontend and backend deterministically resolve the same active client, and fail fast in production-like postures when the contract is missing/invalid.

## 2) Exact Files / Modules Likely Affected

Frontend (env ingress must remain centralized):

- `frontend/src/shared/config/env.ts`
- `frontend/src/shared/config/envContract.ts`
- `frontend/src/shared/config/env.test.ts`
- `frontend/vite.config.ts` (only if needed to fail-fast at build/dev start)
- `frontend/.env.example`
- `frontend/.env.client.*.example`
- `frontend/src/test/*` (only where mocks require the updated `env` shape)

Backend (runtime/config stays under backend/app/config, app startup stays thin):

- `backend/app/config/runtime.py`
- `backend/app/main.py`
- `backend/tests/test_runtime_config.py`

Bootstrap (operator path that currently ties both sides together):

- `scripts/mvp_bootstrap.py`
- `frontend/README.md` (only if the contract requirements change and need operator clarity)

Reference input (active engineering input for this adjustment):

- `docs/architecture/client_code_parameterization_current_state.md`
- `docs/ui-adjustments-backlog.md` (ADJ-016 row)

## 3) Acceptance Criteria

Client code contract (frontend):

1. Frontend exposes a normalized `env.clientCode` derived from `import.meta.env.VITE_CLIENT_CODE` and continues to read `import.meta.env` only inside `frontend/src/shared/config/env.ts`.
2. For `VITE_DEPLOY_TARGET=client`, the frontend fails fast at runtime initialization if `VITE_CLIENT_CODE` is missing or invalid.
3. For `VITE_DEPLOY_TARGET=local`, `VITE_CLIENT_CODE` may be optional, but when present must still be validated (no silent normalization to a different value).

Client code contract (backend):

4. Backend runtime config provides a single accessor (e.g., `get_client_code()` or `resolve_client_context()`) under `backend/app/config/runtime.py`.
5. When `APP_ENV` is production-like, backend startup fails fast if `CLIENT_CODE` is missing or invalid.
6. Backend includes the resolved `client_code` in `app.state.runtime_summary` and logs it during `backend_runtime_configured` and `backend_startup_complete`.

Bootstrap alignment:

7. When using `scripts/mvp_bootstrap.bat --client-code <code>`, the frontend receives `VITE_CLIENT_CODE=<code>` and the backend receives `CLIENT_CODE=<code>` deterministically (no need for manual duplication).
8. `.env.client.<code>.example` templates for frontend include `VITE_CLIENT_CODE=<code>` and backend templates include `CLIENT_CODE=<code>`, and the values match.

Safety / non-regression:

9. No changes to routes, auth, adapters, domain hooks, or page shells.
10. No new demo credentials, preview flows, or client-visible demo copy is introduced into production-oriented paths.
11. Standard backend error envelope remains unchanged (no endpoint changes in this story).
12. Tests at the nearest relevant layer are updated/added and pass.

## 4) Implementation Notes (Smallest Safe Patch)

Contract shape and validation:

- Use the same validation rules for `client_code` across services:
  - trim whitespace
  - require non-empty (at least in production-like postures / client deploy target)
  - restrict characters to the existing bootstrap allowance: letters, numbers, hyphen, underscore
    - current precedent: `scripts/mvp_bootstrap.py` validates `client_code` with `.isalnum()` after stripping `-` and `_`.

Frontend:

- Add `VITE_CLIENT_CODE` as the only supported ingress for runtime client code (so it is visible in Vite `import.meta.env`).
- Keep all `import.meta.env` reads in `frontend/src/shared/config/env.ts`.
- Prefer adding a small normalizer in `frontend/src/shared/config/envContract.ts` (e.g., `normalizeClientCode(raw, deployTarget)`), then call it from `env.ts`.
- Update any tests that stub/mock `env` to include the new `clientCode` field only where TypeScript requires it (keep diffs narrow).

Backend:

- Add `get_client_code()` (or similar) to `backend/app/config/runtime.py`.
  - Gate strictness by `is_production_like_environment()`.
  - Keep the function pure and env-driven; do not pull in storage or services here.
- In `backend/app/main.py`, read the client code once during `create_app()` and include it in `app.state.runtime_summary`.
  - Do not add business rules to routes; this is startup posture only.

Bootstrap:

- Extend `scripts/mvp_bootstrap.py` so `--client-code` also sets `VITE_CLIENT_CODE=<code>` for the frontend process environment (in addition to existing `CLIENT_CODE`).
  - Do not rely on `CLIENT_CODE` for frontend runtime because Vite does not expose it.
  - Keep behavior backward-compatible for users who manually define `VITE_CLIENT_CODE` in the env file: do `setdefault` semantics.

Templates/docs:

- Add `VITE_CLIENT_CODE` to `frontend/.env.example` and `frontend/.env.client.*.example`.
- Confirm `backend/.env.client.*.example` already has `CLIENT_CODE` and that its value matches the frontend template.
- If `frontend/README.md` describes bootstrap by `client_code`, update it only to state that `VITE_CLIENT_CODE` is now part of the contract for client deploys (avoid broader doc edits).

## 5) Tests to Add / Update (Nearest Relevant Layer)

Frontend (contract tests):

- Update `frontend/src/shared/config/env.test.ts`:
  - Add a test that `VITE_DEPLOY_TARGET=client` without `VITE_CLIENT_CODE` fails with a clear error.
  - Add a test that invalid `VITE_CLIENT_CODE` (e.g., contains spaces or punctuation) fails.
  - Add a test that `VITE_DEPLOY_TARGET=local` can omit `VITE_CLIENT_CODE` (if we keep it optional for local).

Frontend (unit tests that mock env shape):

- Update only the tests that mock `../shared/config/env` and need the new `env.clientCode` field to satisfy TS and runtime usage.
  - Keep changes to the minimum set of tests impacted by the `env` object shape.

Backend (runtime config tests):

- Add tests in `backend/tests/test_runtime_config.py`:
  - production-like `APP_ENV` without `CLIENT_CODE` fails fast with a deterministic error message.
  - invalid `CLIENT_CODE` fails fast.
  - local `APP_ENV=local` may allow missing `CLIENT_CODE` (if we keep it optional for local), but still validates when present.

Bootstrap (no existing tests):

- No new test harness is required in this story unless one already exists for `scripts/`; keep this as a manual/ops verification step:
  - run `scripts\\mvp_bootstrap.bat --client-code accmed` and confirm frontend starts with `VITE_CLIENT_CODE` present (visible indirectly by logging or by adding a dev-only console log is out of scope; instead validate by a one-off env dump in the bootstrap logs if already present).

## 6) Explicit Out of Scope

- Multi-tenant runtime switching; this story is about deterministic selection at startup, not runtime switching.
- Changing API shapes, adding new endpoints, or modifying the standardized backend error envelope.
- Changing auth, routing, adapters, domain hooks, or UI shells beyond what is needed to read the environment contract.
- Moving storage roots or store paths based on `client_code` (storage remains controlled by existing per-store env vars).
- Adding "demo" defaults for production-like environments or client deploys.
- Introducing new `import.meta.env` reads outside `frontend/src/shared/config/env.ts`.

## 7) Release Risks If Not Implemented

- Client mismatch risk: frontend branding/base path can point to client A while backend runs with client B (or generic defaults), with no immediate failure signal.
- Operator error risk: staging/hosted deploy can pass superficial checks but serve inconsistent identity/data postures, creating hard-to-debug incidents.
- Compliance risk: lingering localhost/dev defaults can leak into hosted environments if env files are reused without a strict contract gate.
- Evidence gap: release logs do not currently record an "active client" identifier for backend, making it harder to attach objective evidence in `docs/production-release-tracker.md`.

## References

- `_bmad-output/project-context.md`
- `docs/ui-adjustments-backlog.md` (ADJ-016)
- `docs/architecture/client_code_parameterization_current_state.md`
- `frontend/src/shared/config/env.ts`
- `frontend/src/shared/config/envContract.ts`
- `backend/app/config/runtime.py`
- `backend/app/main.py`
- `scripts/mvp_bootstrap.py`
