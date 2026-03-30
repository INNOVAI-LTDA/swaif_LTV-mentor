---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - _bmad-output/project-context.md
  - docs/discovery/data-ingestion-admin-brief.md
  - docs/mvp-mentoria/batch-g-data-ingestion-admin-current-state.md
  - docs/architecture/platform_architecture_operational_model.md
  - docs/mvp-mentoria/frontend-integration-architecture.md
  - docs/mvp-mentoria/contracts-freeze-v1.md
  - docs/mvp-mentoria/frontend-deployment-readiness-checklist.md
  - docs/admin-crud-spec.md
  - docs/admin-crud-implementation-plan.md
workflowType: "architecture"
project_name: "swaif_LTV-mentoria"
user_name: "dmene"
date: "2026-03-30"
lastStep: 8
status: "complete"
completedAt: "2026-03-30"
solutionAnchor:
  - docs/discovery/data-ingestion-admin-brief.md
  - docs/mvp-mentoria/batch-g-data-ingestion-admin-current-state.md
---

# Batch G Data Ingestion Admin Architecture

This document defines the brownfield architecture for the admin-facing data ingestion capability requested in Batch G.

The architecture is intentionally narrow:

- extend the existing admin-only student indicator load flow
- add preview/apply/backup/audit/rollback support around that flow
- keep writes limited to explicitly approved JSON stores
- avoid introducing a generic repository-wide importer in final stabilization mode

## Project Context Analysis

### Requirements Overview

**Functional requirements**

The solution must allow an admin user to:

- enter the admin surface and access an `Ingestao de Dados` operation
- identify the ingestion origin
- run a dry-run without persisting business data
- review a structured preview before confirming the write
- execute the apply step only after explicit confirmation
- receive an execution identifier and structured result
- preserve enough evidence for support and rollback

**Non-functional requirements**

- preserve the existing admin role boundary on frontend and backend
- keep the backend error envelope `{ error: { status, code, message, details } }`
- avoid raw filesystem path exposure in the UI
- keep writes constrained to approved JSON targets
- preserve current brownfield conventions: thin FastAPI routes, service-layer business logic, JSON-backed repositories, frontend adapter/service boundaries
- add nearest-layer tests for preview, apply, backup, audit, and rollback-sensitive behavior

**Scale and complexity**

- Primary domain: full-stack brownfield admin workflow
- Complexity level: medium
- Estimated architectural components: 1 frontend admin panel, 1 backend orchestration service, 1 execution-audit repository, contract/schema extensions, targeted tests

### Technical Constraints and Dependencies

- The current repo already has `/app/admin` behind `RequireAdmin` and backend `require_admin_user`.
- The current ingestion capability is `POST /admin/alunos/{student_id}/indicadores/carga-inicial`.
- Current persistence semantics are `replace_for_enrollment(...)` for measurements and checkpoints.
- Snapshot and restore utilities already exist in `backend/app/operations/storage_maintenance.py`.
- Frontend integration must continue to use `httpClient`, `AppError`, adapters, and centralized env access.
- Contract freeze v1 forbids silent breaking changes to existing routes and error payload behavior.

### Cross-Cutting Concerns Identified

- authorization and role gating
- validation before persistence
- backup-before-write
- immutable execution audit
- rollback procedure
- frontend safe handling of preview/apply states
- explicit scope control for allowed JSON targets

## Starter Template Evaluation

### Primary Technology Domain

Brownfield full-stack web application on the repo's existing React/Vite frontend and FastAPI/Pydantic backend.

### Selected Foundation

No new starter template or stack change is approved for this batch.

**Rationale**

- the repository is already operational and in final stabilization mode
- the current stack already contains the exact layers needed for this feature
- introducing a starter, framework migration, or parallel architecture would increase risk without solving a current blocker

**Brownfield baseline retained**

- Frontend: React 18 + Vite + TypeScript strict mode
- Backend: FastAPI + Pydantic + JSON repositories
- Admin shell and route model: existing `/app/admin` surface
- Operational snapshot tooling: existing storage maintenance module

**First implementation priority**

Implement preview/apply orchestration around the existing indicator load flow before any wider ingestion ambition.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical decisions**

- freeze the MVP scope to indicator ingestion for one selected student enrollment at a time
- separate preview from apply in the backend contract
- require backup snapshot before any apply write
- persist execution audit records
- preserve current replace-for-enrollment semantics

**Important decisions**

- place the new entry inside the existing admin surface instead of creating a new top-level route
- keep rollback operator-assisted in MVP rather than exposing a UI rollback button
- introduce forward-compatible source metadata without committing to multi-target file import in this batch

**Deferred decisions**

- generic multi-entity JSON ingestion
- recurring or scheduled ingestion
- multi-user concurrent bulk ingestion workflows
- UI-native rollback execution
- generic file-upload ingestion beyond the current indicator domain

### Scope Boundary

Batch G does **not** create a generic "write any JSON file" capability.

Approved business targets for this batch:

- `measurements`
- `checkpoints`

Approved operational target for this batch:

- `ingestion_executions`

All other JSON-backed entities remain outside this architecture until explicitly approved in a later artifact.

### Admin Entry and Frontend Surface

The feature will live inside the existing `/app/admin` route and `AdminShell`.

Recommended UI entry:

- add a dedicated admin panel keyed by `panel=ingestao-dados`
- keep the current student context model: client -> product -> mentor -> student
- render a dedicated ingestion panel/wizard for the selected student instead of a new top-level route

This keeps routing centralized, preserves the existing admin shell pattern, and avoids a second admin surface.

### Source Model

The contract will include source metadata from day one, but Batch G will activate only one source mode:

- active in MVP: `manual_assisted`
- reserved for future expansion: `json_file`

Required source metadata in MVP:

- `source_type`
- `source_label`

This satisfies the operational requirement to record origin while keeping the batch aligned to the existing brownfield flow. File upload remains a future extension, not part of this stabilization batch.

### Backend Contract

Use the existing `admin_students.py` route module and extend the current indicator-load namespace with explicit preview/apply endpoints.

Recommended endpoints:

```txt
POST /admin/alunos/{student_id}/indicadores/carga-inicial/preview
POST /admin/alunos/{student_id}/indicadores/carga-inicial/apply
GET  /admin/ingestoes/{execution_id}
```

The existing endpoint:

```txt
POST /admin/alunos/{student_id}/indicadores/carga-inicial
```

should remain as a compatibility bridge during migration and internally delegate to the new apply orchestration until the frontend is fully moved.

#### Preview request

```json
{
  "source_type": "manual_assisted",
  "source_label": "Carga inicial guiada no admin",
  "duplication_mode": "replace_enrollment",
  "metric_values": [
    {
      "metric_id": "met_123",
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
```

#### Preview response

```json
{
  "execution_id": "ing_preview_001",
  "student_id": "std_1",
  "enrollment_id": "enr_1",
  "mode": "preview",
  "status": "previewed",
  "summary": {
    "received_metric_rows": 1,
    "received_checkpoint_rows": 1,
    "valid_metric_rows": 1,
    "valid_checkpoint_rows": 1,
    "rejected_rows": 0,
    "conflict_count": 0,
    "will_replace_measurements": 3,
    "will_replace_checkpoints": 2
  },
  "affected_stores": ["measurements", "checkpoints"],
  "conflicts": [],
  "rejections": []
}
```

#### Apply request

```json
{
  "preview_execution_id": "ing_preview_001",
  "confirm": true
}
```

#### Apply response

```json
{
  "execution_id": "ing_apply_001",
  "preview_execution_id": "ing_preview_001",
  "student_id": "std_1",
  "enrollment_id": "enr_1",
  "mode": "apply",
  "status": "applied",
  "measurement_count": 1,
  "checkpoint_count": 1,
  "affected_stores": ["measurements", "checkpoints"],
  "backup_ref": "snapshot-20260330T000000Z"
}
```

### Validation and Duplication Policy

Batch G freezes the duplication behavior to:

- `duplication_mode = replace_enrollment`

This is an explicit continuation of current repository behavior and not a new merge strategy.

Preview must validate at least:

- student exists
- active enrollment exists for the selected student
- every metric exists and is active
- metrics are valid for the selected product context
- checkpoint fields are valid
- payload shape is complete enough for apply
- counts of existing measurement/checkpoint rows that will be replaced

Apply must reject when:

- the preview execution does not exist
- the preview execution is not in `previewed` status
- the apply request references a different student than the preview
- the preview payload has expired or was invalidated by an earlier apply

### Orchestration and Audit

Introduce a dedicated backend orchestration service:

- `backend/app/services/admin_indicator_ingestion_service.py`

Responsibilities:

- normalize and validate preview input
- persist preview execution records
- create pre-apply backup snapshot
- call measurement/checkpoint repositories with current replace semantics
- persist final execution result
- trigger restore on post-snapshot apply failure

Introduce a dedicated JSON-backed execution repository:

- `backend/app/storage/ingestion_execution_repository.py`

Each execution record should capture:

- `id`
- `student_id`
- `enrollment_id`
- `requested_at`
- `performed_by`
- `mode`
- `status`
- `source_type`
- `source_label`
- `duplication_mode`
- normalized payload summary
- `total_received`
- `total_valid`
- `total_applied`
- `total_rejected`
- `conflicts`
- `rejections`
- `affected_stores`
- `backup_ref`
- internal `snapshot_dir` for operator use only
- `rollback_status`
- `error_code`
- `error_message`

### Backup and Rollback

Apply must create a backup snapshot before touching measurements or checkpoints.

Implementation rule:

1. load approved preview execution
2. acquire storage IO lock
3. create snapshot using existing `storage_maintenance.create_backup_snapshot(...)`
4. write measurements and checkpoints
5. persist apply execution result
6. on post-snapshot failure, call `restore_backup_snapshot(...)`
7. mark execution as `rolled_back` or `rollback_failed`

Rollback in MVP is operator-assisted, not user-driven in the UI.

Documented rollback path:

- operator locates execution by `execution_id`
- operator reads the internal snapshot reference from the audit store
- operator executes the documented restore command
- operator records the rollback outcome back into the execution log

### Error Handling

API failures must continue to use the standard envelope:

```json
{
  "error": {
    "status": 409,
    "code": "INGESTAO_CONFLICT",
    "message": "A carga nao pode ser aplicada neste estado.",
    "details": null
  }
}
```

Target failure classes:

- `401` missing or invalid token
- `403` non-admin access
- `404` student, enrollment, metric, or execution not found
- `409` invalid state transition, preview already applied, or restore conflict
- `422` invalid preview/apply payload

### Frontend Architecture

Frontend must follow the existing layered integration pattern:

- component/panel
- domain service
- shared `httpClient`
- adapter from API DTO to frontend domain

Recommended additions:

- `frontend/src/contracts/adminDataIngestion.ts`
- `frontend/src/domain/adapters/adminDataIngestionAdapter.ts`
- `frontend/src/domain/services/adminDataIngestionService.ts`
- `frontend/src/features/admin/components/AdminDataIngestionPanel.tsx`

Frontend rules for this feature:

- no raw API payload binding in React state
- no direct `import.meta.env` reads
- no fetch details in page JSX
- all API failures normalize through existing `AppError`
- copy remains in Portuguese
- UI shows intro -> edit -> preview -> apply result states

The current `AdminPage.tsx` can host the panel entry and current selected student context without a route redesign.

## Implementation Patterns and Consistency Rules

### Naming Patterns

**Backend**

- route paths remain in existing Portuguese admin namespace
- request/response schema fields remain `snake_case`
- execution repository file and service names remain explicit: `ingestion_execution`, `indicator_ingestion`

**Frontend**

- contracts and services use `adminDataIngestion*`
- UI-facing domain fields may use `camelCase`
- normalization from backend `snake_case` to frontend `camelCase` belongs in adapters, never in components

### Structure Patterns

- keep FastAPI route handlers thin inside `backend/app/api/routes/admin_students.py`
- put orchestration rules in `backend/app/services/admin_indicator_ingestion_service.py`
- keep JSON store read/write details inside repositories under `backend/app/storage`
- keep frontend feature code under `frontend/src/features/admin`
- keep API services under `frontend/src/domain/services`
- keep frontend tests under `frontend/src/test`
- keep backend tests split by `unit`, `api`, and `integration`

### Format Patterns

- preview/apply success payloads use direct JSON responses
- errors always use the standard envelope
- timestamps use ISO-8601 strings in UTC
- `affected_stores` uses explicit stable store names, not filesystem paths
- `backup_ref` is opaque and safe for UI display

### Communication Patterns

- preview writes only the execution log, never business stores
- apply consumes a preview execution ID instead of trusting a second ad hoc payload
- UI confirmation is not the safeguard by itself; backend preview/apply state is the safeguard

### Process Patterns

- every apply begins from a valid preview execution
- every apply records `performed_by`
- every apply creates backup before touching business stores
- every post-snapshot failure attempts restore
- every rollback outcome is recorded in the execution log

### Enforcement Guidelines

All AI agents must:

- keep allowed write targets limited to measurements, checkpoints, and ingestion_executions
- preserve replace-for-enrollment semantics unless a later approved architecture changes it
- avoid exposing server paths in any UI response or copy
- extend the nearest existing admin modules instead of introducing a parallel ingestion subsystem

## Project Structure and Boundaries

### Scoped Project Directory Structure

```txt
_bmad-output/
  planning-artifacts/
    batch-g-data-ingestion-admin-architecture.md

frontend/
  src/
    contracts/
      adminDataIngestion.ts
    domain/
      adapters/
        adminDataIngestionAdapter.ts
      services/
        adminDataIngestionService.ts
    features/
      admin/
        components/
          AdminDataIngestionPanel.tsx
        pages/
          AdminPage.tsx
    test/
      admin-data-ingestion-panel.test.tsx
      admin-client-modal.test.tsx

backend/
  app/
    api/
      routes/
        admin_students.py
    schemas/
      indicator_load.py
    services/
      admin_indicator_ingestion_service.py
      indicator_carga_service.py
    storage/
      ingestion_execution_repository.py
      measurement_repository.py
      checkpoint_repository.py
    operations/
      storage_maintenance.py
  tests/
    api/
      test_admin_indicator_ingestion_api.py
    unit/
      test_admin_indicator_ingestion_service.py
    integration/
      test_admin_indicator_ingestion_storage.py

docs/
  mvp-mentoria/
    data-ingestion-admin-operations.md
```

### Architectural Boundaries

**Frontend boundary**

- `AdminPage.tsx` owns panel selection and shell integration
- `AdminDataIngestionPanel.tsx` owns the wizard state only
- `adminDataIngestionService.ts` owns HTTP calls
- adapter owns DTO-to-domain normalization

**Backend boundary**

- `admin_students.py` owns HTTP routing and error mapping
- `admin_indicator_ingestion_service.py` owns preview/apply orchestration
- `indicator_carga_service.py` remains the existing domain helper for student/enrollment/metric context and read-model behavior
- repositories own JSON persistence
- `storage_maintenance.py` remains the backup/restore implementation

**Data boundary**

- business writes: `measurements`, `checkpoints`
- operational writes: `ingestion_executions`
- snapshots cover the current registered JSON storage set through the existing snapshot module

### Requirements-to-Structure Mapping

**Admin-only entry**

- frontend `AdminPage.tsx`
- existing `/app/admin` route and `RequireAdmin`
- backend `require_admin_user`

**Dry-run and preview**

- frontend `AdminDataIngestionPanel.tsx`
- backend `admin_students.py`
- backend `admin_indicator_ingestion_service.py`
- backend `ingestion_execution_repository.py`

**Apply with backup**

- backend `admin_indicator_ingestion_service.py`
- backend `storage_maintenance.py`
- backend `measurement_repository.py`
- backend `checkpoint_repository.py`

**Audit and rollback**

- backend `ingestion_execution_repository.py`
- docs `data-ingestion-admin-operations.md`

**Coverage**

- frontend tests for panel flow
- backend API tests for preview/apply envelopes and permissions
- backend unit/integration tests for backup, write, and restore behavior

## Architecture Validation Results

### Coherence Validation

The architecture is coherent with the current repository because it:

- reuses the existing admin route and auth boundary
- preserves current measurement/checkpoint replace semantics
- routes backup and restore through the existing operations module
- keeps frontend integration inside the current service/adapter/httpClient model
- does not introduce any new persistence technology or parallel admin surface

### Requirements Coverage Validation

The architecture covers the requested Batch G outcomes:

- admin-only access: covered
- dedicated admin entry for ingestion: covered
- dry-run without business persistence: covered
- preview summary before apply: covered
- explicit confirmation and apply: covered
- backup before write: covered
- structured result and execution identifier: covered
- audit trail: covered
- operational rollback path: covered
- nearest-layer tests and operational docs: covered

### Implementation Readiness Validation

This architecture is ready for implementation because it fixes the key ambiguities that would otherwise cause agent divergence:

- allowed write targets are explicit
- duplication policy is explicit
- preview/apply contract is explicit
- audit store ownership is explicit
- rollback posture is explicit
- frontend placement is explicit

### Gap Analysis

**Accepted MVP gaps**

- no generic file upload in this batch
- no multi-student batch apply
- no UI rollback button
- no generic ingestion of clients, mentors, products, or relations

These are intentional scope cuts, not omissions.

### Architecture Readiness Assessment

**Overall status:** READY FOR IMPLEMENTATION AFTER SCOPE APPROVAL

**Confidence level:** high

**Key strengths**

- smallest safe extension of an already working flow
- reuses existing auth, admin shell, JSON repositories, and snapshot tooling
- adds the operational controls explicitly missing from current state
- avoids widening the system into an unsafe generic importer

**Areas for future enhancement**

- activate `json_file` source mode
- add multi-student or multi-enrollment batch ingestion
- expose execution detail and rollback tools in the admin UI
- extend approved targets beyond measurements/checkpoints only through a new architecture decision

### Implementation Handoff

AI agents implementing this architecture should proceed in this order:

1. extend backend schemas and preview/apply routes
2. add execution repository and orchestration service
3. wire snapshot-before-apply and restore-on-failure behavior
4. update frontend contracts/services/adapters
5. integrate the `Ingestao de Dados` panel into `AdminPage`
6. add API, service, integration, and frontend tests
7. add operator documentation for restore by `execution_id`

First implementation priority:

- define the preview/apply contract and execution audit store before touching the UI flow
