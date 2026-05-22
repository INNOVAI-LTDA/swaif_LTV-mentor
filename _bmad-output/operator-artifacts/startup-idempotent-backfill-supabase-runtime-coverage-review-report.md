# Review Report - startup-idempotent-backfill-supabase-runtime-coverage

Date: 2026-05-21
Reviewer mode: bmad-code-review (adversarial triage)
Spec/context used:
- `_bmad-output/operator-artifacts/startup-idempotent-backfill-supabase-runtime-coverage-quick-spec.md`
- `_bmad-output/project-context.md`
- `docs/mvp-mentoria/contracts-freeze-v1.md`

## Findings

### Patch

1. **Runtime regression: local/dev admin indicator load now hard-requires Supabase URL**
- Category: `patch`
- Severity: High
- Location: `backend/app/services/indicator_carga_service.py:1049`
- Evidence: `load_initial_indicators` now raises `RuntimeDependencyError` whenever `SUPABASE_DB_URL` is empty, without environment gating.
- Why this is a problem: this blocks local/test seeding flows that previously returned `200`, and it is confirmed by failing suites that seed Radar/Workspace via `/admin/alunos/{id}/indicadores/carga-inicial`.
- Runtime evidence:
  - `python -m pytest tests/api/test_radar_api.py -q` -> `2 failed` (expects `200`, gets `409`).
  - `python -m pytest tests/api/test_student_workspace_api.py -q` -> `4 failed` (same `409` regression path).
- Contract/intent impact: violates Story 1.2 runtime-mode rule for local/dev/test exception and blocks real runtime coverage validation for Radar in non-prod test flows.

2. **Coverage masking in mentor API tests hides real contract/runtime breakage**
- Category: `patch`
- Severity: High
- Location: `backend/tests/api/test_mentor_api.py:169`
- Evidence: test setup now accepts `409` from admin indicator load and writes directly to repositories (`replace_for_enrollment`) as fallback.
- Why this is a problem: API contract regressions in the admin load path can pass unnoticed; tests no longer validate the intended end-to-end HTTP path for seeded mentor/radar scenarios.
- Contract/intent impact: weakens regression guardrails exactly where frozen v1 behavior should stay observable at the boundary.

3. **Startup sync backfill has avoidable O(enrollments) connection + DDL overhead**
- Category: `patch`
- Severity: Medium
- Locations:
  - `backend/app/operations/sync_runtime_stores_from_supabase.py:502`
  - `backend/app/storage/postgres_indicator_repositories.py:28`
  - `backend/app/storage/postgres_indicator_repositories.py:152`
  - `backend/app/storage/postgres_indicator_repositories.py:256`
- Evidence:
  - Backfill loops each active enrollment and calls both repository `insert_missing_for_enrollment` methods.
  - Each call opens a new DB connection and runs `_ensure_table` (CREATE TABLE/INDEX IF NOT EXISTS checks).
- Why this is a problem: startup cost scales poorly with active enrollments and can increase boot latency/DB churn, especially under strict runtime where sync is forced.
- Contract/intent impact: no direct v1 payload break, but risks operational instability/performance during startup sync.

4. **Auth contract assertion weakened in mentor API smoke**
- Category: `patch`
- Severity: Low
- Location: `backend/tests/api/test_mentor_api.py:286`
- Evidence: `test_mentor_routes_require_auth` now asserts only `401`, no longer asserting envelope `error.code` (`AUTH_MISSING_TOKEN`).
- Why this is a problem: decreases protection for frozen error-envelope semantics.

### Defer

1. **Radar and student workspace API suites still red on seeded load path**
- Category: `defer`
- Severity: Medium
- Evidence: failures reproduced in this review run and linked to the same runtime gating regression above.
- Why deferred: this report is review-only; fix should happen in follow-up implementation pass.

## Validation Evidence Executed

- `python -m pytest tests/unit/test_supabase_runtime_sync.py tests/unit/test_indicator_carga_service.py tests/api/test_mentor_api.py tests/api/test_student_workspace_api.py tests/integration/test_enrollment_repository.py tests/integration/test_indicator_repositories.py -q`
  - Result: `26 passed, 4 failed` (all failures in `test_student_workspace_api.py`, expecting `200` but receiving `409`).
- `python -m pytest tests/api/test_radar_api.py -q`
  - Result: `1 passed, 2 failed` (seed load expects `200`, receives `409`).
- `python -m pytest tests/integration/test_product_assignment_repository.py -q`
  - Result: `6 passed`.

## Triage Summary

- intent_gap: 0
- bad_spec: 0
- patch: 4
- defer: 1
- rejected as noise: 0

## Recommendation

Proceed with a focused `bmad-dev-story` patch that:
1. Restores environment-aware load behavior (`SUPABASE_DB_URL` required only when strict runtime is required),
2. Removes test-side repository write bypasses in API setup,
3. Keeps startup backfill idempotent but reduces per-enrollment connection/DDL overhead.
