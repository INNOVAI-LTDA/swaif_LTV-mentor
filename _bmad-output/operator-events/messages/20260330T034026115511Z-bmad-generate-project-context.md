```json
{
  "status": "completed",
  "summary": "Updated `_bmad-output/project-context.md` to preserve the existing project-wide agent guidance while adding the newly discovered brownfield constraints for the admin data-ingestion initiative. The artifact now includes the two new source documents, refreshed metadata dated 2026-03-30, and lean rules covering admin-role boundaries, ingestion payload handling, approved JSON target scoping, backup/dry-run/audit expectations, and test-extension guidance anchored to the current indicator-load implementation.",
  "decisions": [
    "Used `_bmad-output/project-context.md` as the existing project-context baseline because the root `project-context.md` referenced by `AGENTS.md` is not present in the repository.",
    "Kept the artifact in English to match `_bmad/bmm/config.yaml` (`document_output_language: English`).",
    "Applied the smallest safe patch by extending the existing context file instead of regenerating it from scratch.",
    "Encoded the admin data-ingestion work as a brownfield extension of the existing student indicator-load path rather than as a greenfield capability.",
    "Recommended `bmad-create-architecture` as the next command because the current-state and brief now need an explicit architecture decision set for source format, approved JSON targets, dry-run/apply contract, backup linkage, and audit persistence."
  ],
  "risks": [
    "The root `project-context.md` expected by `AGENTS.md` is still absent, so future agents may only see the generated context if they follow the `_bmad-output` convention or operator guidance.",
    "Some backend version metadata in the context file remains inferred from the local environment rather than fully locked by a single backend packaging file.",
    "The updated artifact captures constraints and current-state boundaries, but it does not resolve the open architecture questions from the ingestion brief such as source-of-truth format, duplication policy, and rollback persistence strategy."
  ],
  "input_artifacts": [
    {
      "path": "docs/mvp-mentoria/batch-g-data-ingestion-admin-current-state.md",
      "role": "Scoped brownfield current-state anchor for the admin data-ingestion capability."
    },
    {
      "path": "_bmad-output/project-context.md",
      "role": "Existing project-context baseline to update rather than recreate."
    },
    {
      "path": "docs/discovery/data-ingestion-admin-brief.md",
      "role": "Feature brief defining the intended admin data-ingestion scope, risks, and open questions."
    },
    {
      "path": "docs/architecture/platform_architecture_operational_model.md",
      "role": "Project architecture source required by repository instructions and used to preserve platform conventions."
    },
    {
      "path": "docs/mvp-mentoria/frontend-integration-architecture.md",
      "role": "Frontend integration rules source used to preserve adapter, error, and routing conventions."
    },
    {
      "path": "docs/mvp-mentoria/contracts-freeze-v1.md",
      "role": "Frozen contract source used to preserve API compatibility and error-envelope expectations."
    },
    {
      "path": "docs/mvp-mentoria/frontend-deployment-readiness-checklist.md",
      "role": "Operational hardening source used to preserve deployment and demo-isolation rules."
    },
    {
      "path": "frontend/package.json",
      "role": "Frontend dependency/version discovery signal."
    },
    {
      "path": "backend/requirements.txt",
      "role": "Backend dependency/version discovery signal."
    },
    {
      "path": "frontend/tsconfig.json",
      "role": "Frontend TypeScript configuration signal."
    },
    {
      "path": "frontend/vite.config.ts",
      "role": "Frontend build/test/environment configuration signal."
    },
    {
      "path": "_bmad/bmm/config.yaml",
      "role": "BMAD workflow configuration for communication language, output language, and artifact path."
    },
    {
      "path": ".agents/skills/bmad-generate-project-context/SKILL.md",
      "role": "BMAD skill entry point."
    },
    {
      "path": ".agents/skills/bmad-generate-project-context/workflow.md",
      "role": "BMAD workflow definition."
    },
    {
      "path": ".agents/skills/bmad-generate-project-context/steps/step-01-discover.md",
      "role": "BMAD discovery-step instructions."
    },
    {
      "path": ".agents/skills/bmad-generate-project-context/steps/step-02-generate.md",
      "role": "BMAD rule-generation-step instructions."
    },
    {
      "path": ".agents/skills/bmad-generate-project-context/steps/step-03-complete.md",
      "role": "BMAD completion-step instructions."
    }
  ],
  "output_artifacts": [
    {
      "artifact_type": "project-context",
      "path": "_bmad-output/project-context.md",
      "content": "---\nproject_name: 'swaif_LTV-mentoria'\nuser_name: 'dmene'\ndate: '2026-03-30'\nsections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'quality_rules', 'workflow_rules', 'anti_patterns']\nstatus: 'complete'\nrule_count: 56\noptimized_for_llm: true\nexisting_patterns_found: 11\n---\n\n# Project Context for AI Agents\n\n_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._\n\n---\n\n## Technology Stack & Versions\n\n### Frontend\n\n- React `18.3.1`\n- React DOM `18.3.1`\n- React Router DOM `6.30.1`\n- Vite `5.4.19`\n- TypeScript `5.8.3`\n- Vitest `2.1.9`\n- Testing Library (`@testing-library/react` `16.3.0`, `@testing-library/jest-dom` `6.7.0`)\n- jsdom `26.1.0`\n\n### Frontend Configuration Signals\n\n- TypeScript runs in `strict` mode.\n- `moduleResolution` is `Bundler`.\n- JSX mode is `react-jsx`.\n- Build runs `tsc --noEmit && vite build`.\n- Tests run in `jsdom` with global APIs enabled.\n- Environment access is centralized under `src/shared/config/env.ts`.\n\n### Backend\n\n- Python `3.13` runtime is inferred from local `cpython-313` artifacts.\n- FastAPI `0.135.1`\n- Starlette `0.52.1`\n- Pydantic `2.12.5`\n- `pydantic-core` `2.41.5`\n- Uvicorn `0.41.0`\n- HTTPX `0.28.1`\n- Pytest `9.0.2`\n\n### Backend Architecture Signals\n\n- Runtime entrypoint is `backend/app/main.py`.\n- HTTP API uses FastAPI routers under `backend/app/api/routes`.\n- Error payloads are standardized in `backend/app/api/errors.py`.\n- Business logic lives in `backend/app/services`.\n- Persistence is JSON-file backed via repositories under `backend/app/storage`.\n- Schemas live under `backend/app/schemas`.\n\n### Project Knowledge Sources\n\n- `docs/architecture/platform_architecture_operational_model.md`\n- `docs/mvp-mentoria/frontend-integration-architecture.md`\n- `docs/mvp-mentoria/contracts-freeze-v1.md`\n- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`\n- `docs/mvp-mentoria/batch-g-data-ingestion-admin-current-state.md`\n- `docs/discovery/data-ingestion-admin-brief.md`\n\n## Critical Implementation Rules\n\n### Language-Specific Rules\n\n- Treat frontend TypeScript `strict` mode as a hard constraint. Do not use `any` unless there is no practical alternative and the boundary is explicitly unknown.\n- Keep raw API payloads as `unknown` at the HTTP boundary, then normalize through adapters before domain or UI usage.\n- Keep raw ingestion payloads and file-derived data at the schema boundary until backend/frontend adapters normalize them; do not thread source-shaped records through components.\n- Do not put contract alias handling in React components. Alias normalization belongs in adapter code.\n- Reuse the existing `AppError` flow for frontend network and HTTP failures; do not introduce feature-specific error object shapes.\n- Centralize environment access in `src/shared/config/env.ts`. Feature code must not read `import.meta.env` directly.\n- In backend Python, keep route handlers thin and move business rules into `app/services`.\n- Preserve the standardized backend error envelope `{ error: { status, code, message, details } }` for all API-facing failures.\n- When adding auth-sensitive backend logic, validate role and token through existing security/service patterns rather than ad hoc header parsing.\n\n### Framework-Specific Rules\n\n- In React, keep data-fetching concerns in domain hooks such as `useAsyncResource` wrappers, not inside page JSX.\n- Reuse shared state panels and existing loading/error/empty conventions instead of inventing per-page resource-state UI.\n- Keep feature structure consistent: feature-specific pages/components/styles stay under `src/features/<feature>/`, while cross-cutting code stays under `src/shared/`, `src/domain/`, or `src/app/`.\n- Keep routing changes centralized in `src/app/routes.tsx`; do not scatter route definitions across features.\n- Preserve the existing shell pattern for role-specific areas (`AdminShell`, `MentorShell`, `StudentShell`) instead of duplicating frame/layout logic in pages.\n- Reuse the existing admin access boundary for operational features: frontend `RequireAdmin` and backend admin-role guards stay role-based and must not depend on a literal admin email.\n- In FastAPI, register HTTP endpoints through routers under `app/api/routes` and include them in `app/main.py`; do not place endpoint logic directly in the app entrypoint.\n- Keep request validation in schemas and HTTPException shaping in the shared API error utilities; route files should not handcraft inconsistent response shapes.\n- Preserve repository-backed persistence boundaries: FastAPI routes call services, services call repositories, and repositories own store-path/file handling.\n- For admin data ingestion work, treat the existing student indicator-load flow as the seed pattern and extend it through the same route/schema/service/repository layers before introducing a parallel architecture.\n- Treat preview/demo flows as framework exceptions that must remain isolated from production-safe auth and routing paths.\n\n### Testing Rules\n\n- Frontend tests belong in `frontend/src/test` and use Vitest plus Testing Library; match the existing `*.test.ts` and `*.test.tsx` naming pattern.\n- Backend tests belong under `backend/tests` and must stay split by scope: `unit`, `api`, `integration`, and `e2e`.\n- When changing API behavior, preserve or update tests that assert the standardized error payload shape, especially for `401`, `404`, `409`, and `422`.\n- When changing repository behavior, prefer integration tests that exercise the JSON-backed storage layer rather than mocking storage internals.\n- When changing service rules, add or update unit tests at the service layer instead of only covering the behavior indirectly through routes.\n- For frontend route or auth changes, update smoke-style route tests and any tests that rely on `AuthProvider`.\n- When evolving admin ingestion behavior, extend the existing indicator-load API/service/modal tests first; dry-run, backup, audit, and rollback behavior each need nearest-layer coverage.\n- Keep test fixtures isolated through temporary storage paths and environment setup rather than relying on shared local state.\n- Do not add new behavior without coverage at the nearest relevant layer.\n\n### Code Quality & Style Rules\n\n- Match the current naming scheme: React components, pages, and shells use PascalCase file names; hooks use `useX`; services, adapters, shared helpers, and config files use camelCase file names.\n- Keep feature code grouped by domain intent rather than by technical layer sprawl; prefer extending existing folders before creating new top-level namespaces.\n- Prefer small, explicit functions with typed inputs and outputs over broad utility abstractions.\n- Keep formatting and display helpers centralized under shared/domain utility locations rather than embedding formatting logic in pages.\n- Follow the current pattern of Portuguese user-facing copy and stable English-oriented technical identifiers where that convention already exists.\n- Reuse existing shared primitives before adding new generic abstractions, especially for auth, API access, resource state, and layout shells.\n- Keep comments sparse and useful; add them only where business rules or non-obvious control flow would be hard to infer from the code.\n- Preserve document-driven constraints from the architecture and contract docs when code and docs intersect; do not silently diverge from frozen contracts.\n\n### Development Workflow Rules\n\n- Treat the docs folder as an active engineering input, not passive documentation. Check relevant architecture, contract, and readiness docs before changing behavior in those areas.\n- When implementing client-safe frontend changes, explicitly account for the deployment-hardening checklist and remove or isolate demo-only behavior rather than extending it.\n- Preserve the current layered delivery model of platform core, skin, and client configuration described in the architecture docs when making structural decisions.\n- Keep changes scoped to the nearest existing module or feature unless a documented architecture reason justifies a broader refactor.\n- When changing contracts or behavior that other layers depend on, update the associated docs and tests in the same change set.\n- Prefer incremental extension of existing routes, services, adapters, and repositories over parallel replacement paths.\n- Treat admin data ingestion as a brownfield expansion of a narrower existing capability, not as greenfield infrastructure and not as proof that the broader brief is already implemented.\n- For ingestion work, explicitly list the approved JSON targets and write paths in the relevant story or architecture artifact before implementation; do not widen scope to generic repository-wide writes.\n- Preserve the current replace-for-enrollment persistence semantics for initial indicator load unless an approved architecture decision explicitly introduces versioning, merge, or append behavior.\n- Route backup/snapshot, dry-run, audit, and rollback concerns through existing backend operations and service boundaries rather than UI-only confirmation or ad hoc scripts.\n- Treat `_bmad-output/project-context.md` and the key docs as coordination artifacts for future agents; keep them aligned with the codebase when major patterns change.\n\n### Critical Don't-Miss Rules\n\n- Do not bypass adapters by binding raw API payloads directly into React UI state.\n- Do not spread `import.meta.env`, token storage access, or fetch details across feature code; keep those concerns in shared infrastructure.\n- Do not break the backend error envelope or invent endpoint-specific error response shapes.\n- Do not put business rules in FastAPI route files or persistence logic in service callers.\n- Do not reintroduce demo credentials, preview sessions, localhost defaults, or client-visible demo copy into production-oriented frontend paths.\n- Do not embed alias migration logic such as legacy patient/client naming directly into components; keep terminology normalization in adapters and documented mappings.\n- Do not add behavior that depends on mutable local JSON stores without matching tests for repository, service, or API effects.\n- Do not silently change contract expectations that the frontend architecture and frozen contract docs rely on.\n- Do not gate admin-only ingestion behavior by `admin@swaif.local`, and do not expose sensitive server paths or backup locations directly in the UI.\n- Do not treat a UI confirmation modal as the operational safeguard for ingestion: `dry-run` must not persist, and `apply` must create a backup/snapshot before writing.\n- Do not describe execution audit logs, conflict reports, backup-linked apply, or rollback support as existing capabilities unless the code and tests implement them explicitly.\n\n---\n\n## Usage Guidelines\n\n**For AI Agents:**\n\n- Read this file before implementing any code.\n- Follow all rules exactly as documented.\n- When in doubt, prefer the more restrictive option.\n- Update this file if new patterns emerge.\n\n**For Humans:**\n\n- Keep this file lean and focused on agent needs.\n- Update it when the technology stack changes.\n- Review it periodically for outdated or obvious rules.\n- Keep it aligned with architecture, contract, and deployment-hardening docs.\n\nLast Updated: 2026-03-30\n"
    }
  ],
  "approval_required": false,
  "next_command": "bmad-create-architecture"
}
```