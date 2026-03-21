# Story 4.1: staging-environment-parameterization

Status: done

## Story

As a release operator,
I want the current deployment parameter set fixed in the release artifacts,
so that the next hosted validation story runs against explicit values instead of placeholders.

## Acceptance Criteria

1. The release tracker records the current deployment baseline values for frontend origin, base path, backend API URL, backend `APP_ENV`, backend `CORS_ALLOW_ORIGINS`, client name, and app name.
2. The deploy checklist and runbook reflect the same baseline values without conflicting placeholder examples for the current local dry-run posture.
3. The frontend is rebuilt successfully with the chosen `/accmed/` base path and the resulting local shell-level proof is recorded.
4. Any still-missing remote-only inputs remain explicit blockers instead of being silently invented.

## Tasks / Subtasks

- [x] Task 1 (AC: 1, 4)
  - [x] Record the provided local baseline values in the release tracker.
  - [x] Keep real hosted origin, TLS, and remote staging specifics as future blockers.
- [x] Task 2 (AC: 2)
  - [x] Update the checklist control fields and runbook examples to match the current local baseline.
  - [x] Correct any stale local examples that conflict with the actual validation setup.
- [x] Task 3 (AC: 3)
  - [x] Rebuild the frontend with `VITE_APP_BASE_PATH=/accmed/` and the selected client/app names.
  - [x] Record a local serve/dist proof package for `/accmed/`.

## Dev Notes

### Why This Story Exists

Epic 4 begins with parameterization, but the repo still carried generic placeholders and `/cliente/` examples. This story locks the current local baseline around `Acelerador Médico (AccMed)`, `Gamma`, and `/accmed/` so the next hosted validation story starts from one coherent configuration.

### Relevant Files

- [production-release-tracker.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/production-release-tracker.md)
- [frontend-deployment-readiness-checklist.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/frontend-deployment-readiness-checklist.md)
- [client-launch-runbook.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md)
- [production-readiness-sprint-plan.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/implementation-artifacts/production-readiness-sprint-plan.md)
- [sprint-status.yaml](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/implementation-artifacts/sprint-status.yaml)

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.build.accmed.log`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.local-serve-check.accmed.json`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.dist-scan.accmed.json`

### Completion Notes List

- The current local baseline is now fixed to `http://127.0.0.1:4173` + `/accmed/` + `http://127.0.0.1:8000` with `APP_ENV=local` and `CORS_ALLOW_ORIGINS=http://127.0.0.1:4173`.
- Client-facing naming for the current baseline is `Acelerador Médico (AccMed)` + `Gamma`.
- The frontend rebuilt successfully with `/accmed/`, and local shell-level proof was recorded.
- Remote host, TLS, and final non-local staging values remain open and explicit for Story `4.2`.

### File List

- `docs/production-release-tracker.md`
- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- `docs/client-launch-runbook.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/production-readiness-sprint-plan.md`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.build.accmed.log`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.local-serve-check.accmed.json`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.dist-scan.accmed.json`
