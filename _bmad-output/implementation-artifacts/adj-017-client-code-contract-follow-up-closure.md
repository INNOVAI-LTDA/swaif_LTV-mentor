# Story ADJ-017: client_code Contract Closure (Follow-up Hardening)

Status: ready-for-dev

## 1) Problem Statement

ADJ-016 improved the shared `client_code` contract, but the release-hardening review found three unresolved gaps that keep a mismatch path open:

1. `backend/app/config/runtime.py` still allows missing `CLIENT_CODE` for `APP_ENV=local`, leaving backend client identity optional in a runtime posture used for release rehearsal.
2. Operator-facing contract docs are incomplete: `frontend/README.md` and `backend/.env.example` do not clearly require and explain the `CLIENT_CODE` + `VITE_CLIENT_CODE` pair.
3. `scripts/mvp_bootstrap.py` now injects both variables, but there is no focused regression test proving synchronization and `setdefault` behavior.

Goal: close these exact gaps with a narrow, brownfield-safe patch so client selection is explicit, deterministic, and release-safe.

## 2) Exact Files to Change

- `backend/app/config/runtime.py`
- `backend/tests/test_runtime_config.py`
- `frontend/README.md`
- `backend/.env.example`
- `scripts/mvp_bootstrap.py`
- `backend/tests/test_mvp_bootstrap_contract.py` (new focused script-contract test module)

## 3) Acceptance Criteria

1. Backend runtime no longer treats `CLIENT_CODE` as optional for local release-like startup:
   - `get_client_code()` must fail fast when `CLIENT_CODE` is missing for `APP_ENV=local` and production-like environments.
   - If a narrow test-only exception is needed, it must be explicit and documented in code/tests (no silent fallback for operational paths).
2. `CLIENT_CODE` validation remains strict and deterministic (letters, numbers, hyphen, underscore only), with clear error messages.
3. Operator docs explicitly define the paired contract:
   - `frontend/README.md` states `VITE_CLIENT_CODE` and `CLIENT_CODE` must represent the same active client in release/bootstrap flows.
   - `backend/.env.example` includes `CLIENT_CODE` with clear guidance for local and production-like startup.
4. Bootstrap synchronization is covered by automated regression tests:
   - tests prove `--client-code <code>` injects backend `CLIENT_CODE` and frontend `VITE_CLIENT_CODE` consistently;
   - tests prove pre-existing env-file overrides are not overwritten (current `setdefault` contract).
5. No unrelated architecture movement:
   - no route changes, no API contract changes, no shell/routing changes, no adapter boundary changes.
6. Docs and tests are updated in the same change set as behavior changes.

## 4) Implementation Notes (Smallest Safe Patch)

- Keep backend runtime rules in `backend/app/config/runtime.py`; do not move this logic into routes or `main.py`.
- Tighten `get_client_code()` so operational startup (`local` + production-like) is explicit by default.
- Keep frontend env ingress centralized in `frontend/src/shared/config/env.ts`; this story should not spread `import.meta.env` access.
- Update only the operator docs that define startup contracts (`frontend/README.md`, `backend/.env.example`).
- In `scripts/mvp_bootstrap.py`, keep current `setdefault` semantics and cover them with tests instead of changing flow shape.
- If testability requires a tiny extraction in `scripts/mvp_bootstrap.py`, keep it local and explicit (no broad refactor).

## 5) Tests to Add / Update

- Update `backend/tests/test_runtime_config.py`:
  - replace/adjust the current local-optional expectation to assert missing `CLIENT_CODE` fails for `APP_ENV=local`;
  - keep/extend validation tests for invalid characters and valid values.
- Add `backend/tests/test_mvp_bootstrap_contract.py`:
  - verifies `client_code` sync injects backend `CLIENT_CODE` and frontend `VITE_CLIENT_CODE`;
  - verifies `setdefault` behavior preserves explicit values already present in loaded env overrides;
  - verifies no injection occurs when `client_code` is absent.
- Optional targeted frontend test update only if README-driven examples require env-shape test fixture updates (no feature-level UI test changes expected).

## 6) Explicit Out-of-Scope

- Any auth, routing, shell, adapter, or page-level UI/layout work.
- Any API endpoint, schema, or error-envelope changes.
- Multi-tenant runtime switching or dynamic client switching at request-time.
- Storage-root redesign or migration tied to `client_code`.
- Broad bootstrap rewrite beyond minimal extraction needed for focused tests.

## 7) Release-Risk Notes

- If this follow-up is not implemented, release rehearsal can still run backend without explicit client identity while frontend is client-scoped, preserving mismatch risk.
- Incomplete operator docs can cause inconsistent manual startup between frontend and backend even when code is correct.
- Without a bootstrap sync regression test, future script edits can silently break the shared `CLIENT_CODE`/`VITE_CLIENT_CODE` contract.

## References

- `_bmad-output/project-context.md`
- `docs/architecture/client_code_parameterization_current_state.md`
- `_bmad-output/implementation-artifacts/adj-016-client-code-contract-hardening.md`
- `frontend/README.md`
- `backend/.env.example`
- `backend/app/config/runtime.py`
- `scripts/mvp_bootstrap.py`
