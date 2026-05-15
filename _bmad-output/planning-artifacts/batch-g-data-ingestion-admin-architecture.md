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

  - docs/architecture/new_database_architecture.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-05-08.md
### Requirements Overview

**Functional requirements**
date: "2026-05-08"
The solution must allow an admin user to:

completedAt: "2026-05-08"
scope: "data-ingestion-admin-and-persistence-transition"
- identify the ingestion origin
- run a dry-run without persisting business data
- review a structured preview before confirming the write
  - docs/architecture/new_database_architecture.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-05-08.md
- execute the apply step only after explicit confirmation
- receive an execution identifier and structured result
# Batch G Data Ingestion and Persistence Transition Architecture

This document supersedes the earlier narrow ingestion-only interpretation.

The approved change proposal reclassifies the work as a major architectural transition. The platform now needs an architecture that explicitly separates:

- the current JSON-backed runtime that still powers the API today
- the target relational database architecture defined in `docs/architecture/new_database_architecture.md`
- the migration and coexistence rules required to move between them without violating the frozen v1 API contract

The architecture remains brownfield and stabilization-first. It does not authorize a big-bang rewrite.

## Project Context Analysis

### Requirements Overview

**Functional requirements**

The revised architecture must support two parallel needs:

1. keep the current admin/student/mentor platform working on the existing JSON-backed runtime
2. prepare a controlled migration path toward a relational model with:
   - organizations
   - users
   - products
   - product pillars
   - product metrics
   - enrollments

It must also provide explicit decisions for:

- how current domain entities map to target tables
- how repository coexistence is handled during transition
- where metric DSL evolution is allowed and where compatibility must be preserved
- how backup and rollback work while two persistence models may temporarily coexist
- what planning artifacts must be updated before epics, stories, and sprint planning continue

**Non-functional requirements**

- preserve the frozen v1 API contract
- keep FastAPI routes thin and business logic in services
- keep the current standardized error envelope `{ error: { status, code, message, details } }`
- avoid simultaneous uncontrolled writers across JSON and relational stores
- preserve operational recoverability during migration
- keep frontend DTO expectations stable even when backend canonical storage changes

**Scale and complexity**

This is now a major platform refactor with two tracks:

- Track 1: stabilize the current JSON-backed runtime
- Track 2: design and sequence migration to the relational target model

The complexity is no longer limited to Batch G ingestion. It affects core runtime persistence, domain naming, canonical exports, and route/service/repository boundaries.

### Technical Constraints and Dependencies

- The live backend still relies on `JsonRepository` across the primary domain repositories.
- The route layer currently instantiates those repositories directly in several places.
- `backend/app/storage/canonical_repositories.py` already provides a partial domain bridge and is the best current seam for coexistence.
- `backend/app/storage/product_repository.py` is currently an alias over `ProtocolRepository`, which confirms that the product terminology is still transitional in code.
- `backend/app/operations/storage_maintenance.py` currently backs up and restores JSON stores only.
- The frozen v1 contract keeps endpoint names and field types stable in the mentoring vocabulary.
- The new target schema does not yet define relational tables for measurements, checkpoints, or measurement overalls.

### Cross-Cutting Concerns Identified

- domain naming drift between current v1 terminology and target relational terminology
- repository lifecycle drift between file-backed stores and future relational tables
- rollout safety for score and metric semantics
- operational recovery when JSON and relational persistence have different backup mechanics
- compatibility of admin, mentor, student, radar, matrix, and command-center reads
- migration sequencing for entities that do not yet have target relational tables

## Starter Template Evaluation

### Primary Technology Domain

Brownfield platform transition on the existing stack:

- frontend: React 18 + Vite + TypeScript strict
- backend: FastAPI + Pydantic v2
- current persistence: JSON repositories
- target persistence: relational database architecture compatible with Supabase/Postgres

### Selected Foundation

No stack replacement is approved.

The selected foundation is a coexistence architecture:

- current runtime remains authoritative on JSON-backed stores until each migration slice is explicitly cut over
- target relational tables are introduced incrementally behind migration-specific adapters and validation flows
- canonical domain adapters become the transition seam between current naming and target naming

### First Implementation Foundation

The first implementation priority is not repository replacement. It is baseline stabilization.

Before any repository cutover:

1. fix current route/service wiring regressions
2. restore trustworthy API regression signals in the JSON runtime
3. document domain mapping and migration boundaries
4. decide the repository coexistence strategy per entity class

## Core Architectural Decisions

### Decision Priority Analysis

**Critical decisions**

- Separate present-state runtime architecture from target-state relational architecture.
- Keep a single source of truth per migration phase.
- Use canonical adapters as the transition seam rather than leaking target naming into v1 routes.
- Preserve v1 route names, response field types, and mentoring vocabulary.
- Treat measurements, checkpoints, and measurement overalls as unresolved relational targets until explicit table design exists.
- Preserve JSON snapshot tooling for the JSON runtime and define a separate rollback strategy for relational migrations.

**Important decisions**

- Document exact current->target entity mappings.
- Sequence read migration before write migration where practical.
- Keep metric DSL evolution behind repository/service boundaries, not in route DTOs or frontend components.
- Distinguish between platform canonical naming and frozen v1 external naming.

**Deferred decisions**

- final relational design for measurements and checkpoints
- final relational design for measurement overalls / derived projections
- whether relational cutover uses shadow reads, dual-write, or batch reconciliation for late migration phases
- whether `protocol` remains a persisted concept or is reduced to metadata/versioning inside product/pillar structures

### Scope Boundary

This architecture now covers two explicit tracks.

**Track 1: Current-runtime stabilization**

- current JSON repositories remain authoritative
- route/service mismatches are fixed
- API regression is restored
- Batch G ingestion remains limited to approved JSON targets

**Track 2: Persistence transition planning**

- target relational tables are treated as the future canonical storage model for the entities they define
- coexistence rules are documented before implementation
- migration proceeds entity by entity, not as a platform-wide swap

This document does not authorize direct replacement of all repositories at once.

### Current Runtime Architecture

The current runtime remains organized around:

- `ClientRepository` for client companies
- `OrganizationRepository` for mentoria/product-like records scoped to a client
- `MentorRepository` and `StudentRepository` for role-specific people records
- `EnrollmentRepository` for mentor/student/product assignment state
- `ProtocolRepository`, `PillarRepository`, and `MetricRepository` for method configuration
- `MeasurementRepository`, `CheckpointRepository`, and `MeasurementOverallRepository` for operational metric data and derived views

Key implications:

- current runtime naming is historically layered and not yet normalized
- route handlers and services often depend on concrete repositories directly
- current backup and restore tooling assumes JSON stores are the authoritative source

### Target Relational Architecture

The target architecture introduces the following relational backbone:

- `deva_accmed_organizations`
- `deva_accmed_users`
- `deva_accmed_products`
- `deva_accmed_product_pillars`
- `deva_accmed_product_metrics`
- `deva_accmed_enrollments`

Key implications:

- identity is unified under `users` rather than split mentor/student stores
- product and product-metric naming becomes canonical in storage
- enrollments reference provider user, client user, and product explicitly
- the target schema formalizes product pillars and product metrics but does not yet formalize measures/checkpoints

### Domain Mapping Between Current Entities and Target Tables

The migration cannot rely on superficial naming. The correct mapping is:

| Current runtime entity | Current meaning in code | Target relational table | Migration note |
| --- | --- | --- | --- |
| `ClientRepository` | client company/account | `deva_accmed_organizations` | direct semantic match for company/brand/cnpj/timezone/currency |
| `OrganizationRepository` | mentoria/product-like unit linked to a client | `deva_accmed_products` | current `organization` name is legacy v1 naming, not target organization semantics |
| `MentorRepository` | provider person record | `deva_accmed_users` | migrate as `role = provider/mentor` compatible user rows |
| `StudentRepository` | end-user/client participant record | `deva_accmed_users` | migrate as `role = client_user/student` compatible user rows |
| `EnrollmentRepository` | assignment between mentor, student, and organization/product | `deva_accmed_enrollments` | rename fields through adapter layer, not public route changes |
| `ProtocolRepository` | method/version context | no direct target table in supplied schema | remains transitional metadata until target persistence is explicitly designed |
| `PillarRepository` | pillar scoped by protocol/method | `deva_accmed_product_pillars` | requires protocol->product/method-version mapping during migration |
| `MetricRepository` | metric scoped by pillar/protocol | `deva_accmed_product_metrics` | metrics migrate only after pillar mapping is stable |
| `MeasurementRepository` | raw measurement values | no target table yet | keep JSON authoritative until relational schema exists |
| `CheckpointRepository` | journey checkpoint values | no target table yet | keep JSON authoritative until relational schema exists |
| `MeasurementOverallRepository` | derived summary/projection | no target table yet | treat as derived read model, not migration-first storage |
| `ContactUserRepository` | contact metadata | unresolved | decide whether it becomes user metadata or a separate relational model |

This mapping is the architectural contract for migration planning.

### Repository Migration and Coexistence Strategy

#### Guiding rule

At any point in time, each business entity class has exactly one authoritative write path.

#### Transition seam

The preferred seam is the canonical adapter layer already present in `backend/app/storage/canonical_repositories.py`.

That means:

- v1 routes continue to consume current mentoring vocabulary DTOs
- services may call canonical adapters or migration-aware ports internally
- target relational naming must not leak directly into frozen v1 route contracts

#### Migration phases

**Phase 0: Stabilize current JSON runtime**

- fix route/service wiring problems
- run current API regression suite
- keep JSON as the only writer

**Phase 1: Mapping and export validation**

- harden canonical export/mapping logic for products, users, pillars, metrics, and enrollments
- validate that JSON data can be transformed to the target table shape deterministically
- no relational writes required for production traffic yet

**Phase 2: Relational mirror for entities with direct target tables**

- add relational repositories for organizations, users, products, product pillars, product metrics, and enrollments
- populate them through controlled migration/import jobs
- keep JSON authoritative for runtime writes until validation is complete

**Phase 3: Shadow-read validation**

- compare relational reads against JSON/canonical outputs for selected admin surfaces
- verify semantic parity before route/service cutover

**Phase 4: Controlled cutover per entity slice**

- switch one entity slice at a time behind service/repository boundaries
- preserve external v1 DTOs and endpoint names
- only cut over entities whose target relational schema is complete

**Phase 5: Post-schema expansion for measures/checkpoints**

- measurements, checkpoints, and derived overalls remain on JSON until their target relational design exists
- do not force them into the current relational schema by overloading existing tables

#### Explicit non-decision

This architecture does not approve unrestricted dual-write.

Dual-write is deferred unless the team later defines:

- idempotency guarantees
- reconciliation jobs
- drift detection
- rollback rules for divergent writes

### API Compatibility Boundaries Under Frozen v1

The frozen v1 contract remains the boundary for all current frontend-facing APIs.

**Must remain stable**

- endpoint paths and HTTP methods
- current mentoring vocabulary in route names and public error semantics
- field presence and field types in existing response DTOs
- standardized error envelope

**May change internally**

- repository implementation behind services
- canonical entity names used inside migration adapters
- persistence source for a route, if output shape and semantics remain compatible

**Must not happen during migration**

- exposing `product_id`, `provider_user_id`, or `client_user_id` directly as replacements for v1 public fields without versioning
- renaming `organization_id` / `protocol_id` fields in v1 payloads
- pushing target naming changes into frontend components as an ad hoc migration shortcut

### Metric DSL Architecture Boundary

Metric DSL evolution is now part of the persistence transition architecture.

Rules:

- target DSL semantics live behind metric repository and score service boundaries
- frontend remains insulated by current backend payload contracts
- metric configuration migration must preserve existing score behavior for current metrics unless intentionally versioned
- descriptive labels must not become canonical logical keys in the new model

The implemented v2 scoring direction is compatible with this architecture, but it is not enough on its own to define repository migration.

### Backup and Rollback

Current JSON runtime rollback remains implemented by `backend/app/operations/storage_maintenance.py` and is valid only for JSON-backed stores.

Therefore:

- JSON-backed flows keep backup-before-write and restore semantics through the existing snapshot tooling
- relational migration flows require a separate backup/rollback discipline, such as:
  - transactional SQL migration scripts where possible
  - database snapshots or export bundles for data migrations
  - migration run manifests with row counts and reconciliation outputs

Architectural rule:

- JSON snapshot restore must never be described as sufficient rollback for relational state
- relational cutover steps must define their own restore point before execution

### Validation and Sequencing Policy

Before any relational cutover begins:

1. current JSON-backed API regression must be green
2. entity mapping rules must be documented and testable
3. canonical export outputs must be verifiable against target schema expectations
4. backup and rollback procedures for the relevant persistence slice must be approved

### Frontend and Operational Implications

Frontend remains aligned to v1 route families and adapters.

Operational implications:

- admin ingestion in Batch G still writes only approved JSON targets in the current runtime
- command center, radar, matrix, and student workspace remain consumers of the current service contracts until cutover per slice is validated
- operator runbooks must eventually distinguish JSON recovery flows from relational recovery flows

## Implementation Patterns and Consistency Rules

### Naming Patterns

- External v1 API naming remains `mentor`, `aluno`, `mentoria`, `metodo`.
- Internal canonical naming may use `product`, `provider`, `end_user`, and `assignment`.
- Relational storage naming follows the new table semantics.
- Route DTOs must not expose internal canonical renames unless a new contract version is created.

### Structure Patterns

- routes call services
- services depend on repositories or canonical adapters
- repositories own persistence mechanics
- migration jobs and reconciliation scripts live outside route handlers
- current JSON repositories and future relational repositories must both be hidden behind service-level orchestration

### Communication Patterns

- current runtime routes continue using existing service signatures until refactor slices are ready
- migration-specific transforms happen in canonical adapters or dedicated migration services
- reconciliation outputs must be explicit artifacts, not implicit assumptions from successful inserts

### Migration Rules

- one authoritative writer per entity per phase
- no silent route contract changes during migration
- no direct frontend dependency on target relational naming
- no migration of measurements/checkpoints into undefined relational destinations

### Enforcement Guidelines

- every repository swap requires nearest-layer tests plus route-level regression for affected surfaces
- every relational migration step requires a documented rollback point
- every changed artifact that affects implementation sequencing must be updated before sprint planning resumes

## Project Structure and Boundaries

### Scoped Project Directory Structure

```txt
repo/
  backend/
    app/
      api/
        routes/
          admin_students.py
          admin_metrics.py
          student_workspace.py
          mentor.py
      services/
        metric_score_service.py
        student_workspace_service.py
        indicator_carga_service.py
        admin_metric_service.py
        method_config_service.py
        student_vinculo_service.py
      storage/
        json_repository.py
        canonical_repositories.py
        client_repository.py
        organization_repository.py
        protocol_repository.py
        pillar_repository.py
        metric_repository.py
        mentor_repository.py
        student_repository.py
        enrollment_repository.py
        measurement_repository.py
        checkpoint_repository.py
        measurement_overall_repository.py
        relational/
          organizations_repository.py
          users_repository.py
          products_repository.py
          product_pillars_repository.py
          product_metrics_repository.py
          enrollments_repository.py
      operations/
        storage_maintenance.py
        export_canonical_data.py
        migration/
          export_current_runtime.py
          import_relational_seed.py
          reconcile_runtime_vs_relational.py
    tests/
      api/
      integration/
      unit/
      e2e/
  docs/
    architecture/
      platform_architecture_operational_model.md
      new_database_architecture.md
    mvp-mentoria/
      contracts-freeze-v1.md
      frontend-integration-architecture.md
      backend-test-strategy.md
  _bmad-output/
    planning-artifacts/
      sprint-change-proposal-2026-05-08.md
      batch-g-data-ingestion-admin-architecture.md
      batch-g-data-ingestion-admin-epics-and-stories.md
```

### Architectural Boundaries

**Current-runtime boundary**

- JSON repositories remain the runtime persistence implementation until a slice is cut over

**Canonical boundary**

- canonical repositories translate legacy runtime entities into product/provider/end-user abstractions used for migration planning

**Relational boundary**

- future relational repositories must align exactly to the new schema and remain hidden behind services or migration operations until validated

**Contract boundary**

- frozen v1 routes remain stable regardless of internal storage evolution

### Requirements-to-Structure Mapping

- Current API stabilization: route files, affected services, existing JSON repositories, API tests, E2E smoke tests
- Domain mapping and coexistence: `canonical_repositories.py`, migration operations, architecture artifacts, reconciliation tests
- Metric DSL evolution: `metric_score_service.py`, `metric_repository.py`, method/admin metric services, metric tests
- Backup/rollback split: `storage_maintenance.py` for JSON, new relational migration runbooks/scripts for relational phases

### Required Artifact Updates Before Epics, Stories, and Sprint Planning Continue

The following artifacts must be updated or confirmed before implementation planning resumes:

1. `docs/architecture/new_database_architecture.md`
   - must remain the target-state relational reference
2. `_bmad-output/planning-artifacts/batch-g-data-ingestion-admin-architecture.md`
   - now serves as the transition architecture between current and target states
3. `docs/mvp-mentoria/frontend-integration-architecture.md`
   - must add semantic compatibility guidance for persistence/domain migration
4. `docs/mvp-mentoria/backend-test-strategy.md`
   - must add coexistence, mapping, rollback, and cutover validation gates
5. `_bmad-output/planning-artifacts/batch-g-data-ingestion-admin-epics-and-stories.md`
   - must split stabilization work from migration-planning work
6. sprint planning inputs
   - must not assume feature expansion continues before architecture and migration boundaries are accepted

## Architecture Validation Results

### Coherence Validation

The revised architecture is coherent because it stops mixing present-state and target-state assumptions.

- current JSON runtime concerns stay in Track 1
- target relational persistence concerns stay in Track 2
- canonical adapters provide a valid transition seam already grounded in the codebase
- frozen v1 compatibility remains the outer contract boundary

### Requirements Coverage Validation

This architecture covers the requested revision scope:

- current JSON-backed runtime and target relational runtime are explicitly separated
- current entities are mapped to target tables with unresolved gaps called out
- repository migration and coexistence strategy is defined by phase
- API compatibility boundaries are stated under the frozen v1 contract
- backup and rollback are split correctly by persistence model
- artifact updates required before planning resumes are listed explicitly

### Implementation Readiness Validation

The architecture is ready for planning and sequencing, but not yet for unconstrained implementation.

Ready now:

- current-runtime stabilization work
- mapping and export validation work
- planning/artifact updates

Not ready yet:

- full repository cutover
- measurement/checkpoint migration
- public API contract rename or vocabulary change

### Gap Analysis

**Critical gaps**

- no target relational tables yet for measurements, checkpoints, and measurement overalls
- no approved relational rollback runbook yet
- current route/service wiring still has known defects that block trustworthy regression

**Important gaps**

- explicit decision needed for `ContactUserRepository`
- explicit decision needed for whether `ProtocolRepository` survives as persisted method-version state
- relational repository interfaces are not yet defined in code

**Nice-to-have gaps**

- automated reconciliation reports between canonical JSON export and relational mirror
- shadow-read diagnostics for admin surfaces before cutover

### Architecture Readiness Assessment

**Overall Status:** READY FOR REPLANNING AND STABILIZATION, NOT READY FOR FULL PERSISTENCE CUTOVER

This architecture is sufficient to:

- guide the next planning updates
- anchor entity mapping decisions
- prevent accidental contract drift during migration

It is intentionally not a green light for broad implementation against the target relational model until the missing slices are designed.

### Implementation Handoff

**Development**

- restore current runtime stability first
- implement mapping/export validation next
- keep repository cutover behind service boundaries and migration scripts

**Architecture / Product**

- approve unresolved mappings and target-state gaps
- decide measurement/checkpoint relational design before those slices migrate

**QA**

- preserve current-runtime API regression as the baseline gate
- add migration-sensitive tests before any slice cutover

**Planning**

- update epics and stories to split stabilization from migration
- do not advance sprint planning on hidden assumptions about storage cutover
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
