# Quick Dev Report - Mentor Workspace Backfill

## Request Restatement
Implement controlled backfill of `mentor_id` / `provider_id` for active mentor-workspace records and validate post-backfill behavior for:
- `GET /mentor/centro-comando/alunos`
- `GET /mentor/radar/alunos/{student_id}`
- `GET /mentor/matriz-renovacao`

## Most Likely Files Involved
- `backend/app/storage/enrollment_repository.py`
- `backend/app/storage/product_assignment_repository.py`
- `backend/app/services/indicator_carga_service.py`
- `backend/tests/integration/test_enrollment_repository.py`
- `backend/tests/integration/test_product_assignment_repository.py`
- `backend/tests/api/test_mentor_api.py`

## Smallest Safe Patch
1. Add explicit repository methods for controlled backfill on active rows only:
   - enrollments: fill missing `mentor_id` by `organization_id -> mentor_id` mapping.
   - product assignments: sync `provider_id`/`mentor_id` aliases and fill missing values from assignment/organization maps.
2. Trigger this backfill in `IndicatorCargaService` before active-enrollment selection used by mentor endpoints.
3. Add nearest-layer tests:
   - repository integration tests for both backfill methods.
   - API-level mentor test to verify post-backfill parity for Command Center, Radar, and Matrix.

## Changes Applied
- Added `EnrollmentRepository.backfill_active_mentor_ids(...)`.
- Added `ProductAssignmentRepository.backfill_active_provider_ids(...)`.
- Added `IndicatorCargaService._backfill_workspace_assignment_links()` and invoked it from `_iter_active_enrollments(...)`.
- Added integration coverage in:
  - `backend/tests/integration/test_enrollment_repository.py`
  - `backend/tests/integration/test_product_assignment_repository.py`
- Added API post-backfill coverage in:
  - `backend/tests/api/test_mentor_api.py`
- Hardened test helper in `test_mentor_api.py` for local environments where indicator-load endpoint returns `409` due Postgres runtime gate by using controlled repository fallback only in tests.

## Validation Executed
Run from `backend/`:

```bash
python -m pytest tests/integration/test_enrollment_repository.py tests/integration/test_product_assignment_repository.py tests/api/test_mentor_api.py -q
```

Result: `11 passed`.

## Risks and Follow-up Checks
- Backfill is write-on-read at service access time (intentional for workspace recovery); monitor I/O in high-frequency endpoint calls.
- Backfill only fills empty fields and does not override populated mentor/provider links, preserving explicit existing assignments.
- If an organization has no `mentor_id` and enrollments lack mentor linkage, rows remain unscoped by design.
