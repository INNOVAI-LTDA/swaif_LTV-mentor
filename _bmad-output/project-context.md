---
project_name: 'swaif_LTV-mentoria'
user_name: 'dmene'
date: '2026-03-30'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'quality_rules', 'workflow_rules', 'anti_patterns']
status: 'complete'
rule_count: 56
optimized_for_llm: true
existing_patterns_found: 11
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

### Frontend

- React `18.3.1`
- React DOM `18.3.1`
- React Router DOM `6.30.1`
- Vite `5.4.19`
- TypeScript `5.8.3`
- Vitest `2.1.9`
- Testing Library (`@testing-library/react` `16.3.0`, `@testing-library/jest-dom` `6.7.0`)
- jsdom `26.1.0`

### Frontend Configuration Signals

- TypeScript runs in `strict` mode.
- `moduleResolution` is `Bundler`.
- JSX mode is `react-jsx`.
- Build runs `tsc --noEmit && vite build`.
- Tests run in `jsdom` with global APIs enabled.
- Environment access is centralized under `src/shared/config/env.ts`.

### Backend

- Python `3.13` runtime is inferred from local `cpython-313` artifacts.
- FastAPI `0.135.1`
- Starlette `0.52.1`
- Pydantic `2.12.5`
- `pydantic-core` `2.41.5`
- Uvicorn `0.41.0`
- HTTPX `0.28.1`
- Pytest `9.0.2`

### Backend Architecture Signals

- Runtime entrypoint is `backend/app/main.py`.
- HTTP API uses FastAPI routers under `backend/app/api/routes`.
- Error payloads are standardized in `backend/app/api/errors.py`.
- Business logic lives in `backend/app/services`.
- Persistence is JSON-file backed via repositories under `backend/app/storage`.
- Schemas live under `backend/app/schemas`.

### Project Knowledge Sources

- `docs/architecture/platform_architecture_operational_model.md`
- `docs/mvp-mentoria/frontend-integration-architecture.md`
- `docs/mvp-mentoria/contracts-freeze-v1.md`
- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- `docs/mvp-mentoria/batch-g-data-ingestion-admin-current-state.md`
- `docs/discovery/data-ingestion-admin-brief.md`

## Critical Implementation Rules

### Language-Specific Rules

- Treat frontend TypeScript `strict` mode as a hard constraint. Do not use `any` unless there is no practical alternative and the boundary is explicitly unknown.
- Keep raw API payloads as `unknown` at the HTTP boundary, then normalize through adapters before domain or UI usage.
- Keep raw ingestion payloads and file-derived data at the schema boundary until backend/frontend adapters normalize them; do not thread source-shaped records through components.
- Do not put contract alias handling in React components. Alias normalization belongs in adapter code.
- Reuse the existing `AppError` flow for frontend network and HTTP failures; do not introduce feature-specific error object shapes.
- Centralize environment access in `src/shared/config/env.ts`. Feature code must not read `import.meta.env` directly.
- In backend Python, keep route handlers thin and move business rules into `app/services`.
- Preserve the standardized backend error envelope `{ error: { status, code, message, details } }` for all API-facing failures.
- When adding auth-sensitive backend logic, validate role and token through existing security/service patterns rather than ad hoc header parsing.

### Framework-Specific Rules

- In React, keep data-fetching concerns in domain hooks such as `useAsyncResource` wrappers, not inside page JSX.
- Reuse shared state panels and existing loading/error/empty conventions instead of inventing per-page resource-state UI.
- Keep feature structure consistent: feature-specific pages/components/styles stay under `src/features/<feature>/`, while cross-cutting code stays under `src/shared/`, `src/domain/`, or `src/app/`.
- Keep routing changes centralized in `src/app/routes.tsx`; do not scatter route definitions across features.
- Preserve the existing shell pattern for role-specific areas (`AdminShell`, `MentorShell`, `StudentShell`) instead of duplicating frame/layout logic in pages.
- Reuse the existing admin access boundary for operational features: frontend `RequireAdmin` and backend admin-role guards stay role-based and must not depend on a literal admin email.
- In FastAPI, register HTTP endpoints through routers under `app/api/routes` and include them in `app/main.py`; do not place endpoint logic directly in the app entrypoint.
- Keep request validation in schemas and HTTPException shaping in the shared API error utilities; route files should not handcraft inconsistent response shapes.
- Preserve repository-backed persistence boundaries: FastAPI routes call services, services call repositories, and repositories own store-path/file handling.
- For admin data ingestion work, treat the existing student indicator-load flow as the seed pattern and extend it through the same route/schema/service/repository layers before introducing a parallel architecture.
- Treat preview/demo flows as framework exceptions that must remain isolated from production-safe auth and routing paths.

### Testing Rules

- Frontend tests belong in `frontend/src/test` and use Vitest plus Testing Library; match the existing `*.test.ts` and `*.test.tsx` naming pattern.
- Backend tests belong under `backend/tests` and must stay split by scope: `unit`, `api`, `integration`, and `e2e`.
- When changing API behavior, preserve or update tests that assert the standardized error payload shape, especially for `401`, `404`, `409`, and `422`.
- When changing repository behavior, prefer integration tests that exercise the JSON-backed storage layer rather than mocking storage internals.
- When changing service rules, add or update unit tests at the service layer instead of only covering the behavior indirectly through routes.
- For frontend route or auth changes, update smoke-style route tests and any tests that rely on `AuthProvider`.
- When evolving admin ingestion behavior, extend the existing indicator-load API/service/modal tests first; dry-run, backup, audit, and rollback behavior each need nearest-layer coverage.
- Keep test fixtures isolated through temporary storage paths and environment setup rather than relying on shared local state.
- Do not add new behavior without coverage at the nearest relevant layer.

### Code Quality & Style Rules

- Match the current naming scheme: React components, pages, and shells use PascalCase file names; hooks use `useX`; services, adapters, shared helpers, and config files use camelCase file names.
- Keep feature code grouped by domain intent rather than by technical layer sprawl; prefer extending existing folders before creating new top-level namespaces.
- Prefer small, explicit functions with typed inputs and outputs over broad utility abstractions.
- Keep formatting and display helpers centralized under shared/domain utility locations rather than embedding formatting logic in pages.
- Follow the current pattern of Portuguese user-facing copy and stable English-oriented technical identifiers where that convention already exists.
- Reuse existing shared primitives before adding new generic abstractions, especially for auth, API access, resource state, and layout shells.
- Keep comments sparse and useful; add them only where business rules or non-obvious control flow would be hard to infer from the code.
- Preserve document-driven constraints from the architecture and contract docs when code and docs intersect; do not silently diverge from frozen contracts.

### Development Workflow Rules

- Treat the docs folder as an active engineering input, not passive documentation. Check relevant architecture, contract, and readiness docs before changing behavior in those areas.
- When implementing client-safe frontend changes, explicitly account for the deployment-hardening checklist and remove or isolate demo-only behavior rather than extending it.
- Preserve the current layered delivery model of platform core, skin, and client configuration described in the architecture docs when making structural decisions.
- Keep changes scoped to the nearest existing module or feature unless a documented architecture reason justifies a broader refactor.
- When changing contracts or behavior that other layers depend on, update the associated docs and tests in the same change set.
- Prefer incremental extension of existing routes, services, adapters, and repositories over parallel replacement paths.
- Treat admin data ingestion as a brownfield expansion of a narrower existing capability, not as greenfield infrastructure and not as proof that the broader brief is already implemented.
- For ingestion work, explicitly list the approved JSON targets and write paths in the relevant story or architecture artifact before implementation; do not widen scope to generic repository-wide writes.
- Preserve the current replace-for-enrollment persistence semantics for initial indicator load unless an approved architecture decision explicitly introduces versioning, merge, or append behavior.
- Route backup/snapshot, dry-run, audit, and rollback concerns through existing backend operations and service boundaries rather than UI-only confirmation or ad hoc scripts.
- Treat `_bmad-output/project-context.md` and the key docs as coordination artifacts for future agents; keep them aligned with the codebase when major patterns change.

### Critical Don't-Miss Rules

- Do not bypass adapters by binding raw API payloads directly into React UI state.
- Do not spread `import.meta.env`, token storage access, or fetch details across feature code; keep those concerns in shared infrastructure.
- Do not break the backend error envelope or invent endpoint-specific error response shapes.
- Do not put business rules in FastAPI route files or persistence logic in service callers.
- Do not reintroduce demo credentials, preview sessions, localhost defaults, or client-visible demo copy into production-oriented frontend paths.
- Do not embed alias migration logic such as legacy patient/client naming directly into components; keep terminology normalization in adapters and documented mappings.
- Do not add behavior that depends on mutable local JSON stores without matching tests for repository, service, or API effects.
- Do not silently change contract expectations that the frontend architecture and frozen contract docs rely on.
- Do not gate admin-only ingestion behavior by `admin@swaif.local`, and do not expose sensitive server paths or backup locations directly in the UI.
- Do not treat a UI confirmation modal as the operational safeguard for ingestion: `dry-run` must not persist, and `apply` must create a backup/snapshot before writing.
- Do not describe execution audit logs, conflict reports, backup-linked apply, or rollback support as existing capabilities unless the code and tests implement them explicitly.

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code.
- Follow all rules exactly as documented.
- When in doubt, prefer the more restrictive option.
- Update this file if new patterns emerge.

**For Humans:**

- Keep this file lean and focused on agent needs.
- Update it when the technology stack changes.
- Review it periodically for outdated or obvious rules.
- Keep it aligned with architecture, contract, and deployment-hardening docs.

Last Updated: 2026-03-30
