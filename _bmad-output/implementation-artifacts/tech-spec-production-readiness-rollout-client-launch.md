---
title: 'Production Readiness Rollout for Client Launch'
slug: 'production-readiness-rollout-client-launch'
created: '2026-03-19'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['React 18.3.1', 'React Router DOM 6.30.1', 'TypeScript 5.8.3 strict', 'Vite 5.4.21', 'Vitest 2.1.9', 'FastAPI 0.135.1', 'Python 3.13', 'JSON-file repositories']
files_to_modify: ['frontend/src/app/layout/AppLayout.tsx', 'frontend/src/pages/LoginPage.tsx', 'frontend/src/app/routes.tsx', 'frontend/src/shared/config/env.ts', 'frontend/src/main.tsx', 'frontend/src/styles/global.css', 'frontend/README.md', 'frontend/.env.example', 'backend/app/main.py', 'backend/app/config/runtime.py', 'backend/app/storage/json_repository.py', 'backend/app/storage/client_repository.py', 'backend/tests/test_cors_config.py', 'docs/mvp-mentoria/frontend-deployment-readiness-checklist.md']
code_patterns: ['frontend routing centralized in app/routes.tsx', 'frontend auth centralized in AuthProvider', 'frontend env access centralized in shared/config/env.ts', 'role-based shells and pages under feature folders', 'backend routers remain thin and services or repositories own logic', 'backend persistence is repository-based and JSON-file backed', 'release docs are treated as active engineering inputs']
test_patterns: ['frontend tests in frontend/src/test with Vitest and Testing Library', 'frontend smoke coverage around routes and auth provider flows', 'backend deploy-config tests in backend/tests', 'verification relies on build plus targeted integrated smoke tests']
---

# Tech-Spec: Production Readiness Rollout for Client Launch

**Created:** 2026-03-19

## Overview

### Problem Statement

The app has passed the recent frontend deployment-hardening slice, but it is still not a client-ready production app. The release gate in `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` still has open work around branding cleanup, demo residue removal, integrated staging validation, deploy operations, backup and restore, observability, and final go-live evidence. In parallel, the backend still persists business data through local JSON files, which is a material durability and operations risk for real client usage.

### Solution

Create a brownfield-safe production-readiness rollout spec that preserves the current frontend and backend architecture while converting the demo into a staging-ready and client-ready app. The rollout should be sliced so the team can harden branding and demo residue first, validate real server deployment next, then close operations, persistence, backup, observability, deploy runbook, and go-live smoke coverage with explicit evidence.

### Scope

**In Scope:**
- Frontend readiness blocks still open after the auth or routing or env hardening pass
- Branding and copy externalization needed for a client-targeted deployment
- Removal or isolation of remaining demo and preview residue from client-facing paths
- Staging deployment validation for SPA routing, assets, backend origin, and role flows
- Production operations baseline: config contract, secrets handling expectations, logging or observability, artifact identity, and rollback posture
- Backup and restore planning for the current backend persistence model
- Explicit treatment of JSON-file persistence risk and the minimum acceptable mitigation path for pilot or client launch
- Deploy runbook and go-live smoke checklist aligned with the readiness document

**Out of Scope:**
- A full product rewrite
- New business features unrelated to production readiness
- Large UX redesign beyond client-branding and production-copy changes
- Full backend domain redesign unrelated to persistence or deploy safety
- Multi-tenant platform rearchitecture

## Context for Development

### Codebase Patterns

- Frontend routing remains centralized in `frontend/src/app/routes.tsx`.
- Frontend auth and session behavior remains centralized in `frontend/src/app/providers/AuthProvider.tsx`.
- Frontend environment parsing is centralized in `frontend/src/shared/config/env.ts` and shared contract helpers.
- Frontend branding still surfaces through `AppLayout`, `LoginPage`, shell components, and static branding asset references, so client-brand changes need coordinated edits across shared layout and page entrypoints.
- Backend runtime entrypoint remains `backend/app/main.py`, with deploy config now split into `backend/app/config/runtime.py`.
- Backend persistence remains repository-based and JSON-file backed through `backend/app/storage`.
- JSON writes are atomic per file through `os.replace`, but storage is still local-disk single-node persistence with no database, backup, or cross-instance coordination.
- The repo-level project context requires preserving thin route files, shared error envelopes, centralized env access, and brownfield-safe incremental slices.
- The deployment checklist is detailed enough to act as a release gate, but it still needs execution slices, evidence capture, and operator-facing runbook outputs.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` | Primary release gate for the remaining production-readiness work |
| `_bmad-output/project-context.md` | Brownfield implementation rules and architectural constraints for future agents |
| `_bmad-output/implementation-artifacts/tech-spec-frontend-deployment-hardening-client-delivery.md` | Most recent completed hardening spec that closes the auth or routing or env baseline |
| `frontend/src/app/routes.tsx` | Protected route topology and client-facing surface map |
| `frontend/src/app/providers/AuthProvider.tsx` | Current session recovery, demo gating, and real-session validation behavior |
| `frontend/src/pages/LoginPage.tsx` | Current login copy, recovery UI, and remaining client-visible access patterns |
| `frontend/src/app/layout/AppLayout.tsx` | Current shell branding and top-level product naming surface |
| `frontend/src/styles/global.css` | Shared visual tokens and branding-dependent styling surface |
| `frontend/src/shared/config/env.ts` | Current frontend deploy configuration contract |
| `frontend/src/main.tsx` | Frontend bootstrap and deploy-time integration entrypoint |
| `frontend/README.md` | Existing frontend deploy notes to expand into a real runbook |
| `frontend/.env.example` | Current frontend environment example to separate local-only from client-facing examples |
| `backend/app/config/runtime.py` | Current backend deploy intent and CORS runtime contract |
| `backend/app/main.py` | Backend app startup wiring and remaining production startup responsibilities |
| `backend/app/storage/json_repository.py` | Current file-based persistence implementation and operational constraints |
| `backend/app/storage/client_repository.py` | Representative repository showing the default `backend/data/*.json` storage pattern |
| `backend/tests/test_cors_config.py` | Current backend deploy-config coverage baseline |

### Technical Decisions

- Treat the checklist as the release gate and require evidence per slice rather than a single terminal QA pass.
- Preserve the current frontend and backend architecture unless a production-readiness requirement forces a local structural change.
- Treat JSON-file persistence as a first-class production risk that must be either mitigated for pilot use or replaced by a database-backed path before full client launch.
- Keep deployability work brownfield-safe: configuration, branding, copy, runbooks, and operational safety should be layered onto the existing app rather than delivered as a rewrite.
- Separate "staging-ready" from "client-ready" so the team can validate real hosting, real routing, and real CORS before committing to client publication.
- Treat server deployment, backup and restore, observability, and go-live smoke testing as first-class deliverables, not post-launch chores.

## Implementation Plan

### Tasks

- [ ] Task 1: Externalize client branding and product identity
  - File: `frontend/src/app/layout/AppLayout.tsx`
  - File: `frontend/src/pages/LoginPage.tsx`
  - File: `frontend/src/shared/config/env.ts`
  - File: `frontend/src/main.tsx`
  - File: `frontend/src/styles/global.css`
  - Action: Introduce a client-brand configuration path for product name, client name, page title, and branding assets so the app no longer hardcodes the current demo identity in shared shells or entry screens.
  - Notes: Keep environment access centralized. Preserve the current shell and route architecture; this slice should only swap identity and branding surfaces, not redesign flows.

- [ ] Task 2: Remove or isolate remaining demo residue from client-facing surfaces
  - File: `frontend/src/pages/LoginPage.tsx`
  - File: `frontend/src/app/layout/AppLayout.tsx`
  - File: `frontend/src/app/routes.tsx`
  - File: `frontend/src/features/**/pages/*.tsx`
  - Action: Scan and remove client-visible `demo`, `preview`, local-credential guidance, and old client-brand strings from login, hub, mentor, student, and admin surfaces, while keeping any internal-only homologation fixtures behind explicit local/demo gating.
  - Notes: Follow the checklist residue scan exactly. If a demo-only path must remain for internal use, it must be explicit, hidden from client mode, and documented.

- [ ] Task 3: Convert the checklist into an execution-tracked release artifact
  - File: `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
  - File: `docs/`
  - Action: Extend the checklist with owner, status, evidence, and completion fields or create a companion release-tracking document that maps each checklist block to objective evidence and deployment signoff.
  - Notes: Do not dilute the checklist. The goal is to make release state auditable for the team and future agents.

- [ ] Task 4: Harden staging deployment validation for SPA hosting and integrated backend access
  - File: `frontend/README.md`
  - File: `frontend/.env.example`
  - File: `backend/app/config/runtime.py`
  - File: `backend/app/main.py`
  - File: `backend/tests/test_cors_config.py`
  - Action: Document and validate the exact staging deploy contract: SPA rewrite expectations, base-path configuration, frontend origin, backend `APP_ENV`, backend `CORS_ALLOW_ORIGINS`, and the integrated smoke path against the real target backend URL.
  - Notes: This slice should produce staging-ready instructions and validation, not only code tweaks. Keep runtime parsing centralized in the existing config module.

- [ ] Task 5: Add operational guardrails for single-server production usage
  - File: `backend/app/config/runtime.py`
  - File: `backend/app/main.py`
  - File: `backend/.env.example`
  - File: `frontend/README.md`
  - Action: Define explicit production operations expectations for secrets, startup config, artifact identity, logging destination, and rollback prerequisites so a real deploy does not rely on tacit local knowledge.
  - Notes: Keep code changes minimal unless startup enforcement is needed. This slice is mainly about fail-fast config and deployment discipline.

- [ ] Task 6: Mitigate or replace JSON-file persistence risk for client launch
  - File: `backend/app/storage/json_repository.py`
  - File: `backend/app/storage/client_repository.py`
  - File: `backend/app/storage/*_repository.py`
  - File: `backend/tests/`
  - File: `frontend/README.md`
  - Action: Choose and implement the minimum acceptable persistence strategy for launch: either formalize JSON storage as a single-server pilot path with backup/restore and operational constraints, or begin a brownfield migration path toward database-backed persistence.
  - Notes: This is the highest-risk production item. If JSON storage remains for initial client usage, the spec must make the limitations explicit and pair them with backup, restore, and hosting constraints.

- [ ] Task 7: Add backup and restore procedure for the deployed data model
  - File: `backend/app/storage/json_repository.py`
  - File: `docs/`
  - File: `frontend/README.md`
  - Action: Define and document a backup and restore procedure for every persisted JSON store, including backup location, execution cadence, restore verification, and operator steps after restore.
  - Notes: If code changes are needed to support snapshotting or integrity verification, keep them local to the storage layer.

- [ ] Task 8: Establish minimal observability and failure handling for production operation
  - File: `backend/app/main.py`
  - File: `backend/app/api/errors.py`
  - File: `frontend/src/app/providers/AuthProvider.tsx`
  - File: `frontend/src/pages/LoginPage.tsx`
  - File: `frontend/README.md`
  - Action: Define and implement the minimum observability posture for initial client usage, including where backend logs go, how auth or network failure is diagnosed, and how operators distinguish user error from deploy misconfiguration.
  - Notes: Reuse the current frontend error flow and backend error envelope. This is not a full telemetry platform; it is the minimum viable release-ops signal set.

- [ ] Task 9: Create deploy runbook and go-live smoke procedure
  - File: `frontend/README.md`
  - File: `docs/`
  - Action: Produce a copy-paste deployment runbook covering frontend build, backend startup, env configuration, SPA rewrite checks, backup verification, rollback trigger, and post-deploy smoke flows for admin, mentor, and aluno if in scope.
  - Notes: The runbook must be executable by someone who did not build the feature locally.

- [ ] Task 10: Expand automated and manual verification around production-readiness slices
  - File: `frontend/src/test/*`
  - File: `backend/tests/*`
  - File: `docs/`
  - Action: Add or update the tests and manual QA artifacts needed to prove branding cleanup, demo residue removal, deploy-config validation, persistence safeguards, and release smoke coverage.
  - Notes: Keep tests at the nearest relevant layer. Use a separate manual QA sheet or tracked section if the checklist itself is kept immutable.

### Acceptance Criteria

- [ ] AC 1: Given a client-targeted configuration, when the app loads the login page, shell, and top-level metadata, then they reflect the configured client identity and no longer expose the previous demo brand.
- [ ] AC 2: Given a client-targeted configuration, when a residue scan is run across the frontend, then no client-visible strings remain for hardcoded local credentials, obsolete demo markers, or the prior branded demo identity unless explicitly documented as internal-only and gated.
- [ ] AC 3: Given the staging deployment instructions, when the frontend is published on the target host with its configured base path, then deep-link refresh, branding assets, and protected route navigation continue to work under the real host path.
- [ ] AC 4: Given the backend is started in a production-like environment, when required deploy configuration is missing or malformed, then startup fails explicitly rather than silently falling back to local assumptions.
- [ ] AC 5: Given the frontend is pointed at the real staging backend, when authenticated and unauthenticated flows are exercised, then integrated behavior is confirmed for login, logout, auth expiry, admin denial, and expected API error classes.
- [ ] AC 6: Given the app is prepared for initial client usage, when operators review the persistence strategy, then the system has either a documented single-server JSON-storage operating model with constraints and backups or an approved migration path away from JSON storage.
- [ ] AC 7: Given JSON-file persistence remains in scope for the initial release, when backups are executed and a restore is simulated, then the documented restore path returns the data stores to a usable state and the application can be verified afterward.
- [ ] AC 8: Given a production deployment issue occurs, when operators inspect the documented observability path, then they can locate the relevant backend or startup signal and distinguish configuration failures from normal user-facing auth or network errors.
- [ ] AC 9: Given the deploy runbook is handed to a teammate who did not implement the hardening work, when they follow it, then they can configure env vars, build the frontend, start the backend, validate rewrites and CORS, and execute the smoke steps without hidden knowledge.
- [ ] AC 10: Given the release candidate is prepared, when `npm run build`, `npm run test`, backend deploy-config tests, and the manual smoke checklist are executed, then all required evidence can be attached to the release gate.
- [ ] AC 11: Given the release checklist is used as the deployment gate, when the team reviews readiness, then each required block has objective evidence, status, and a clear remaining blocker if incomplete.

## Additional Context

### Dependencies

- The current deployment hardening baseline in `_bmad-output/implementation-artifacts/tech-spec-frontend-deployment-hardening-client-delivery.md`
- The release gate defined in `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- Shared frontend env contract and backend runtime config modules
- Real target hosting details: domain, subpath strategy, TLS, SPA rewrite capability, backend origin, and single-server vs managed-host assumptions
- A product decision on whether the first client release may operate on JSON-file storage or must migrate persistence before launch

### Testing Strategy

- Update frontend tests to cover client-brand and demo-residue cleanup at the nearest relevant layer, especially shared shell and entry-page surfaces.
- Add backend tests for any new runtime validation, persistence safety, or backup-related helper logic introduced during the rollout.
- Add a tracked manual QA flow for integrated staging validation covering admin, mentor, and aluno if the aluno flow is part of the real client scope.
- Run release verification as a package: frontend build, frontend tests, backend targeted tests, real staging smoke, residue scan, and backup/restore verification.
- Capture evidence links or artifacts for each checklist block instead of treating test success as implicit proof.

### Notes

- Highest risk: launching client usage on JSON-file persistence without an explicit single-server operating model, backup cadence, and restore verification.
- Second risk: treating staging deploy as a documentation exercise rather than a real hosted validation on the final origin and base path shape.
- Third risk: leaving brand and demo cleanup partially complete, which would make the product look like a repackaged demo even if the auth and deploy contracts are sound.
- If the team chooses to keep JSON storage for an initial pilot, the rollout should call that release posture what it is: pilot-grade production with constrained operating assumptions, not horizontally scalable production.
- A later follow-up spec may be needed for persistence migration if the team decides not to accept JSON-backed storage for client launch.
