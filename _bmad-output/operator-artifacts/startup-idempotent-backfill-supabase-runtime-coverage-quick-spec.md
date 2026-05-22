---
title: 'Startup Idempotent Backfill for Supabase Runtime Coverage (Radar/Matrix/Command Center)'
slug: 'startup-idempotent-backfill-supabase-runtime-coverage'
created: '2026-05-21T00:00:00-03:00'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.13', 'FastAPI', 'Postgres (Supabase)', 'psycopg', 'Pytest']
files_to_modify: ['backend/app/operations/sync_runtime_stores_from_supabase.py', 'backend/app/storage/postgres_indicator_repositories.py', 'backend/app/main.py', 'backend/tests/unit/test_supabase_runtime_sync.py', 'backend/tests/api/test_mentor_api.py']
code_patterns: ['Thin route handlers via routers under app/api/routes', 'Business logic in app/services and app/operations', 'Repository-backed persistence for runtime domains', 'Preserve v1 API contract and standardized error envelope']
test_patterns: ['Backend unit tests under backend/tests/unit', 'Backend API tests under backend/tests/api', 'Assert standardized error envelope shape when applicable']
---

# Tech-Spec: Startup Idempotent Backfill for Supabase Runtime Coverage (Radar/Matrix/Command Center)

**Created:** 2026-05-21T00:00:00-03:00

## Overview

### Problem Statement

In Supabase strict runtime, only 3 of ~250 enrollments currently have `runtime_measurements`/`runtime_checkpoints` data, causing low mentor-view coverage and unstable behavior for Command Center, Matrix, and Radar reads.

### Solution

Extend startup sync with an idempotent runtime backfill that ensures both `deva_accmed_runtime_measurements` and `deva_accmed_runtime_checkpoints` are populated for all active enrollments, while preserving contracts v1 and the standardized API error envelope.

### Scope

**In Scope:**
- Idempotent startup-time population/repair of runtime measurement/checkpoint rows for active enrollments.
- Runtime write path designed to be safe on repeated startup executions.
- Validation impact across mentor routes for Command Center, Matrix, and Radar.
- Keep current API contracts and error envelope unchanged.

**Out of Scope:**
- Any v1 response-shape changes.
- New public endpoints.
- Broad architecture refactors beyond runtime sync/backfill.

## Context for Development

### Codebase Patterns

- Startup flow runs in `backend/app/main.py` and already calls `sync_runtime_stores_from_supabase(...)` when startup sync is enabled.
- Runtime sync operation in `backend/app/operations/sync_runtime_stores_from_supabase.py` currently builds payloads and writes JSON stores; strict runtime route reads rely on Postgres repositories.
- Postgres repositories exist for runtime indicators in `backend/app/storage/postgres_indicator_repositories.py` with `replace_for_enrollment` semantics.
- Mentor routes in `backend/app/api/routes/mentor.py` resolve Postgres repositories in strict runtime and rely on `IndicatorCargaService` for center/matrix/radar behavior.
- `IndicatorCargaService` computes mentor views from active enrollments plus measurements/checkpoints and must remain the business-logic owner.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `backend/app/main.py` | Startup hook and sync trigger point |
| `backend/app/config/runtime.py` | Strict runtime/sync enablement gates |
| `backend/app/operations/sync_runtime_stores_from_supabase.py` | Source-to-runtime mapping logic and current sync write path |
| `backend/app/storage/postgres_indicator_repositories.py` | Runtime Postgres repositories for measurements/checkpoints |
| `backend/app/services/indicator_carga_service.py` | Read-path behavior for mentor center/matrix/radar |
| `backend/app/api/routes/mentor.py` | Contract-facing mentor routes and error-envelope behavior |
| `backend/tests/unit/test_supabase_runtime_sync.py` | Unit anchor for sync payload behavior |
| `backend/tests/api/test_mentor_api.py` | API coverage for mentor center/radar/matrix behavior |
| `backend/tests/api/test_admin_indicator_load_api.py` | Error-envelope and runtime-domain hardening patterns |
| `docs/mvp-mentoria/contracts-freeze-v1.md` | Frozen v1 compatibility constraints |
| `docs/diagnostics/supabase-student-relational-report.md` | Diagnostic evidence of low runtime coverage |

### Technical Decisions

- Keep startup sync as the single entrypoint for this repair; avoid introducing a new API path.
- Implement idempotent writes by natural keys and "insert-missing" semantics, avoiding overwrite of existing runtime measurements/checkpoints.
- Keep route handlers thin; do not move business logic out of services/operations.
- Keep v1 responses untouched and preserve the standardized envelope `{ error: { status, code, message, details } }` for API-visible failures.

## Implementation Plan

### Tasks

- [ ] Task 1: Add runtime backfill planner inside startup sync operation
  - File: `backend/app/operations/sync_runtime_stores_from_supabase.py`
  - Action: Add helper(s) to derive active runtime enrollment ids plus per-enrollment measurement/checkpoint candidates from the already-built payloads.
  - Notes: Reuse existing `_build_runtime_payloads` output; do not add a parallel source query pipeline.

- [ ] Task 2: Add idempotent insert-missing methods to runtime Postgres repositories
  - File: `backend/app/storage/postgres_indicator_repositories.py`
  - Action: Add repository methods that upsert/insert missing rows by natural key (`enrollment_id + metric_id` for measurements; `enrollment_id + week` for checkpoints) using Postgres `ON CONFLICT DO NOTHING`.
  - Notes: Keep existing `replace_for_enrollment` unchanged for admin load flows; startup backfill should use new methods to avoid destructive rewrites.

- [ ] Task 3: Integrate startup sync with Postgres runtime table backfill
  - File: `backend/app/operations/sync_runtime_stores_from_supabase.py`
  - Action: After payload generation, execute idempotent backfill into `deva_accmed_runtime_measurements` and `deva_accmed_runtime_checkpoints` for active enrollments.
  - Notes: Preserve current JSON store writes and sync report behavior; add explicit counters for candidates/inserted/skipped.

- [ ] Task 4: Expose startup backfill observability without contract changes
  - File: `backend/app/main.py`
  - Action: Keep startup flow unchanged but include new sync counters in runtime summary/log for operational verification.
  - Notes: No route contract changes, no new endpoints, no change in API payload shapes.

- [ ] Task 5: Add unit coverage for idempotent startup behavior
  - File: `backend/tests/unit/test_supabase_runtime_sync.py`
  - Action: Add tests proving repeated startup backfill attempts do not duplicate runtime measurement/checkpoint rows and that only active enrollments are targeted.
  - Notes: Assert deterministic candidate counts and insert/skipped counters.

- [ ] Task 6: Add API coverage for mentor route validation after startup repair
  - File: `backend/tests/api/test_mentor_api.py`
  - Action: Add/extend scenario where runtime data starts sparse, startup sync repair runs, then mentor routes (`/mentor/centro-comando/alunos`, `/mentor/matriz-renovacao`, `/mentor/radar/alunos/{student_id}`) return expected data for scoped active students.
  - Notes: Keep existing authorization/error-envelope checks intact.

### Acceptance Criteria

- [ ] AC 1: Given strict runtime startup sync is enabled and active enrollments exist, when backend startup executes sync, then missing rows are populated in `deva_accmed_runtime_measurements` and `deva_accmed_runtime_checkpoints` for all active enrollments.
- [ ] AC 2: Given startup sync runs multiple times with unchanged source data, when idempotent backfill executes repeatedly, then no duplicate runtime measurement/checkpoint rows are created.
- [ ] AC 3: Given runtime rows already exist for an enrollment, when startup backfill runs, then existing rows are preserved (insert-missing semantics) and only missing natural-key rows are added.
- [ ] AC 4: Given mentor requests center/matrix/radar after startup repair, when routes are called for a student in mentor scope, then responses are successful and include runtime-derived data expected by existing route contracts.
- [ ] AC 5: Given mentor requests center/matrix/radar for a student outside mentor scope, when routes are called, then existing scoped behavior and error-envelope semantics remain unchanged.
- [ ] AC 6: Given current v1 frozen contract expectations, when this change is applied, then no endpoint names, response field types, or standardized error envelope structure are modified.

## Additional Context

### Dependencies

- `SUPABASE_DB_URL` present in strict runtime/startup-sync modes.
- Postgres access with permissions to read source tables and write runtime indicator tables.
- Runtime source tables (`deva_accmed_enrollments`, metrics/pillars/products/users) available at startup.
- `psycopg` installed in runtime environment.

### Testing Strategy

- Unit tests (`backend/tests/unit/test_supabase_runtime_sync.py`):
  - Validate active-enrollment targeting.
  - Validate idempotent insert-missing semantics over repeated execution.
  - Validate counters/report fields for inserted vs skipped rows.
- API tests (`backend/tests/api/test_mentor_api.py`):
  - Validate mentor center, matrix, and radar happy-path responses after startup repair.
  - Validate mentor scoping remains enforced.
- Regression checks:
  - Run existing tests covering standardized error envelope and mentor auth behavior to ensure no contract regressions.

### Notes

- This is a stabilization-only change in final-adjustment mode; avoid introducing generic migration infrastructure.
- Potential risk: if natural-key uniqueness is not enforced, idempotence can be bypassed; repository-level conflict handling must be explicit.
- Future optimization (out of scope): batch-oriented SQL for very large enrollment volumes after correctness baseline is proven.
