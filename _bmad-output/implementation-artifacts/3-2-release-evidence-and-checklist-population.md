# Story 3.2: release-evidence-and-checklist-population

Status: done

## Story

As a release operator,
I want the local validation package attached to the real release gate artifacts,
so that Epic 4 starts from objective local evidence instead of placeholders.

## Acceptance Criteria

1. The production release tracker references the concrete local evidence files for build, tests, local API validation, and residue scan.
2. The frontend deployment readiness checklist reflects the current local evidence status and leaves remote-only gaps as explicit blockers.
3. Story `3.1` is closed in the sprint artifacts and Story `3.2` becomes the reviewed handoff point for Epic 4.
4. No checklist or tracker row claims remote staging proof that was not actually executed.

## Tasks / Subtasks

- [x] Task 1 (AC: 1)
  - [x] Capture missing local evidence logs for frontend tests, backend targeted validation, and residue scan.
  - [x] Attach those artifacts to the release tracker.
- [x] Task 2 (AC: 2, 4)
  - [x] Update the readiness checklist block controls and gate summary with local evidence-backed statuses.
  - [x] Keep staging-only and browser-only validation as unresolved blockers instead of implying completion.
- [x] Task 3 (AC: 3)
  - [x] Mark Story `3.1` as done in the sprint tracker.
  - [x] Move Story `3.2` to review and point the sprint plan at Epic 4.

## Dev Notes

### Why This Story Exists

Epic 3 is only useful if the local validation work is attached to the real operational artifacts. This story converts the current local proof package into release-gate evidence and leaves the remote-only work visible for Epic 4.

### Relevant Files

- [frontend-deployment-readiness-checklist.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/frontend-deployment-readiness-checklist.md)
- [production-release-tracker.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/production-release-tracker.md)
- [production-readiness-sprint-plan.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/implementation-artifacts/production-readiness-sprint-plan.md)
- [sprint-status.yaml](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/implementation-artifacts/sprint-status.yaml)

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.build.log`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.test.log`
- `_bmad-output/implementation-artifacts/local-validation-20260320/backend.targeted-tests.log`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.residue-scan.log`
- `_bmad-output/implementation-artifacts/local-validation-20260320/backend.local-validation.log`
- `_bmad-output/implementation-artifacts/local-validation-20260320/backend.api-validation.json`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.local-serve-check.json`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.dist-scan.json`

### Completion Notes List

- The local evidence package now includes build, tests, targeted backend validation, API posture checks, local shell serving proof, and a residue scan log.
- The release tracker references the local evidence under `EV-001`, `EV-002`, `EV-003`, `EV-005`, and `EV-010`.
- The deployment readiness checklist now reflects the local-only completion state and keeps staging/browser proof as explicit blockers.
- Story `3.1` is closed and Epic 4 is now the next execution stage.

### File List

- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- `docs/production-release-tracker.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/production-readiness-sprint-plan.md`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.build.log`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.test.log`
- `_bmad-output/implementation-artifacts/local-validation-20260320/backend.targeted-tests.log`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.residue-scan.log`
