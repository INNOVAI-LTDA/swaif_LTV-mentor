# Production Release Tracker

Date: 2026-03-20

## Purpose

Track objective evidence for the client-launch rollout without losing the original release gate. This tracker is the operational companion to `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`.

## Release Summary

| Field | Value |
| ---- | ----- |
| Release ID | `local-accmed-20260320` |
| Release target | `staging-ready (local baseline)` |
| Frontend origin | `http://127.0.0.1:4173` |
| Base path | `/accmed/` |
| Backend API URL | `http://127.0.0.1:8000` |
| Backend APP_ENV | `local` |
| Backend CORS_ALLOW_ORIGINS | `http://127.0.0.1:4173` |
| Deploy operator | `dmene` |
| Technical owner | `dmene` |
| Planned deploy date | `2026-03-20 (local parameter baseline)` |

## Current Release Posture

- Current target: `staging-ready`, then `client-ready`
- Current local baseline values: http://127.0.0.1:4173 + /accmed/ + http://127.0.0.1:8000 with CLIENT_NAME=Acelerador Médico (AccMed) and APP_NAME=Gamma
- Hosted deployment contract for staging validation: VITE_APP_BASE_PATH=/ on the published host
- Current persistence posture: `single-server JSON pilot recommended only for initial controlled client usage under explicit operating constraints`
- Current mentor data posture: `mentor workspace is now published by default; any remaining mentor-demo naming is treated as technical legacy rather than a published-access gate`
- Current decision posture (2026-05-17): `go (piloto controlado)` with mentor-first operational scope, explicit waivers, and incremental post-launch hardening
- Tracker/runbook deploy-posture alignment check (2026-05-16): local baseline remains `127.0.0.1 + /accmed/ + 127.0.0.1 backend` for dry-run evidence, while hosted validation contract remains `VITE_APP_BASE_PATH=/` with explicit backend origin + CORS and remote mentor-demo disabled (`ENABLE_MENTOR_DEMO_ROUTES=false`, `ALLOW_REMOTE_MENTOR_DEMO_ROUTES=false`).

## Status Model

- `pending`: not started
- `in_progress`: actively being executed
- `blocked`: cannot proceed without resolving a blocker
- `done`: complete with evidence attached
- `waived`: intentionally excluded from this release with explicit approval

## Blocking Decisions

| Decision | Owner | Status | Deadline | Resolution | Evidence |
| -------- | ----- | ------ | -------- | ---------- | -------- |
| Decide whether JSON-file persistence is acceptable for initial client usage | `dmene` | `done` | `2026-05-17` | `Approved for controlled pilot under existing constraints (single backend instance, maintained backups, maintenance-window restore). Migration remains a follow-up track, not a launch blocker.` | `EV-007, EV-009, EV-012` |
| Decide whether mentor demo endpoints remain valid for the first client release | `dmene` | `in_progress` | `before go/no-go recheck (2026-05-22)` | `Published mentor login remains enabled by default; follow-up cleanup for legacy mentor-demo naming is tracked as a non-blocking technical debt item for a later slice.` | `EV-005, EV-011, EV-012` |
| Confirm whether `ENABLE_MENTOR_DEMO_ROUTES` stays disabled on remote environments | `dmene` | `done` | `2026-05-16` | `Remote posture is constrained to ENABLE_MENTOR_DEMO_ROUTES=false and ALLOW_REMOTE_MENTOR_DEMO_ROUTES=false for normal staging/client flows.` | `EV-008, EV-012` |
| Confirm client domain, subpath strategy, TLS, and reverse-proxy rewrite model | `dmene` | `in_progress` | `post-launch checkpoint (2026-05-22)` | `Published host/TLS baseline is active and deep-route host reachability is evidenced. Remaining query-preservation/auth-loop checks move to post-launch hardening window.` | `EV-004, EV-011, EV-012` |
| Confirm whether aluno is part of the real launch scope | `dmene` | `waived` | `waiver review (2026-05-22)` | `Pilot launch proceeds with mentor-first scope. Aluno full validation remains tracked as a timeboxed post-launch commitment.` | `EV-004, EV-006, EV-012` |
## Gate Tracker

| Gate | Owner | Status | Evidence | Active blocker | Next action |
| ---- | ----- | ------ | -------- | -------------- | ----------- |
| 1. Auth and access hardening | `dmene` | `done` | `EV-002, EV-005, EV-010` | `nenhum` | `manter evidencias e repetir apenas em staging se houver regressao` |
| 2. Routing and hosting validation | `dmene` | `in_progress` | `EV-004, EV-010, EV-011` | `Hosted deep-refresh baseline is captured and mentor protected-route behavior is partially evidenced; remaining query-preservation/admin-aluno checks are post-launch hardening items` | `Complete pending query-preservation/admin-aluno route checks in post-launch window` |
| 3. Env contract and API integration | `dmene` | `in_progress` | `EV-004, EV-010, EV-011, EV-013, EV-014` | `Published CORS and readiness probes are captured; hosted startup-log proof and broader authenticated coverage remain post-launch` | `Attach hosted startup posture log and extend runtime host evidence incrementally` |
| 4. Branding and client copy | `dmene` | `waived` | `EV-004, EV-005, EV-010, EV-011` | `Minor hosted branding/copy refinements are accepted as non-blocking for controlled pilot` | `Close residual branding checks during incremental post-launch cycle` |
| 5. Demo residue cleanup | `dmene` | `in_progress` | `EV-005, EV-011` | `Internal mentor-demo legacy naming remains, but current published posture is already controlled` | `Track cleanup in a follow-up slice without blocking current no-go remediation` |
| 6. Observability and controlled failure | `dmene` | `in_progress` | `EV-003, EV-004, EV-008, EV-010, EV-013, EV-014` | `Core 401 and backend-unavailable fallback evidence captured; 422 envelope reconfirmed on hosted probe; 403/409 integrated depth remains iterative hardening` | `Capture 403/409 integrated behavior in post-launch iterations` |
| 7. Release quality and smoke evidence | `dmene` | `in_progress` | `EV-001, EV-002, EV-003, EV-004, EV-010, EV-013, EV-014` | `Mentor-first smoke path is evidenced; admin/aluno depth remains incremental due to missing authenticated probe credentials` | `Complete remaining role-flow matrix without interrupting pilot availability` |
| 8. Deploy documentation and operator readiness | `dmene` | `in_progress` | `EV-004, EV-008, EV-010` | `Operational baseline is sufficient for controlled pilot; signoff hardening remains open` | `Update operator signoff evidence during post-launch checkpoint` |
| 9. Persistence and backup posture | `dmene` | `done` | `EV-007, EV-009, EV-012` | `Constrained JSON pilot approved for launch under documented operating model` | `Maintain rehearsal cadence and revisit migration by roadmap` |
## Evidence Ledger

Record every artifact used to approve a gate.

| Evidence ID | Gate | Artifact | Source path or URL | Recorded by | Date | Notes |
| ----------- | ---- | -------- | ------------------ | ----------- | ---- | ----- |
| EV-001 | `7` | `frontend build log` | `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.build.log` | `dmene` | `2026-03-20` | `Client-safe local build passed with VITE_DEPLOY_TARGET=client, VITE_API_BASE_URL=http://127.0.0.1:8000, and VITE_APP_BASE_PATH=/cliente/.` |
| EV-002 | `1, 7` | `frontend test output` | `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.test.log` | `dmene` | `2026-03-20` | `Local frontend suite passed with 52 tests. Warnings are limited to the existing React Router future-flag notices.` |
| EV-003 | `6, 7` | `backend targeted validation output` | `_bmad-output/implementation-artifacts/local-validation-20260320/backend.targeted-tests.log` | `dmene` | `2026-03-20` | `Targeted backend validation passed with 32 tests, covering runtime config, storage maintenance, bootstrap, CORS config, and health.` |
| EV-004 | 2, 3, 4, 6, 7, 8 | staging smoke record | _bmad-output/implementation-artifacts/staging-validation-evidence-2026-05-16.md | dmene | 2026-05-16 | Partial hosted evidence now attached: published-host deep-route 200 checks, CORS explicit-origin proof (no wildcard), `/health` readiness 200, CSP Report-Only/HSTS observation, runtime login request to published API origin with 401 behavior, authenticated mentor-route runtime host capture (no localhost in captured mentor-flow requests), and backend-unavailable controlled fallback/no-loop evidence. Remaining blockers: integrated admin/aluno flows, explicit 403/409/422 integrated behavior, and hosted startup-posture log evidence. |
| EV-005 | `1, 4, 5` | `residue scan output` | `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.residue-scan.log` | `dmene` | `2026-03-20` | `The broad repo scan still returns intentional local-only or non-published references in docs, tests, Vite local config, and explicitly gated preview code. Client-facing residue removed in Story 1.2 remains the release posture, and mentor login is now part of the published surface by default.` |
| EV-006 | 8 | operator signoff | docs/production-release-tracker.md#operator-checklist | dmene | 2026-05-16 | Final remote operator signoff is still pending alongside hosted smoke completion. |
| EV-007 | `9` | `backup snapshot verification` | `backend/backups/snapshot-20260320T131601Z` | `dmene` | `2026-03-20` | `Local backup, verify, and restore rehearsal completed after moving the shared storage I/O lock to a writable temp location keyed to the resolved JSON store set and validating the split-directory layout case; rollback snapshot: backend/backups/pre-restore-20260320T131618Z; current posture still requires maintenance-window restore for the JSON pilot` |
| EV-008 | `6` | `startup posture log` | `backend startup log with backend_runtime_configured/backend_startup_complete` | `dmene` | `2026-03-20` | `Startup posture now records app_env, cors_origins, mentor_demo_routes, mentor_demo_policy, storage_root, and backup_dir. Remote mentor-demo enablement requires ALLOW_REMOTE_MENTOR_DEMO_ROUTES=true together with ENABLE_MENTOR_DEMO_ROUTES=true.` |
| EV-009 | `9` | `JSON pilot operating model recommendation` | `docs/client-launch-runbook.md#json-pilot-operating-model` | `dmene` | `2026-03-20` | `Documented the recommended operating constraints that make the current JSON-backed pilot acceptable only for limited initial client usage. Final owner approval is still required before remote staging.` |
| EV-010 | `2, 3, 7, 8` | `local production validation package` | `_bmad-output/implementation-artifacts/local-validation-20260320/` | `dmene` | `2026-03-20` | `Contains backend startup posture log, backend API validation JSON, frontend client-safe build log, local /cliente/ serve check, and frontend dist scan. This is local-only evidence; browser-rendered checks and remote-host validation remain for later stories.` |
| EV-011 | `2, 3, 4, 5, 8` | `current local parameter baseline` | `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.build.accmed.log` | `dmene` | `2026-03-20` | `Frontend rebuilt with FRONTEND_ORIGIN=http://127.0.0.1:4173, FRONTEND_BASE_PATH=/accmed/, BACKEND_API_URL=http://127.0.0.1:8000, CLIENT_NAME=Acelerador Médico (AccMed), APP_NAME=Gamma, and published posture keeping VITE_ENABLE_INTERNAL_MENTOR_DEMO=false by default.` |
| EV-012 | 9 | go/no-go decision record | _bmad-output/implementation-artifacts/4-3-go-no-go-client-pilot-decision.md | dmene | 2026-05-17 | Decision trail now records controlled pilot go-live with explicit waivers and post-launch checkpoint actions; prior 2026-05-16 no-go remains as historical decision context. |
| EV-013 | 3, 6, 7 | hosted post-launch incremental probe | _bmad-output/implementation-artifacts/post-launch-incremental-probe-2026-05-17.json (+ raw HTTP captures: `post-launch-health-2026-05-18.http`, `post-launch-422-envelope-2026-05-18.http`, `post-launch-401-invalid-token-2026-05-18.http`) | dmene | 2026-05-18 | Reconfirmed hosted readiness gate (`GET /health=200`) and standardized `422` envelope for invalid login payload; auth probes for admin/mentor/aluno candidate credentials returned `401` (no token), so integrated admin/aluno plus hosted `403`/`409` and startup-log evidence remain open without introducing new blocker classes. |
| EV-014 | 3, 6, 7 | hosted checkpoint 2026-05-22 startup posture + authenticated 403/409 matrix capture | _bmad-output/implementation-artifacts/checkpoint-2026-05-22-hosted-startup-and-403-409-auth-matrix-2026-05-18-000247.md (+ raw captures: `checkpoint-2026-05-22-health-2026-05-18-000247.http`, `checkpoint-2026-05-22-login-422-2026-05-18-000247.http`, `checkpoint-2026-05-22-admin-invalid-token-401-2026-05-18-000247.http`, `checkpoint-2026-05-22-startup-and-auth-matrix-2026-05-18-000247.json`) | dmene | 2026-05-18 | Captured hosted checkpoint evidence for health/startup posture and auth matrix preconditions. Standardized `422` and `401` envelopes were reconfirmed. Authenticated `403/409` execution remained blocked due to missing operator-approved hosted credentials, and hosted startup runtime markers with explicit `APP_ENV` remained log-access constrained in this operator environment. |

## Staging Validation Matrix

This matrix is the minimum operator-ready proof for `staging-ready`.

| Check | Expected result | Evidence | Status | Blocker |
| ----- | --------------- | -------- | ------ | ------- |
| Frontend published at target origin | App opens under the final host shape | `EV-004` | `done` | `nenhum` |
| Base path matches build config | Router and assets resolve under configured path | `EV-004` | `in_progress` | `Authenticated-path semantics and query-preservation checks still pending` |
| SPA rewrite works on deep refresh | Direct refresh of protected route returns app shell | `EV-004` | `in_progress` | `Hosted deep-refresh baseline and bounded protected-route failure behavior are captured; query-preservation and admin/aluno protected-route coverage are still pending` |
| Backend started with explicit APP_ENV | No silent local fallback at startup | `EV-004, EV-013, EV-014` | `in_progress` | `Hosted startup-log evidence is still missing; keep as post-launch hardening item under controlled pilot checkpoint (no new release blocker class)` |
| Backend CORS matches frontend origin | Browser requests succeed without CORS rejection | `EV-004` | `done` | `nenhum` |
| Integrated admin flow | Login, `/app/admin`, logout succeed | `EV-004, EV-013, EV-014` | `in_progress` | `Hosted auth probes were executed again but no authenticated session token was obtained from available operator credential set` |
| Integrated mentor flow or waiver | Mentor login succeeds and published mentor routes load under the configured frontend posture | `EV-004` | `in_progress` | `Published authenticated mentor-route coverage is captured, but explicit fresh mentor-login proof in this evidence slice is still pending` |
| Integrated aluno flow or waiver | Flow approved or explicitly waived | `EV-004, EV-006` | `waived` | `Pilot launch approved with mentor-first scope; aluno flow validation is timeboxed post-launch` |
| Auth expiry and `403` handling | Session clears or access denied view behaves as designed | `EV-004, EV-013, EV-014` | `in_progress` | `Hosted 401 and backend-unavailable controlled fallback/no-loop behavior are captured; explicit 403 integrated depth remains incremental` |
| Integrated `409` conflict handling | Conflict responses are handled with expected error envelope and UX behavior | `EV-004, EV-013, EV-014` | `in_progress` | Canonical hosted 409 scenario still requires authenticated conflict trigger path in post-launch hardening window |
| Integrated `422` validation handling | Validation errors are handled with expected error envelope and UX behavior | `EV-004, EV-013, EV-014` | `in_progress` | Hosted standardized 422 envelope was reconfirmed; integrated authenticated UX-level 422 depth remains incremental |
| No localhost traffic in browser | Requests target only the published backend URL | `EV-004` | `in_progress` | `No localhost traffic is captured for mentor authenticated flows, but admin/aluno authenticated flow coverage is still pending` |
## Operator Checklist

- [ ] Review `docs/client-launch-runbook.md` before touching the environment
- [ ] Run one local backup and restore rehearsal before remote staging
- [ ] Fill release summary and blocking decisions before staging deploy
- [ ] Attach evidence IDs to every completed gate
- [ ] Stop the deploy if any gate moves to `blocked`
- [ ] Record the final go or no-go decision below

## Final Decision

| Decision | Approved by | Date | Notes |
| -------- | ----------- | ---- | ----- |
| `go (piloto controlado)` | `dmene` | `2026-05-17` | `Decision prioritizes client availability and core value path (mentor-first metricas/pilares flow) with explicit waivers and incremental hardening. EV-004 confirms hosted reachability, CORS explicit-origin, mentor authenticated runtime host capture, and controlled backend-unavailable behavior. Pending depth checks (admin/aluno integrated coverage, explicit 403/409/422 integrated handling, and hosted startup-posture logging) are accepted as post-launch commitments with checkpoint on 2026-05-22. Operacao segue sob constrained JSON pilot model (EV-007/EV-009).` |

### Final Decision Approval Evidence

| Approver | Role | Timestamp | Approval artifact |
| -------- | ---- | --------- | ----------------- |
| `dmene` | `release owner` | `2026-05-17` | `docs/production-release-tracker.md#final-decision` |

### Post-Launch Incremental Actions (Pilot Checkpoint)
| Action | Owner | Evidence target | Checkpoint |
| ------ | ----- | --------------- | ---------- |
| Expand integrated hosted evidence for admin/aluno + protected-route depth (query-preservation and loop checks) | dmene | EV-004 | 2026-05-22 |
| Capture explicit hosted `403`/`409`/`422` integrated behavior with UX evidence | dmene | EV-004 | 2026-05-22 |
| Attach hosted backend startup posture evidence (`APP_ENV`, runtime summary, policy markers) | dmene | EV-004, EV-008 | 2026-05-22 |
| Review pilot waivers (aluno scope and branding polish) and either close or extend with justification | dmene | EV-004, EV-006 | 2026-05-22 |
