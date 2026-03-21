# Story 3.1: local-production-validation-pass

Status: done

## Story

As a release operator,
I want one real local validation pass under explicit production-like frontend settings and explicit backend runtime settings,
so that the next evidence-tracking story is based on actual local proof instead of placeholders.

## Acceptance Criteria

1. The backend starts locally with explicit runtime env vars and emits the expected startup posture signal.
2. Local auth validation covers at least one successful login, one `/me` read, one unauthorized case, and one access-denied case against the local pilot backend.
3. A client-safe frontend build succeeds locally with explicit env vars, and the built app can be served locally for shell-level verification.
4. The story records the local evidence locations and leaves any remaining manual-only checks explicit instead of implied.

## Tasks / Subtasks

- [x] Task 1 (AC: 1, 2)
  - [x] Start the backend locally with explicit env vars and capture the startup log.
  - [x] Run local auth/access API checks against the running backend.
- [x] Task 2 (AC: 3)
  - [x] Build the frontend with `VITE_DEPLOY_TARGET=client` and explicit local pilot values.
  - [x] Serve the built app locally and verify the shell responds under the configured base path.
- [x] Task 3 (AC: 4)
  - [x] Record the local validation evidence in the story notes and, where useful, in the release tracker.
  - [x] Keep any browser-only or remote-only validation gaps explicit for the next stories.

## Dev Notes

### Why This Story Exists

Epic 2 is now stable enough to support a real local validation pass. Before moving into broader evidence population or remote staging, the repo needs one explicit local run that proves backend posture, auth checks, and frontend client-safe build behavior under operator-controlled settings.

### Relevant Files

- [client-launch-runbook.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md)
- [production-release-tracker.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/production-release-tracker.md)
- [production-readiness-sprint-plan.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/implementation-artifacts/production-readiness-sprint-plan.md)

### Implementation Guardrails

- Do not fake browser-only verification that was not actually run.
- Prefer explicit local evidence files or logged command outputs over prose-only claims.
- Keep this story focused on local validation, not remote staging.

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- Sprint handoff after Story 1.2 completion on 2026-03-20
- `_bmad-output/implementation-artifacts/local-validation-20260320/backend.local-validation.log`
- `_bmad-output/implementation-artifacts/local-validation-20260320/backend.api-validation.json`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.build.log`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.local-serve-check.json`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.dist-scan.json`

### Completion Notes List

- Backend local posture was validated under explicit env vars: `APP_ENV=local`, `CORS_ALLOW_ORIGINS=http://127.0.0.1:4173`, `ENABLE_MENTOR_DEMO_ROUTES=true`, `ALLOW_REMOTE_MENTOR_DEMO_ROUTES=false`, and `STORAGE_BACKUP_DIR=backups`.
- Local API checks proved one successful admin login, one `/me` read, one unauthorized `401`, and one mentor-to-admin `403` denial against the local pilot backend. The runtime summary captured the expected startup posture fields.
- The frontend now builds successfully in client-safe mode against the local pilot backend with `VITE_DEPLOY_TARGET=client`, `VITE_API_BASE_URL=http://127.0.0.1:8000`, and `VITE_APP_BASE_PATH=/cliente/`.
- A local serve/fetch check confirmed the built shell responds at `/cliente/` and serves hashed assets under `/cliente/assets/`.
- Remaining gaps are explicit: no real browser-rendered validation was run in this story, the local build intentionally points at the local loopback backend, and all remote-host checks remain for the staging stories.

### File List

- `frontend/src/features/student/pages/StudentPage.tsx`
- `docs/production-release-tracker.md`
- `docs/client-launch-runbook.md`
- `_bmad-output/implementation-artifacts/local-validation-20260320/backend.local-validation.log`
- `_bmad-output/implementation-artifacts/local-validation-20260320/backend.api-validation.json`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.build.log`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.local-serve-check.json`
- `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.dist-scan.json`
