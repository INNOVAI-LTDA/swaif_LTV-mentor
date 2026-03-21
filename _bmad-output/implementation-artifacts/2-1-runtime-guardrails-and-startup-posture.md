# Story 2.1: runtime-guardrails-and-startup-posture

Status: done

## Story

As a release operator,
I want backend runtime posture and mentor-demo routing policy to be explicit at startup,
so that local pilot validation is safe and remote environments cannot silently expose demo-oriented behavior.

## Acceptance Criteria

1. Production-like environments fail fast if `ENABLE_MENTOR_DEMO_ROUTES=true` is set without an explicit remote-approval flag.
2. Local environments retain the current default mentor-demo behavior unless explicitly disabled.
3. Startup posture logs clearly record the resolved `APP_ENV`, CORS origins, mentor-demo route state, mentor-demo policy source, storage root, and backup directory.
4. Operator docs and env examples describe the remote mentor-demo policy and the expected startup posture output.
5. Targeted backend tests cover the new runtime guardrails and pass.

## Tasks / Subtasks

- [x] Task 1 (AC: 1, 2)
  - [x] Tighten [runtime.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/config/runtime.py) so production-like environments require explicit approval before mentor-demo routes can be enabled.
  - [x] Preserve local default behavior while keeping boolean parsing explicit and fail-fast.
- [x] Task 2 (AC: 3)
  - [x] Extend [main.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/main.py) runtime summary and startup logs with operator-usable posture fields.
  - [x] Ensure the startup signal is emitted before and after storage bootstrap so operators can diagnose posture separately from repository boot issues.
- [x] Task 3 (AC: 4)
  - [x] Update [backend/.env.example](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/.env.example) with the explicit remote mentor-demo approval policy.
  - [x] Update [client-launch-runbook.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md) and [production-release-tracker.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/production-release-tracker.md) to reflect the startup posture evidence and remote policy.
- [x] Task 4 (AC: 5)
  - [x] Extend [test_runtime_config.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/tests/test_runtime_config.py) for the new approval rules and runtime summary.
  - [x] Run the targeted backend pytest command for this slice.

## Dev Notes

### Why This Story Exists

Story `2.2` closed the backup and restore mechanics, but Epic 2 is still blocked by runtime posture ambiguity. The backend currently logs a useful startup summary, yet production-like environments can still enable mentor-demo routes with a plain boolean. This story makes that remote policy explicit and operator-visible before the local production validation pass.

### Current Gaps To Close

1. Production-like environments allow `ENABLE_MENTOR_DEMO_ROUTES=true` without a second approval signal.
2. Operator posture logs do not distinguish default local mentor-demo behavior from an explicit remote approval path.
3. The runbook and tracker still describe the remote mentor-demo decision as pending without a concrete runtime contract.

### Relevant Files

- [runtime.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/config/runtime.py)
- [main.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/main.py)
- [test_runtime_config.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/tests/test_runtime_config.py)
- [backend/.env.example](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/.env.example)
- [client-launch-runbook.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md)
- [production-release-tracker.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/production-release-tracker.md)

### Architecture Compliance

- Keep runtime env parsing centralized in `backend/app/config/runtime.py`.
- Keep `main.py` responsible for app wiring and startup logging, not env parsing rules.
- Do not widen this story into persistence changes or frontend validation.
- Keep remote mentor-demo policy explicit and fail-fast instead of relying on tacit operator discipline.

### Testing Requirements

- Add or update tests for:
  - local default mentor-demo posture
  - production-like mentor-demo requiring explicit approval
  - runtime summary fields and startup posture exposure through `create_app()`
- Verification command:

```bash
py -m pytest tests/test_runtime_config.py tests/test_storage_maintenance.py tests/test_bootstrap.py tests/test_cors_config.py tests/test_health.py -q
```

### References

- [production-readiness-sprint-plan.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/implementation-artifacts/production-readiness-sprint-plan.md)
- [tech-spec-production-readiness-rollout-client-launch.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/implementation-artifacts/tech-spec-production-readiness-rollout-client-launch.md)
- [project-context.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/project-context.md)

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- Sprint plan handoff on 2026-03-20
- `py -m pytest tests/test_runtime_config.py tests/test_storage_maintenance.py tests/test_bootstrap.py tests/test_cors_config.py tests/test_health.py -q`

### Completion Notes List

- Added a central mentor-demo route policy resolver that preserves local defaults but requires `ALLOW_REMOTE_MENTOR_DEMO_ROUTES=true` before production-like environments can enable demo routes.
- Extended backend startup posture logging so both `backend_runtime_configured` and `backend_startup_complete` include `mentor_demo_policy` alongside env, CORS, storage root, and backup directory.
- Updated backend env examples and operator docs so remote mentor-demo posture is explicit and reviewable instead of implicit.
- Added runtime tests for the new remote approval guard and runtime summary exposure.
- Completed targeted backend verification: 32 tests passed.

### File List

- `backend/app/config/runtime.py`
- `backend/app/main.py`
- `backend/tests/test_runtime_config.py`
- `backend/tests/test_storage_maintenance.py`
- `backend/tests/test_bootstrap.py`
- `backend/tests/test_cors_config.py`
- `backend/tests/test_health.py`
- `backend/.env.example`
- `docs/client-launch-runbook.md`
- `docs/production-release-tracker.md`
