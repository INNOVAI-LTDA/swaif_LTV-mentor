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
- Current local baseline values: `http://127.0.0.1:4173` + `/accmed/` + `http://127.0.0.1:8000` with `CLIENT_NAME=Acelerador Médico (AccMed)` and `APP_NAME=Gamma`
- Current persistence posture: `single-server JSON pilot recommended only for initial controlled client usage under explicit operating constraints`
- Current mentor data posture: `mentor-demo routes are isolated from the published frontend path and remain available only for explicit local internal validation`
- Current operator-safety posture: `local backup/restore utility available with a shared storage I/O lock in a writable temp location keyed to the JSON store set; backend startup now logs mentor-demo policy source explicitly and remote mentor-demo enablement requires a second approval flag; restore remains best-effort across multiple JSON files and remote go-live still requires rehearsal evidence`

## Status Model

- `pending`: not started
- `in_progress`: actively being executed
- `blocked`: cannot proceed without resolving a blocker
- `done`: complete with evidence attached
- `waived`: intentionally excluded from this release with explicit approval

## Blocking Decisions

| Decision | Owner | Status | Deadline | Resolution | Evidence |
| -------- | ----- | ------ | -------- | ---------- | -------- |
| Decide whether JSON-file persistence is acceptable for initial client usage | `preencher` | `in_progress` | `before remote staging` | `Recommended posture: acceptable only for an initial single-server client pilot with local-disk storage, one active backend instance, rehearsal-backed backups, maintenance-window restore, and no scale-out or high-concurrency expectation. If those constraints are not acceptable, escalate to database migration before staging.` | `EV-007, EV-009` |
| Decide whether mentor demo endpoints remain valid for the first client release | `dmene` | `in_progress` | `before remote staging` | `Published frontend path now excludes mentor-demo surfaces by default. Keep the route family restricted to explicit local/internal validation unless a later product decision reintroduces a real mentor surface backed by non-demo contracts.` | `EV-005, EV-011` |
| Confirm whether `ENABLE_MENTOR_DEMO_ROUTES` stays disabled on remote environments | `preencher` | `in_progress` | `Remote enablement now requires ALLOW_REMOTE_MENTOR_DEMO_ROUTES=true as an explicit second approval.` | `preencher` | `EV-008` |
| Confirm client domain, subpath strategy, TLS, and reverse-proxy rewrite model | `dmene` | `in_progress` | `before 4-2` | `Local baseline fixed as 127.0.0.1 + /accmed/. Remote origin, TLS, and reverse-proxy values still need operator confirmation.` | `EV-011` |
| Confirm whether aluno is part of the real launch scope | `preencher` | `pending` | `preencher` | `preencher` | `preencher` |

## Gate Tracker

| Gate | Owner | Status | Evidence | Active blocker | Next action |
| ---- | ----- | ------ | -------- | -------------- | ----------- |
| 1. Auth and access hardening | `dmene` | `done` | `EV-002, EV-005, EV-010` | `nenhum` | `manter evidencias e repetir apenas em staging se houver regressao` |
| 2. Routing and hosting validation | `dmene` | `in_progress` | `EV-010, EV-011` | `Deep refresh and browser-level validation still need the real hosted environment` | `Use the fixed /accmed/ baseline when validating rewrite and protected navigation under the real host in 4-2` |
| 3. Env contract and API integration | `dmene` | `in_progress` | `EV-010, EV-011` | `Local proof is recorded, but browser-origin, real CORS, and published non-localhost validation still require staging` | `Carry the local /accmed/ baseline into 4-2 and validate the published backend origin there` |
| 4. Branding and client copy | `dmene` | `in_progress` | `EV-005, EV-010, EV-011` | `A baseline local branding set is fixed, but the final remote assets and copy review are still pending` | `Use Acelerador Médico (AccMed) + Gamma as the current baseline and finalize the published assets before staging smoke` |
| 5. Demo residue cleanup | `dmene` | `in_progress` | `EV-005, EV-011` | `O scan amplo do repositorio ainda encontra referencias internas em docs, testes e codigo explicitamente gated; a superficie publicada agora isola mentor-demo, mas a decisao final sobre eventual produto mentor continua pendente` | `Manter mentor-demo apenas no caminho interno local e repetir o scan de superficie publicada em 4-2` |
| 6. Observability and controlled failure | `dmene` | `in_progress` | `EV-003, EV-008, EV-010` | `Ainda falta a validacao manual em browser para backend indisponivel e expiracao de sessao no host real` | `Executar os cenarios de falha controlada em 4-2` |
| 7. Release quality and smoke evidence | `dmene` | `in_progress` | `EV-001, EV-002, EV-003, EV-010` | `A navegacao integrada em browser e o smoke remoto ainda nao foram executados` | `Usar 4-2 para completar o smoke hospedado` |
| 8. Deploy documentation and operator readiness | `dmene` | `in_progress` | `EV-008, EV-010` | `Os artefatos estao prontos, mas ainda faltam os parametros reais do ambiente remoto e a revisao pelo operador final` | `Preencher os valores reais em 4-1 e revisar o runbook antes do staging` |
| 9. Persistence and backup posture | `preencher` | `in_progress` | `EV-007, EV-009` | `Owner approval of the constrained JSON pilot model is still pending` | `approve constrained pilot posture or escalate to persistence migration` |

## Evidence Ledger

Record every artifact used to approve a gate.

| Evidence ID | Gate | Artifact | Source path or URL | Recorded by | Date | Notes |
| ----------- | ---- | -------- | ------------------ | ----------- | ---- | ----- |
| EV-001 | `7` | `frontend build log` | `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.build.log` | `dmene` | `2026-03-20` | `Client-safe local build passed with VITE_DEPLOY_TARGET=client, VITE_API_BASE_URL=http://127.0.0.1:8000, and VITE_APP_BASE_PATH=/cliente/.` |
| EV-002 | `1, 7` | `frontend test output` | `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.test.log` | `dmene` | `2026-03-20` | `Local frontend suite passed with 52 tests. Warnings are limited to the existing React Router future-flag notices.` |
| EV-003 | `6, 7` | `backend targeted validation output` | `_bmad-output/implementation-artifacts/local-validation-20260320/backend.targeted-tests.log` | `dmene` | `2026-03-20` | `Targeted backend validation passed with 32 tests, covering runtime config, storage maintenance, bootstrap, CORS config, and health.` |
| EV-004 | `preencher` | `staging smoke record` | `preencher` | `preencher` | `preencher` | `preencher` |
| EV-005 | `1, 4, 5` | `residue scan output` | `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.residue-scan.log` | `dmene` | `2026-03-20` | `The broad repo scan still returns intentional local-only or non-published references in docs, tests, Vite local config, and explicitly gated preview code. Client-facing residue removed in Story 1.2 remains the release posture, and the published frontend path now keeps mentor-demo outside the default surface.` |
| EV-006 | `preencher` | `operator signoff` | `preencher` | `preencher` | `preencher` | `preencher` |
| EV-007 | `9` | `backup snapshot verification` | `backend/backups/snapshot-20260320T131601Z` | `dmene` | `2026-03-20` | `Local backup, verify, and restore rehearsal completed after moving the shared storage I/O lock to a writable temp location keyed to the resolved JSON store set and validating the split-directory layout case; rollback snapshot: backend/backups/pre-restore-20260320T131618Z; current posture still requires maintenance-window restore for the JSON pilot` |
| EV-008 | `6` | `startup posture log` | `backend startup log with backend_runtime_configured/backend_startup_complete` | `dmene` | `2026-03-20` | `Startup posture now records app_env, cors_origins, mentor_demo_routes, mentor_demo_policy, storage_root, and backup_dir. Remote mentor-demo enablement requires ALLOW_REMOTE_MENTOR_DEMO_ROUTES=true together with ENABLE_MENTOR_DEMO_ROUTES=true.` |
| EV-009 | `9` | `JSON pilot operating model recommendation` | `docs/client-launch-runbook.md#json-pilot-operating-model` | `dmene` | `2026-03-20` | `Documented the recommended operating constraints that make the current JSON-backed pilot acceptable only for limited initial client usage. Final owner approval is still required before remote staging.` |
| EV-010 | `2, 3, 7, 8` | `local production validation package` | `_bmad-output/implementation-artifacts/local-validation-20260320/` | `dmene` | `2026-03-20` | `Contains backend startup posture log, backend API validation JSON, frontend client-safe build log, local /cliente/ serve check, and frontend dist scan. This is local-only evidence; browser-rendered checks and remote-host validation remain for later stories.` |
| EV-011 | `2, 3, 4, 5, 8` | `current local parameter baseline` | `_bmad-output/implementation-artifacts/local-validation-20260320/frontend.build.accmed.log` | `dmene` | `2026-03-20` | `Frontend rebuilt successfully with FRONTEND_ORIGIN=http://127.0.0.1:4173, FRONTEND_BASE_PATH=/accmed/, BACKEND_API_URL=http://127.0.0.1:8000, CLIENT_NAME=Acelerador Médico (AccMed), APP_NAME=Gamma, and the published path keeping VITE_ENABLE_INTERNAL_MENTOR_DEMO=false. Supporting shell-level proof: frontend.local-serve-check.accmed.json and frontend.dist-scan.accmed.json.` |

## Staging Validation Matrix

This matrix is the minimum operator-ready proof for `staging-ready`.

| Check | Expected result | Evidence | Status | Blocker |
| ----- | --------------- | -------- | ------ | ------- |
| Frontend published at target origin | App opens under the final host shape | `preencher` | `pending` | `nenhum` |
| Base path matches build config | Router and assets resolve under configured path | `preencher` | `pending` | `nenhum` |
| SPA rewrite works on deep refresh | Direct refresh of protected route returns app shell | `preencher` | `pending` | `nenhum` |
| Backend started with explicit APP_ENV | No silent local fallback at startup | `preencher` | `pending` | `nenhum` |
| Backend CORS matches frontend origin | Browser requests succeed without CORS rejection | `preencher` | `pending` | `nenhum` |
| Integrated admin flow | Login, `/app/admin`, logout succeed | `preencher` | `pending` | `nenhum` |
| Integrated mentor flow or waiver | Internal-only mentor path remains waived from the published surface or is explicitly re-approved for a local-only validation window | `preencher` | `pending` | `nenhum` |
| Integrated aluno flow or waiver | Flow approved or explicitly waived | `preencher` | `pending` | `nenhum` |
| Auth expiry and `403` handling | Session clears or access denied view behaves as designed | `preencher` | `pending` | `nenhum` |
| No localhost traffic in browser | Requests target only the published backend URL | `preencher` | `pending` | `nenhum` |

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
| `go` / `no-go` | `preencher` | `preencher` | `preencher` |
