# Story 2.2: backup-restore-safety-and-rehearsal

Status: done

## Story

As a release operator,
I want the JSON backup and restore workflow to be safe enough for local pilot validation,
so that I can rehearse recovery before any remote staging or client usage.

## Acceptance Criteria

1. Backup snapshot creation is collision-safe even when two backup commands start in the same second.
2. Snapshot verification fails if the manifest omits any known JSON store or if listed entries are malformed.
3. Restore does not leave the system partially restored when one store fails mid-run; the workflow either restores all stores or rolls back to the pre-restore state as much as the current JSON architecture allows.
4. Storage-root resolution fails with a clear runtime error when configured store paths do not share a common filesystem root.
5. One local backup -> verify -> restore rehearsal is documented in the production release tracker with an evidence location.
6. Targeted backend tests cover the new backup/restore and storage-root guard behavior and pass.

## Tasks / Subtasks

- [x] Task 1 (AC: 1)
  - [x] Make snapshot directory naming collision-safe in [storage_maintenance.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/operations/storage_maintenance.py).
  - [x] Add a test that proves two backup attempts cannot fail just because they share the same second.
- [x] Task 2 (AC: 2)
  - [x] Tighten manifest verification so every known store from [catalog.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/storage/catalog.py) must be represented exactly once.
  - [x] Fail verification on malformed manifest entries before restore starts.
- [x] Task 3 (AC: 3)
  - [x] Add pre-restore snapshot or equivalent rollback protection before mutating live store files.
  - [x] Ensure restore errors do not leave a mixed partially restored state.
  - [x] Add tests that simulate restore failure and assert rollback behavior.
- [x] Task 4 (AC: 4)
  - [x] Guard [resolve_storage_root()](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/storage/catalog.py) against store paths on different drive roots or incompatible roots.
  - [x] Raise a clear runtime error instead of leaking a raw `commonpath()` failure.
- [x] Task 5 (AC: 5)
  - [x] Record the local rehearsal evidence placeholder or location in [production-release-tracker.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/production-release-tracker.md).
  - [x] Keep the tracker aligned with the runbook's backup workflow.
- [x] Task 6 (AC: 6)
  - [x] Extend [test_storage_maintenance.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/tests/test_storage_maintenance.py).
  - [x] Extend [test_runtime_config.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/tests/test_runtime_config.py) if runtime error paths change.
  - [x] Run the targeted backend pytest command for this slice.

## Dev Notes

### Why This Story Exists

The current local production-readiness slice added JSON snapshot tooling, startup posture logging, and mentor-demo route gating. The latest edge-case review found five closure gaps that make the backup and restore path unsafe for real operator rehearsal. This story exists to close those gaps before local evidence collection or remote staging.

### Current Review Findings To Close

1. Backup directory names can collide when two backups start in the same second.
2. Snapshot creation can mix different store versions because files are copied one by one without a broader snapshot guard.
3. Manifest verification is not strict enough to guarantee all known stores are present.
4. Restore can leave stores partially restored if a later store fails.
5. Storage-root discovery can crash unexpectedly when store paths live on different roots.

### Relevant Files

- [storage_maintenance.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/operations/storage_maintenance.py)
- [catalog.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/storage/catalog.py)
- [io_gate.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/storage/io_gate.py)
- [json_repository.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/storage/json_repository.py)
- [store_registry.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/storage/store_registry.py)
- [runtime.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/config/runtime.py)
- [test_storage_maintenance.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/tests/test_storage_maintenance.py)
- [test_runtime_config.py](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/tests/test_runtime_config.py)
- [production-release-tracker.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/production-release-tracker.md)

### Architecture Compliance

- Keep backend route files thin. This story should stay inside runtime, storage, and test layers unless a documentation update is required.
- Preserve repository-backed persistence boundaries. Do not introduce ad hoc file handling in unrelated services or routes.
- Keep changes brownfield-safe. This is a safety-hardening pass for the current JSON pilot, not a persistence redesign.
- Keep error handling explicit and operator-oriented. Fail fast with clear runtime errors instead of silent fallback.

### File Structure Requirements

- Operational code belongs under `backend/app/operations`.
- Storage topology helpers belong under `backend/app/storage`.
- Runtime env helpers remain in `backend/app/config/runtime.py`.
- Backend tests stay under `backend/tests` and should be placed at the nearest relevant layer.

### Implementation Guardrails

- Do not replace the JSON storage model in this story. Only make the current pilot tooling safer.
- Do not widen the scope into staging deployment or frontend validation.
- Do not remove `mentor-demo` here unless that is required by a runtime-safety fix. The product decision remains separate in Story `2-3`.
- Prefer explicit rollback mechanics over "best effort" restore when a failure can leave mixed store state.
- If perfect atomic multi-file restore is not practical, document and enforce the safest available rollback within the current architecture.

### Testing Requirements

- Add or update tests for:
  - snapshot name collision handling
  - manifest completeness validation
  - partial-restore rollback or fail-safe behavior
  - multi-root storage path guard behavior
- Preserve existing passing tests for runtime config, bootstrap, CORS, and health.
- Verification command:

```bash
py -m pytest tests/test_runtime_config.py tests/test_storage_maintenance.py tests/test_bootstrap.py tests/test_cors_config.py tests/test_health.py -q
```

### Local Rehearsal Requirement

After code changes, run one real local rehearsal using the operator flow:

```bash
py -m app.operations.storage_maintenance backup
py -m app.operations.storage_maintenance verify <snapshot_dir>
py -m app.operations.storage_maintenance restore <snapshot_dir>
```

Record the snapshot directory or evidence location in [production-release-tracker.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/production-release-tracker.md).

### Project Structure Notes

- The repo has no dedicated production-readiness epics file yet. This story is derived from:
  - [production-readiness-sprint-plan.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/implementation-artifacts/production-readiness-sprint-plan.md)
  - [tech-spec-production-readiness-rollout-client-launch.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/implementation-artifacts/tech-spec-production-readiness-rollout-client-launch.md)
- `sprint-status.yaml` is the tracking source of truth for the current solo-agent workflow.

### References

- [production-readiness-sprint-plan.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/implementation-artifacts/production-readiness-sprint-plan.md)
- [tech-spec-production-readiness-rollout-client-launch.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/implementation-artifacts/tech-spec-production-readiness-rollout-client-launch.md)
- [project-context.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/project-context.md)
- [client-launch-runbook.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md)
- [production-release-tracker.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/production-release-tracker.md)

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- Edge-case review findings for the local production-readiness slice on 2026-03-20
- `py -m pytest tests/test_runtime_config.py tests/test_storage_maintenance.py tests/test_bootstrap.py tests/test_cors_config.py tests/test_health.py -q`
- `py -m app.operations.storage_maintenance backup`
- `py -m app.operations.storage_maintenance verify C:\Users\dmene\Projetos\innovai\repos\swaif_LTV-mentoria\backend\backups\snapshot-20260320T131601Z`
- `py -m app.operations.storage_maintenance restore C:\Users\dmene\Projetos\innovai\repos\swaif_LTV-mentoria\backend\backups\snapshot-20260320T131601Z`

### Completion Notes List

- Story created from sprint plan and current reviewed backend state.
- Replaced the old process-local maintenance assumption with a shared storage I/O lock stored in a writable temp location and keyed to the resolved JSON store set, used by both repository writes and maintenance commands.
- Implemented collision-safe snapshot directories with retry behavior and stricter snapshot payload validation before restore mutates live files.
- Wrapped rollback-verification failures inside the operator-facing restore error contract instead of leaking a lower-level verification exception.
- Kept rollback protection in place and documented the remaining best-effort limit for multi-file JSON restore under the current pilot architecture.
- Added coverage for split-directory same-drive storage layouts so the lock path remains writable and independent from backup-dir configuration.
- Completed targeted backend verification: 29 tests passed.
- Completed a fresh local backup, verify, and restore rehearsal on 2026-03-20; updated evidence recorded in the release tracker as `EV-007` with snapshot `backend/backups/snapshot-20260320T131601Z` and rollback snapshot `backend/backups/pre-restore-20260320T131618Z`.

### File List

- `backend/app/operations/storage_maintenance.py`
- `backend/app/storage/catalog.py`
- `backend/app/storage/io_gate.py`
- `backend/app/storage/json_repository.py`
- `backend/app/storage/store_registry.py`
- `backend/tests/test_storage_maintenance.py`
- `backend/tests/test_runtime_config.py`
- `docs/client-launch-runbook.md`
- `docs/production-release-tracker.md`
