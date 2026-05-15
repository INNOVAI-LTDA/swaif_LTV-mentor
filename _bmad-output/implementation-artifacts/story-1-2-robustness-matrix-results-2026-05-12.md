# Story 1.2 Robustness Matrix Results

Date: 2026-05-12  
Script: `scripts/validate-story-1-2.ps1`

## Command Executed

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-story-1-2.ps1 -SupabaseDbUrl "postgresql://runtime-db" -ClientCode "accmed" -CorsAllowOrigins "http://127.0.0.1:4173"
```

Exit code: `1`

## Raw Console Output

```text
=== Story 1.2 Robustness Matrix ===
Repo: C:\Users\dmene\Projetos\innovai\git\swaif_LTV-mentor
Backend: C:\Users\dmene\Projetos\innovai\git\swaif_LTV-mentor\backend
API: http://127.0.0.1:8000
Log dir: C:\Users\dmene\Projetos\innovai\git\swaif_LTV-mentor\.tmp_story_1_2_validation

=== Scenario 1 - production-like + mentor/admin checks ===

=== Scenario 2 - production-like without SUPABASE_DB_URL ===

=== Scenario 3 - local success path ===

=== Scenario 4 - domain_not_ready coverage via pytest ===
..                                                                       [100%]
============================== warnings summary ===============================
app\main.py:8
app\main.py:8
  C:\Users\dmene\Projetos\innovai\git\swaif_LTV-mentor\backend\app\main.py:8: DeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    from app.api.errors import http_exception_handler, request_validation_exception_handler

app\main.py:131
  C:\Users\dmene\Projetos\innovai\git\swaif_LTV-mentor\backend\app\main.py:131: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    @app.on_event("startup")

.vendor\fastapi\applications.py:4599
  C:\Users\dmene\Projetos\innovai\git\swaif_LTV-mentor\backend\.vendor\fastapi\applications.py:4599: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    return self.router.on_event(event_type)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
2 passed, 4 warnings in 1.67s

=== Summary ===

Test                             Passed Details                        
----                             ------ -------                        
scenario_1_execution              False Backend not ready (Scenario 1).
scenario_2_execution              False Backend not ready (Scenario 2).
scenario_3_execution              False Backend not ready (Scenario 3).
domain_not_ready_coverage_pytest   True exit_code=0                    


[ERR] Robustness matrix failed: 3 test(s).
```

## Scenario Result Summary

| Scenario | Result | Details |
| --- | --- | --- |
| `scenario_1_execution` | Failed | Backend not ready (Scenario 1) |
| `scenario_2_execution` | Failed | Backend not ready (Scenario 2) |
| `scenario_3_execution` | Failed | Backend not ready (Scenario 3) |
| `domain_not_ready_coverage_pytest` | Passed | exit_code=0 |

## Notes

- The matrix script reached pytest execution and validated the `domain_not_ready` coverage path successfully.
- The first three scenarios failed at backend readiness check; no API-level assertions were executed for those scenarios.

---

## Rerun 1 (Hardened Script, `-SkipPytest`)

Command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-story-1-2.ps1 -SupabaseDbUrl "postgresql://runtime-db" -ClientCode "accmed" -CorsAllowOrigins "http://127.0.0.1:4173" -SkipPytest
```

Exit code: `1`

Summary:

| Test | Passed | Details |
| --- | --- | --- |
| `mentor_blocked_admin_endpoint` | `True` | status=403 |
| `json_fallback_forbidden_production_like` | `False` | status=409, `error.code` not extracted, raw body empty |
| `postgres_runtime_unavailable` | `False` | status=409, `error.code` not extracted, raw body empty |
| `local_success_indicator_load` | `True` | status=200 |
| `domain_not_ready_coverage_pytest` | `True` | skipped by `-SkipPytest` |

Observation:
- Startup/readiness became deterministic for scenarios 1-3 after hardening.
- Remaining failures are now isolated to response-body extraction for the two expected `409` paths.

---

## Rerun 2 (Hardened Script, Full Run)

Command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-story-1-2.ps1 -SupabaseDbUrl "postgresql://runtime-db" -ClientCode "accmed" -CorsAllowOrigins "http://127.0.0.1:4173"
```

Exit code: `1`

Summary:

| Test | Passed | Details |
| --- | --- | --- |
| `mentor_blocked_admin_endpoint` | `True` | status=403 |
| `json_fallback_forbidden_production_like` | `False` | status=409, `error.code` not extracted, raw body empty |
| `postgres_runtime_unavailable` | `False` | status=409, `error.code` not extracted, raw body empty |
| `local_success_indicator_load` | `True` | status=200 |
| `domain_not_ready_coverage_pytest` | `True` | `exit_code=0` (`2 passed`) |

Additional diagnostics now emitted by script:
- Per-scenario uvicorn logs:
  - `.tmp_story_1_2_validation/scenario1-uvicorn.stdout.log`
  - `.tmp_story_1_2_validation/scenario1-uvicorn.stderr.log`
  - `.tmp_story_1_2_validation/scenario2-uvicorn.stdout.log`
  - `.tmp_story_1_2_validation/scenario2-uvicorn.stderr.log`
  - `.tmp_story_1_2_validation/scenario3-uvicorn.stdout.log`
  - `.tmp_story_1_2_validation/scenario3-uvicorn.stderr.log`

---

## Rerun 3 (No-JSON Endpoint Policy, `-SkipPytest`)

Command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-story-1-2.ps1 -SupabaseDbUrl "postgresql://runtime-db" -ClientCode "accmed" -CorsAllowOrigins "http://127.0.0.1:4173" -SkipPytest
```

Exit code: `0`

Summary:

| Test | Passed | Details |
| --- | --- | --- |
| `mentor_blocked_admin_endpoint` | `True` | `status=403`, `code=AUTH_FORBIDDEN` |
| `production_like_uses_postgres_path` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `postgres_runtime_unavailable` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `local_without_db_url_runtime_unavailable` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `domain_not_ready_coverage_pytest` | `True` | skipped by `-SkipPytest` |

Interpretation:
- JSON path is no longer accepted for this endpoint.
- Without working Postgres runtime (`SUPABASE_DB_URL` valid + psycopg/connection), the endpoint fails closed with standardized `POSTGRES_RUNTIME_UNAVAILABLE`.

---

## Rerun 4 (No-JSON Endpoint Policy, Full Run)

Command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-story-1-2.ps1 -SupabaseDbUrl "postgresql://runtime-db" -ClientCode "accmed" -CorsAllowOrigins "http://127.0.0.1:4173"
```

Exit code: `0`

Summary:

| Test | Passed | Details |
| --- | --- | --- |
| `mentor_blocked_admin_endpoint` | `True` | `status=403`, `code=AUTH_FORBIDDEN` |
| `production_like_uses_postgres_path` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `postgres_runtime_unavailable` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `local_without_db_url_runtime_unavailable` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `domain_not_ready_coverage_pytest` | `True` | `exit_code=0` (`2 passed`) |

Interpretation:
- Robustness matrix now passes end-to-end.
- Endpoint policy is consistent with “no JSON fallback”: all non-Postgres-ready paths fail with explicit runtime-unavailable envelope.

---

## Rerun 5 (No JSON env for measurement/checkpoint, `-SkipPytest`)

Command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-story-1-2.ps1 -SkipPytest
```

Exit code: `0`

Summary:

| Test | Passed | Details |
| --- | --- | --- |
| `mentor_blocked_admin_endpoint` | `True` | `status=403`, `code=AUTH_FORBIDDEN` |
| `production_like_uses_postgres_path` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `postgres_runtime_unavailable` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `local_without_db_url_runtime_unavailable` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `domain_not_ready_coverage_pytest` | `True` | skipped by `-SkipPytest` |

Interpretation:
- Script no longer exports `MEASUREMENT_STORE_PATH` / `CHECKPOINT_STORE_PATH`.
- Indicator initial-load path remains fail-closed on Postgres runtime availability.

---

## Rerun 6 (No JSON env for measurement/checkpoint, Full Run)

Command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-story-1-2.ps1
```

Exit code: `0`

Summary:

| Test | Passed | Details |
| --- | --- | --- |
| `mentor_blocked_admin_endpoint` | `True` | `status=403`, `code=AUTH_FORBIDDEN` |
| `production_like_uses_postgres_path` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `postgres_runtime_unavailable` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `local_without_db_url_runtime_unavailable` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `domain_not_ready_coverage_pytest` | `True` | `exit_code=0` (`2 passed`) |

Interpretation:
- Matrix remains green after removing JSON runtime env wiring for indicator stores.
- Current runtime still needs a valid reachable Postgres and installed `psycopg` to return `200` on scenario 1.

---

## Rerun 7 (After psycopg install, Full Run)

Command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-story-1-2.ps1
```

Exit code: `0`

Summary:

| Test | Passed | Details |
| --- | --- | --- |
| `mentor_blocked_admin_endpoint` | `True` | `status=403`, `code=AUTH_FORBIDDEN` |
| `production_like_uses_postgres_path` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `postgres_runtime_unavailable` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `local_without_db_url_runtime_unavailable` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `domain_not_ready_coverage_pytest` | `True` | `exit_code=0` (`2 passed`) |

Interpretation:
- `psycopg` is now installed in `backend/.vendor`.
- Scenario 1 still returns `POSTGRES_RUNTIME_UNAVAILABLE` because the script uses a placeholder DB URL by default (`postgresql://runtime-db`) and no real Supabase URL is configured.

---

## Rerun 8 (Real Supabase runtime + migration 009, Full Run)

Pre-steps:
- Confirmed `SUPABASE_DB_URL` in `backend/.env` is a PostgreSQL DSN (masked validation only).
- Applied `backend/scripts/supabase/sql/009_runtime_measurements_checkpoints_v1.sql` in Supabase.

Command:

```powershell
Set-Location scripts
.\validate-story-1-2.ps1 -SupabaseDbUrl "<REAL_SUPABASE_DB_URL>"
```

Exit code: `0`

Summary:

| Test | Passed | Details |
| --- | --- | --- |
| `mentor_blocked_admin_endpoint` | `True` | `status=403`, `code=AUTH_FORBIDDEN` |
| `production_like_uses_postgres_path` | `True` | `status=200` (success path on real Supabase runtime) |
| `postgres_runtime_unavailable` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `local_without_db_url_runtime_unavailable` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `domain_not_ready_coverage_pytest` | `True` | `exit_code=0` (`2 passed`) |

Interpretation:
- Scenario 1 now validates the production-like success path (`200`) against real Supabase runtime.
- No-JSON policy remains enforced on non-ready paths (`POSTGRES_RUNTIME_UNAVAILABLE`, no silent JSON fallback).

---

## Rerun 9 (Scenario 1 strict `200` gate, Real Supabase runtime)

Change before rerun:
- Updated `scripts/validate-story-1-2.ps1` so `production_like_uses_postgres_path` passes **only** when Scenario 1 returns `200`.

Command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-story-1-2.ps1 -SupabaseDbUrl "<REAL_SUPABASE_DB_URL>"
```

Exit code: `0`

Summary:

| Test | Passed | Details |
| --- | --- | --- |
| `mentor_blocked_admin_endpoint` | `True` | `status=403`, `code=AUTH_FORBIDDEN` |
| `production_like_uses_postgres_path` | `True` | `status=200` |
| `postgres_runtime_unavailable` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `local_without_db_url_runtime_unavailable` | `True` | `status=409`, `code=POSTGRES_RUNTIME_UNAVAILABLE` |
| `domain_not_ready_coverage_pytest` | `True` | `exit_code=0` (`2 passed`) |

Additional focused regression:

```powershell
Set-Location backend
$env:PYTHONPATH='.vendor;.'
python -m pytest tests/unit/test_indicator_carga_service.py tests/api/test_admin_indicator_load_api.py -q --basetemp .tmp_pytest_story_1_2_review
```

Result: `12 passed`.

Interpretation:
- Robustness matrix remains green with strict success criteria for Scenario 1.
- Story readiness signal is now deterministic for real Supabase validation (no acceptance of `409` on Scenario 1).
