---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - C:\Users\dmene\Projetos\innovai\repos\swaif_LTV-mentoria\_bmad-output\project-context.md
  - C:\Users\dmene\Projetos\innovai\repos\swaif_LTV-mentoria\docs\mvp-mentoria\batch-g-data-ingestion-admin-current-state.md
  - C:\Users\dmene\Projetos\innovai\repos\swaif_LTV-mentoria\docs\discovery\data-ingestion-admin-brief.md
  - C:\Users\dmene\Projetos\innovai\repos\swaif_LTV-mentoria\docs\architecture\platform_architecture_operational_model.md
  - C:\Users\dmene\Projetos\innovai\repos\swaif_LTV-mentoria\docs\mvp-mentoria\frontend-integration-architecture.md
  - C:\Users\dmene\Projetos\innovai\repos\swaif_LTV-mentoria\docs\mvp-mentoria\contracts-freeze-v1.md
  - C:\Users\dmene\Projetos\innovai\repos\swaif_LTV-mentoria\docs\mvp-mentoria\frontend-deployment-readiness-checklist.md
workflowType: architecture
project_name: swaif_LTV-mentoria
user_name: dmene
date: 2026-03-30
lastStep: 8
status: complete
completedAt: 2026-03-30
scope: data-ingestion-admin
---

# Admin Data Ingestion Architecture

## Project Context Analysis

### Requirements Overview

**Functional requirements**

The requested capability is an admin-only operational flow called `Ingestao de Dados` that must:

- expose an admin-visible entry inside the existing admin area
- accept a structured source chosen by the admin
- support `dry_run` with no persistence
- show validation, conflict, rejection, and impact summaries before apply
- require explicit confirmation before write
- create a backup snapshot before apply
- return a structured execution report
- keep a minimal audit trail
- document rollback

**Non-functional requirements**

The architecture is shaped more by operational safety than by UI novelty:

- role-based admin access only
- no dependency on literal `admin@swaif.local`
- no raw JSON writes from frontend code
- no generic repository-wide write access
- preserve the standard API error envelope
- preserve React service/hook/adapter boundaries
- keep FastAPI route handlers thin
- reuse JSON-backed repositories and backup tooling
- extend nearest-layer tests for API, service, repository, and admin UI flow

**Scale and complexity**

This is a medium-complexity brownfield feature:

- full-stack, but localized to the admin operational surface
- low traffic, high safety sensitivity
- no external ETL in MVP
- high validation and audit requirements
- data volume is batch-oriented, not streaming

Primary domain: admin operational data ingestion over the existing mentoria runtime.

### Technical Constraints and Dependencies

- The current repo already implements one admin-only ingestion slice for a single student enrollment through `POST /admin/alunos/{student_id}/indicadores/carga-inicial`.
- Persistence is JSON-backed through repositories and currently uses `replace_for_enrollment(...)` for `measurements` and `checkpoints`.
- Snapshot and restore utilities already exist in `backend/app/operations/storage_maintenance.py`.
- Frontend admin access already exists behind `RequireAdmin` on `/app/admin`.
- The contract freeze forbids breaking existing v1 endpoints and error shapes.
- Frontend integration rules require service/adapters, not raw fetch logic in page JSX.

### Cross-Cutting Concerns Identified

- Access control must remain role-based on both frontend and backend.
- Validation must distinguish transport errors from domain rejections inside the batch.
- Preview and apply must run through the same server-side validator to avoid drift.
- Backup and restore must stay in backend operational boundaries, not UI-only confirmation.
- Audit metadata must be captured without exposing sensitive backup paths in the UI.
- The architecture must stay explicitly scoped to approved JSON targets.

## Starter Template Evaluation

### Brownfield Decision

No new starter template will be introduced.

This initiative is a brownfield extension of the current stack:

- frontend: React 18 + Vite 5 + TypeScript strict
- backend: FastAPI + Pydantic v2 + JSON repositories
- persistence: registered JSON stores under `backend/data`
- operations: existing storage snapshot and restore tooling

### Rationale for No Starter

- The repository is already in stabilization mode.
- A starter would add unrelated churn and conflict with the existing architecture.
- The correct architectural move is to extend the current indicator-load slice through the same route/schema/service/repository layering.

### First Implementation Foundation

The first implementation story should not scaffold new infrastructure. It should define the new ingestion contract and admin entry using the existing runtime, routing, auth, and storage conventions.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical decisions**

- Fix the MVP scope to approved indicator-related JSON targets only.
- Choose the official source model.
- Define the `dry_run` and `apply` contract.
- Define duplication and replacement semantics.
- Define where audit data lives and how backup references are surfaced.

**Important decisions**

- Choose whether the new admin entry is a new route or a new panel in `AdminPage`.
- Decide whether rollback is UI-driven or operator-assisted in MVP.
- Define how partial validity is reported without breaking the HTTP error contract.

**Deferred decisions**

- Generic ingestion into `students`, `mentors`, `organizations`, `protocols`, or other stores.
- Scheduled ingestion or ETL integration.
- Multi-user concurrency controls beyond the storage I/O lock.
- Historical analytics dashboard for ingestion executions.

### Data Architecture

#### Scope Boundary

The MVP architecture is intentionally narrower than the broad brief examples.

Approved write targets for this feature:

1. `backend/data/measurements.json`
2. `backend/data/checkpoints.json`
3. `backend/data/admin_ingestion_executions.json` (new audit store)

Explicitly not allowed in this MVP:

- writes to `students.json`
- writes to `mentors.json`
- writes to `organizations.json`
- writes to `protocols.json`
- writes to `metrics.json`
- writes to any unregistered or ad hoc JSON file

The feature is therefore a standalone admin operation for batch indicator loading, not a generic JSON mutator.

#### Source Model

The official MVP source is a structured JSON file uploaded by the admin from the browser.

Rationale:

- matches the brief preference for a structured, deterministic, validatable file
- avoids exposing server paths in the UI
- keeps raw source parsing on the backend boundary
- preserves frontend simplicity and adapter discipline

#### Canonical Payload Shape

The uploaded file must follow one explicit schema version:

```json
{
  "schema_version": 1,
  "source_kind": "indicator_batch_json",
  "items": [
    {
      "student_id": "std_1",
      "metric_values": [
        {
          "metric_id": "met_1",
          "value_baseline": 55,
          "value_current": 68,
          "value_projected": 75,
          "improving_trend": true
        }
      ],
      "checkpoints": [
        {
          "week": 1,
          "status": "green",
          "label": "Inicio consistente"
        }
      ]
    }
  ]
}
```

The ingestion file stays source-shaped until backend schema parsing completes. React components must never hold normalized ingestion domain objects built from the raw file body.

#### Duplication and Replacement Semantics

The MVP duplication rule is:

- duplicate `student_id` entries inside the same file: reject the duplicated items
- duplicate `metric_id` inside one student item: reject that student item
- duplicate checkpoint `week` inside one student item: reject that student item
- missing student, missing active enrollment, or missing/inactive metric: reject that student item
- existing persisted measurements/checkpoints for the target enrollment: replace the current enrollment slice on apply

This preserves the current repo behavior of `replace_for_enrollment(...)` and avoids introducing merge or append history in the same change.

#### Persistence Strategy

For each valid student item:

1. resolve the active enrollment through the existing service path
2. validate all metrics against active metrics
3. normalize measurements and checkpoints using the existing indicator-load rules
4. on `apply`, replace measurements and checkpoints for that enrollment

The architecture keeps `replace_for_enrollment(...)` as the persistence rule for the MVP.

### Authentication and Security

- Frontend access remains under `/app/admin` and `RequireAdmin`.
- Backend access remains admin-role based via existing `require_admin_user`.
- The feature must not depend on `admin@swaif.local`.
- The UI must not display filesystem paths for backups or storage roots.
- Audit records may store internal backup paths, but the API response shown to the UI must expose only a safe backup reference.

### API and Communication Patterns

#### Endpoint Shape

Add a dedicated admin ingestion endpoint family without breaking existing v1 contracts:

- `POST /admin/ingestoes/indicadores`
- `POST /admin/ingestoes/indicadores/{execution_id}/rollback` (admin-only, optional in the first delivery slice, but reserved by the architecture)

The existing `POST /admin/alunos/{student_id}/indicadores/carga-inicial` endpoint remains unchanged.

#### Request Contract

`POST /admin/ingestoes/indicadores` accepts `multipart/form-data` with:

- `file`: uploaded JSON source
- `mode`: `dry_run | apply`
- `source_label`: optional operator-provided label
- `preview_execution_id`: optional link to a prior dry-run
- `confirm_apply`: required boolean when `mode=apply`

`apply` must rerun full validation server-side even if a previous dry-run exists.

#### Success Contract

Batch validation results are returned as successful responses, even when some items are rejected, because rejections are part of the operational report and not a transport-level API failure.

Suggested response shape:

```json
{
  "execution_id": "ing_20260330_001",
  "mode": "dry_run",
  "status": "dry_run_ready",
  "source": {
    "kind": "uploaded_json",
    "file_name": "indicadores-lote-01.json",
    "source_label": "Carga operador local",
    "checksum_sha256": "..."
  },
  "summary": {
    "received_items": 3,
    "valid_items": 2,
    "rejected_items": 1,
    "conflict_count": 1,
    "affected_enrollments": 2,
    "affected_stores": ["measurements", "checkpoints"]
  },
  "results": [
    {
      "student_id": "std_1",
      "enrollment_id": "enr_1",
      "status": "ready",
      "measurement_count": 4,
      "checkpoint_count": 2,
      "conflicts": []
    }
  ],
  "rejections": [
    {
      "student_id": "std_9",
      "code": "MATRICULA_NOT_FOUND",
      "message": "Vinculo do aluno com mentoria nao encontrado."
    }
  ],
  "backup": null
}
```

#### Error Contract

The standard API error envelope remains unchanged for:

- `401` unauthenticated
- `403` forbidden
- `404` route/resource not found outside the batch-report flow
- `409` unrecoverable apply or rollback conflict
- `422` malformed multipart request, unreadable file, or schema-invalid top-level payload

The feature must not invent a custom HTTP error shape.

### Frontend Architecture

#### Admin Entry

Add `Ingestao de Dados` as a new panel inside the existing `AdminPage`, not as a new top-level route.

Recommended navigation model:

- keep `/app/admin`
- add `?panel=ingestao-dados`
- reuse the existing admin shell and panel conventions

This is the smallest safe frontend extension and avoids route sprawl.

#### Frontend Layering

Frontend additions should follow the current architecture:

- contract DTOs: `frontend/src/contracts/adminDataIngestion.ts`
- service calls: `frontend/src/domain/services/adminDataIngestionService.ts`
- resource hook: `frontend/src/domain/hooks/useAdminDataIngestion.ts` if state reuse is needed
- UI state and modal/panel rendering: existing `frontend/src/features/admin/pages/AdminPage.tsx`
- shared upload/report display helpers only if they are genuinely reusable

The page must not:

- parse raw JSON source into domain entities
- call `fetch` directly
- read environment variables directly
- normalize backend error payloads inline

#### UI Flow

1. Admin opens `Ingestao de Dados`.
2. Admin selects a JSON file and optional source label.
3. UI calls `dry_run`.
4. UI renders counts, affected stores, per-item conflicts, and rejections.
5. Admin confirms apply.
6. UI resubmits the same file with `mode=apply`.
7. UI shows final execution report and safe backup reference.

Rollback is not exposed as a primary UI action in the MVP. The UI may show that rollback is available through operator support using the execution ID.

### Infrastructure and Deployment

#### Operational Locking

`apply` and `rollback` operations must run inside the existing storage I/O lock boundary.

#### Backup Model

Before any `apply`, the backend must call the existing snapshot utility:

- reuse `create_backup_snapshot(...)`
- accept that the current utility snapshots all registered stores
- report only the logical stores affected by the feature in the execution result

This preserves the current operational posture and avoids inventing a second backup system.

#### Failure Recovery

If an `apply` fails after snapshot creation but before successful completion:

1. the service must attempt restore from the just-created snapshot
2. the final execution record must capture the failure and restore outcome
3. the API must return a standard error envelope only for unrecoverable apply failure

#### Audit Store

Create a new JSON-backed repository for execution audit:

- file: `backend/data/admin_ingestion_executions.json`
- env override: `INGESTION_EXECUTION_STORE_PATH`
- store registry name: `admin_ingestion_executions`

Each execution record must include:

- `execution_id`
- `created_at`
- `completed_at`
- `operator_id`
- `operator_email`
- `mode`
- `status`
- `source_kind`
- `source_file_name`
- `source_label`
- `source_checksum_sha256`
- `received_items`
- `valid_items`
- `applied_items`
- `rejected_items`
- `conflict_count`
- `affected_store_names`
- `affected_enrollment_ids`
- `backup_snapshot_id`
- `backup_snapshot_dir` (internal only)
- `preview_execution_id`
- `rollback_of_execution_id`
- `rollback_execution_id`

## Implementation Patterns and Consistency Rules

### Naming Patterns

**API naming**

- use plural admin ingestion noun: `/admin/ingestoes/indicadores`
- use snake_case in backend schemas and JSON persistence
- keep frontend DTOs in snake_case only at contract boundaries
- keep frontend domain/UI names idiomatic to existing code

**Code naming**

- React page/components: PascalCase
- hooks: `useX`
- services, repositories, config helpers: camelCase file names where already used in the repo
- Python modules remain snake_case

**Execution identifiers**

- prefix execution IDs with `ing_`
- prefix rollback execution IDs with the same family, not a new ad hoc scheme

### Structure Patterns

- Thin FastAPI routes under `backend/app/api/routes`
- Business rules in `backend/app/services`
- JSON read/write in `backend/app/storage`
- Existing `indicator_load.py` is the schema seed and should be extended or closely paired, not bypassed
- Existing `IndicatorCargaService` is the service seed and should own normalization logic reused by batch preview/apply

### Format Patterns

**Batch report format**

- validation failures belong in `results` / `rejections`
- transport and auth failures belong in the standard API error envelope
- all store names in reports use registry names, not raw filesystem paths
- timestamps use ISO 8601 UTC strings

**File schema versioning**

- the uploaded JSON file must carry `schema_version`
- the backend rejects unknown schema versions with `422`
- future schema expansion must add a new schema version, not reinterpret version 1 silently

### Process Patterns

**Dry-run**

- never persists measurements or checkpoints
- may persist an audit execution record
- must use the same validator used by apply

**Apply**

- requires explicit `confirm_apply=true`
- reruns full validation
- creates backup before write
- writes only approved stores
- persists execution audit after outcome is known

**Rollback**

- must restore from the recorded snapshot reference
- must update the execution audit trail
- should be operator-assisted first, UI-driven later if ever needed

### Enforcement Guidelines

All AI agents implementing this feature must:

- preserve the standard API error envelope
- keep raw uploaded data out of page-level React state
- keep approved target scope explicit in code and tests
- reuse the current indicator normalization path instead of creating a parallel ingestion engine
- keep filesystem path details off the UI

## Project Structure and Boundaries

### Target Project Tree

```txt
backend/
  app/
    api/
      routes/
        admin_students.py                    # existing endpoint remains
        admin_data_ingestion.py              # new ingestion route family
    schemas/
      indicator_load.py                      # extend or pair with batch request/response models
    services/
      indicator_carga_service.py             # extend with batch preview/apply orchestration
      ingestion_execution_service.py         # optional small helper if audit orchestration needs separation
    storage/
      measurement_repository.py              # existing target
      checkpoint_repository.py               # existing target
      ingestion_execution_repository.py      # new audit repository
      store_registry.py                      # register new audit store
frontend/
  src/
    contracts/
      adminDataIngestion.ts                  # new DTOs
    domain/
      services/
        adminDataIngestionService.ts         # new HTTP service
      hooks/
        useAdminDataIngestion.ts             # only if panel state benefits from a shared resource hook
    features/
      admin/
        pages/
          AdminPage.tsx                      # add panel and report flow
    test/
      admin-data-ingestion-panel.test.tsx    # new or extended admin panel coverage
backend/tests/
  api/
    test_admin_data_ingestion_api.py         # new dry-run/apply/rollback API tests
  unit/
    test_indicator_carga_service.py          # extend for batch validation/orchestration
  integration/
    test_ingestion_execution_repository.py   # new audit repository coverage
```

### Architectural Boundaries

**Backend route boundary**

- route validates auth and request envelope
- route delegates to service
- route maps only transport-level failures to the standard API error envelope

**Backend service boundary**

- parse uploaded file
- validate schema version and content
- resolve student and enrollment context
- compute preview report
- orchestrate snapshot, write, restore-on-failure, and audit record

**Storage boundary**

- measurement and checkpoint repositories remain responsible for row persistence only
- audit repository owns execution log persistence
- storage maintenance continues to own snapshot and restore

**Frontend boundary**

- `AdminPage` owns interaction flow only
- service layer owns HTTP transport
- contracts define DTO boundaries
- adapters or mapping helpers normalize success/error payloads before UI rendering if needed

### Requirements to Structure Mapping

**Admin entry**

- `frontend/src/features/admin/pages/AdminPage.tsx`
- optionally `frontend/src/test/admin-client-modal.test.tsx` or a dedicated new panel test file

**Dry-run and apply contract**

- `backend/app/api/routes/admin_data_ingestion.py`
- `backend/app/schemas/indicator_load.py`
- `backend/app/services/indicator_carga_service.py`

**Audit trail**

- `backend/app/storage/ingestion_execution_repository.py`
- `backend/app/storage/store_registry.py`

**Rollback**

- `backend/app/api/routes/admin_data_ingestion.py`
- `backend/app/services/indicator_carga_service.py`
- `backend/app/operations/storage_maintenance.py` reused, not replaced

### Integration Points

**Internal communication**

- Admin panel -> frontend service -> admin ingestion API
- API route -> `IndicatorCargaService`
- service -> measurement/checkpoint repositories + audit repository + storage maintenance

**External integrations**

- none in MVP

**Data flow**

1. uploaded file enters backend boundary
2. backend validates and computes per-item outcome
3. dry-run returns structured preview only
4. apply snapshots registered stores, writes valid enrollments, records audit, returns execution report
5. rollback restores from recorded snapshot and records rollback outcome

## Architecture Validation Results

### Coherence Validation

The architecture is coherent with the current brownfield:

- it reuses the current admin auth boundary
- it preserves the current indicator normalization and replace semantics
- it uses the existing JSON snapshot tooling rather than inventing a second operational path
- it avoids breaking frozen v1 endpoints

### Requirements Coverage Validation

Covered by this architecture:

- admin-only access
- dedicated `Ingestao de Dados` admin entry
- structured source selection
- backend `dry_run`
- explicit confirmation before apply
- backup before write
- structured execution result
- minimal audit trail
- rollback path
- constrained JSON target list

Intentionally deferred:

- generic ingestion for all JSON stores
- automated scheduling
- analytics dashboard over ingestion history

### Implementation Readiness Validation

AI-agent implementation readiness is high because the architecture fixes the main ambiguity points:

- official source model: uploaded JSON file
- official target scope: measurements, checkpoints, audit store only
- official duplication rule: reject duplicates inside the batch, replace existing enrollment slice on apply
- official UI placement: new admin panel inside `AdminPage`
- official operational model: dry-run, apply with backup, operator-first rollback

### Gap Analysis

The following approvals are still required before implementation should widen scope:

1. confirm that the MVP should stay limited to indicator ingestion rather than generic JSON ingestion
2. confirm that uploaded JSON file is the official source model
3. confirm that replace-for-enrollment remains acceptable for existing persisted indicator data
4. confirm that rollback is operator-assisted first, not a primary UI action

### Architecture Readiness Assessment

Overall status: READY FOR EPICS AND STORIES AFTER SCOPE APPROVAL

Confidence level: medium-high

Key strengths:

- smallest safe brownfield extension
- explicit operational safety model
- explicit write-target list
- clean fit with existing frontend and backend conventions

Areas for later enhancement:

- scoped snapshots instead of full registered-store snapshots
- richer item-level conflict taxonomy
- self-service rollback UI only if operationally justified

## Implementation Handoff

### First Implementation Priority

Create epics and stories in this order:

1. admin panel entry and frontend contract
2. backend `dry_run` endpoint and validator
3. apply orchestration with snapshot and audit store
4. rollback endpoint or operator-assisted helper plus audit update
5. operational documentation and tests

### AI Agent Guidance

- Do not describe this feature as already implemented.
- Do not widen the target JSON list without an approved architecture update.
- Do not move alias handling or raw source parsing into React components.
- Do not bypass `storage_maintenance.py` for backup and restore.
- Do not change the existing student indicator-load endpoint unless a story explicitly requires compatibility work.
