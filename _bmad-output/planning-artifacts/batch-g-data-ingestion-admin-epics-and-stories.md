---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/batch-g-data-ingestion-admin-architecture.md
  - _bmad-output/project-context.md
  - docs/mvp-mentoria/batch-g-data-ingestion-admin-current-state.md
  - docs/discovery/data-ingestion-admin-brief.md
  - docs/architecture/platform_architecture_operational_model.md
  - docs/mvp-mentoria/frontend-integration-architecture.md
  - docs/mvp-mentoria/contracts-freeze-v1.md
  - docs/mvp-mentoria/frontend-deployment-readiness-checklist.md
  - docs/admin-crud-spec.md
  - docs/admin-crud-implementation-plan.md
workflowType: epics-and-stories
project_name: swaif_LTV-mentoria
user_name: dmene
date: 2026-03-30
lastStep: 4
status: complete
completedAt: 2026-03-30
scope: batch-g-data-ingestion-admin
---

# swaif_LTV-mentoria - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for `batch-g-data-ingestion-admin`, decomposing the approved brownfield architecture into implementable stories that preserve the current admin indicator-load boundaries and final-stabilization constraints.

## Requirements Inventory

### Functional Requirements

FR1: Admin users must be able to access an `Ingestao de Dados` operation from the existing `/app/admin` surface without creating a parallel route family or auth path.

FR2: The admin workflow must operate on the existing selected-student context and record ingestion origin through `source_type` and `source_label`, with `manual_assisted` as the active MVP source mode.

FR3: The backend must provide a dedicated preview flow that validates the ingestion payload without persisting business writes.

FR4: The preview flow must validate student, active enrollment, active metrics, product-context compatibility, checkpoint rules, and replacement impact for the selected enrollment.

FR5: The preview response must return a structured execution identifier, summary counts, conflicts, rejections, and the approved affected store list.

FR6: The apply flow must require explicit confirmation and a valid preview execution for the same student context.

FR7: The apply flow must rerun validation, create a backup snapshot before write, and write only to the approved business stores.

FR8: The apply flow must preserve current `replace_enrollment` semantics for `measurements` and `checkpoints`.

FR9: The system must persist execution audit records for preview and apply, including operator, timestamps, source metadata, summary data, affected stores, backup reference, and rollback status.

---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/project-context.md
  - docs/architecture/platform_architecture_operational_model.md
  - docs/architecture/new_database_architecture.md
  - docs/mvp-mentoria/contracts-freeze-v1.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-05-08.md
  - _bmad-output/planning-artifacts/batch-g-data-ingestion-admin-architecture.md
workflowType: epics-and-stories
project_name: swaif_LTV-mentoria
user_name: dmene
date: 2026-05-08
lastStep: 4
status: complete
completedAt: 2026-05-08
scope: batch-g-data-ingestion-admin-and-persistence-transition
---

# swaif_LTV-mentoria - Epic Breakdown

## Overview

This document revises the existing Batch G epic and story plan to align with the approved major change proposal and the updated transition architecture.

The plan is no longer limited to a narrow ingestion enhancement. It now decomposes the approved work into two explicit tracks:

- Track 1: stabilize the current JSON-backed runtime and keep the valid Batch G ingestion scope operating safely inside that runtime
- Track 2: prepare, validate, and gate the controlled migration path toward the target relational architecture without breaking the frozen v1 API contract

The plan preserves the original Batch G scope where it is still valid, especially the admin-only ingestion flow and JSON-authoritative write path. It removes assumptions that direct repository replacement or broad persistence cutover can happen immediately.

## Requirements Inventory

### Functional Requirements

FR1: The current JSON-backed runtime must be stabilized and regain a trustworthy green regression baseline before any relational cutover work can begin.

FR2: Batch G admin ingestion must remain inside the existing admin surface and continue writing only to the approved JSON-backed targets while the JSON runtime is authoritative.

FR3: The platform must define and validate deterministic mappings from current runtime entities to the target relational entities for organizations, users, products, product pillars, product metrics, and enrollments.

FR4: Repository coexistence must be implemented through canonical adapters or migration-aware ports so that target relational naming does not leak into frozen v1 routes and DTOs.

FR5: Relational mirror repositories and controlled migration jobs must be introduced only for entities that already have direct target relational tables.

FR6: Selected admin/runtime surfaces must support shadow-read parity validation between current JSON-backed outputs and relational/canonical outputs before any cutover.

FR7: Persistence cutover must happen one entity slice at a time behind service and repository boundaries while preserving frozen v1 endpoint paths, field presence, and field types.

FR8: Measurements, checkpoints, and derived measurement overalls must remain JSON-backed until an explicit target relational schema exists for them.

FR9: Backup and rollback must be split by persistence model: JSON flows continue using existing snapshot tooling, while relational migrations define dedicated restore points, manifests, and reconciliation evidence.

FR10: Downstream planning and readiness artifacts must be revised to reflect coexistence boundaries, contract constraints, rollback implications, and migration validation gates before sprint planning resumes.

FR11: Implementation readiness must explicitly validate the next migration gates: current-runtime regression, mapping tests, export/import reconciliation, contract compatibility, and rollback approval for the relevant slice.

### NonFunctional Requirements

NFR1: Preserve the frozen v1 API contract, including endpoint paths, HTTP methods, field presence, field types, `organization_id` and `protocol_id` semantics, and the standardized error envelope.

NFR2: Keep the solution brownfield and incremental; do not authorize a big-bang rewrite or uncontrolled direct persistence replacement.

NFR3: Maintain one authoritative writer per entity per migration phase and do not introduce unrestricted dual-write.

NFR4: Keep FastAPI route handlers thin, business orchestration in services, and persistence mechanics in repositories or migration operations.

NFR5: Keep target relational naming out of current frontend components and current v1 route DTOs.

NFR6: Preserve operational recoverability and do not describe JSON snapshot restore as sufficient rollback for relational state.

NFR7: Require nearest-layer automated coverage plus route-level regression checks for every repository swap or migration-sensitive service change.

NFR8: Do not migrate measurements, checkpoints, or derived overalls into undefined relational destinations.

NFR9: Preserve metric scoring behavior for existing metrics unless an intentional versioned change is approved.

NFR10: Require explicit migration manifests, row counts, reconciliation outputs, and rollback points for each relational migration step.

### Additional Requirements

- The preferred coexistence seam is the canonical adapter layer already present in `backend/app/storage/canonical_repositories.py`.
- JSON repositories remain the authoritative runtime persistence implementation until a slice is explicitly cut over.
- Batch G remains valid in Track 1 as an admin-only ingestion flow scoped to approved JSON targets.
- The direct target relational tables currently in scope are `deva_accmed_organizations`, `deva_accmed_users`, `deva_accmed_products`, `deva_accmed_product_pillars`, `deva_accmed_product_metrics`, and `deva_accmed_enrollments`.
- `MeasurementRepository`, `CheckpointRepository`, and `MeasurementOverallRepository` stay on JSON until target relational tables are designed and approved.
- The known route/service drift around `StudentVinculoService` is treated as evidence that baseline stabilization must precede migration-sensitive work.
- Shadow-read validation must compare semantics, not only row existence.
- The following downstream artifacts must be updated or confirmed before sprint planning resumes:
  - `docs/mvp-mentoria/frontend-integration-architecture.md`
  - `docs/mvp-mentoria/backend-test-strategy.md`
  - `_bmad-output/planning-artifacts/batch-g-data-ingestion-admin-epics-and-stories.md`
  - sprint planning inputs that currently assume local feature expansion only

### UX Design Requirements

No standalone UX design document was revised for this transition. UX work remains constrained by the existing admin shell and current frontend conventions:

- keep Track 1 ingestion inside the current admin surface
- preserve Portuguese user-facing copy where the flow already exists
- avoid exposing internal persistence names, file paths, or backup locations in UI states
- keep current frontend adapters aligned to frozen v1 route semantics while backend storage evolves behind the contract boundary

### FR Coverage Map

FR1: Epic 1 - Restore the current JSON-backed runtime and regression baseline.

FR2: Epic 1 - Keep Batch G ingestion scoped to approved JSON-authoritative writes.

FR3: Epic 2 - Define and test the current-to-target domain mapping contract.

FR4: Epic 2 - Implement repository coexistence through canonical adapters and migration-aware boundaries.

FR5: Epic 3 - Introduce relational mirror repositories and controlled migration jobs only for direct-target entities.

FR6: Epic 3 - Validate parity through shadow reads on selected current-runtime surfaces.

FR7: Epic 3 - Gate cutover one entity slice at a time behind service boundaries.

FR8: Epic 1 and Epic 3 - Keep measures, checkpoints, and derived overalls on JSON until explicit target schema exists.

FR9: Epic 4 - Define split backup and rollback discipline by persistence model.

FR10: Epic 4 - Update downstream planning, test strategy, and readiness artifacts.

FR11: Epic 4 - Publish the next implementation-readiness validation gates before sprint re-entry.

## Epic List

### Epic 1: Stabilize the Current Runtime and Preserve Valid Batch G Scope
The team restores a trustworthy JSON-backed baseline, fixes current route/service drift, and keeps the existing Batch G ingestion scope operating only where it is still architecturally valid.
**FRs covered:** FR1, FR2, FR8

### Epic 2: Define the Domain Mapping and Coexistence Contract
The team formalizes the current-to-target entity mapping, locks the canonical coexistence seam, and protects frozen v1 route semantics while internal storage evolves.
**FRs covered:** FR3, FR4

### Epic 3: Build the Relational Mirror and Validate Cutover Readiness by Slice
The team adds non-authoritative relational mirrors for direct-target entities, validates parity through migration jobs and shadow reads, and gates any future cutover entity by entity.
**FRs covered:** FR5, FR6, FR7, FR8

### Epic 4: Establish Rollback Discipline and Re-Open Readiness for Planning
The team defines backup and rollback rules for both persistence models, updates downstream artifacts, and documents the exact gates that must be green before sprint planning resumes.
**FRs covered:** FR9, FR10, FR11

## Epic 1: Stabilize the Current Runtime and Preserve Valid Batch G Scope

Restore confidence in the current JSON-backed platform first. Keep Batch G within the already-approved admin ingestion boundaries while fixing the regressions and drift that currently block safe validation.

### Story 1.1: Fix Current Route and Service Wiring Defects Before Migration Work

As a platform maintainer,
I want current route and service mismatches resolved in the JSON runtime,
So that migration planning starts from a working baseline instead of a broken one.

**Acceptance Criteria:**

**Given** current admin and student routes contain stale integration assumptions
**When** the affected route and service wiring is corrected
**Then** the route layer delegates to services without dependency mismatches or ad hoc workarounds
**And** the fix preserves the current service/repository layering.

**Given** the current runtime baseline is re-tested after the fixes
**When** the relevant API suites execute
**Then** the existing admin/student flows run against JSON-backed repositories without new contract drift
**And** failures still use the standardized v1 error envelope.

### Story 1.2: Keep Batch G Ingestion JSON-Authoritative in Track 1

As an admin operator,
I want the existing Batch G ingestion flow to remain constrained to the approved JSON-backed stores,
So that valid current-scope functionality survives while migration planning proceeds separately.

**Acceptance Criteria:**

**Given** Batch G preview and apply flows run inside the current admin surface
**When** the operator submits or confirms ingestion
**Then** business writes remain limited to the approved JSON-backed targets for the current runtime
**And** relational repositories are not introduced as authoritative writers for this flow.

**Given** the legacy ingestion endpoint remains part of the frozen v1 surface during Track 1
**When** the endpoint is exercised
**Then** it preserves the current mentoring vocabulary and endpoint contract
**And** any internal orchestration changes stay behind service boundaries.

### Story 1.3: Re-Establish the Current-Runtime Regression Baseline

As a release owner,
I want the JSON-backed runtime to have a trustworthy regression baseline,
So that later migration-sensitive work can be gated against a known-good platform state.

**Acceptance Criteria:**

**Given** the current runtime stabilization work is complete
**When** the API and smoke regression suites run
**Then** the admin, mentor, student, command center, radar, matrix, and error payload guard suites are green against the JSON-backed runtime
**And** that green baseline is recorded as a prerequisite for later migration stories.

**Given** a migration-sensitive story is proposed after this baseline step
**When** readiness is reviewed
**Then** the story cannot proceed if the current-runtime regression baseline has regressed
**And** the regression failure is treated as a Track 1 blocker rather than a Track 2 shortcut.

## Epic 2: Define the Domain Mapping and Coexistence Contract

Convert the transition architecture into explicit implementation slices by defining the domain mapping, canonical adapter boundaries, and frozen-contract protections that all later migration work must respect.

### Story 2.1: Document and Test the Current-to-Target Domain Mapping Contract

As an architect,
I want an explicit mapping contract from current runtime entities to target relational entities,
So that migration jobs and repository slices use deterministic semantics instead of ad hoc renaming.

**Acceptance Criteria:**

**Given** the current runtime entities and the target relational tables are known
**When** the mapping contract is finalized
**Then** each direct-target entity class has an explicit current-to-target mapping with unresolved gaps called out
**And** measurements, checkpoints, and derived overalls remain explicitly marked as deferred.

**Given** the mapping contract is used by implementation work
**When** tests or migration utilities consume it
**Then** the expected target table shape can be derived deterministically from current data
**And** mismatches fail as explicit mapping defects rather than silent coercions.

### Story 2.2: Harden Canonical Adapters and Migration-Aware Service Boundaries

As a backend maintainer,
I want coexistence to flow through canonical adapters and migration-aware ports,
So that services can evolve internally without leaking target naming into frozen v1 APIs.

**Acceptance Criteria:**

**Given** coexistence logic is implemented for a target entity slice
**When** services need migration-aware behavior
**Then** they call canonical adapters or dedicated migration-aware ports internally
**And** route handlers continue to operate on current v1 mentoring vocabulary DTOs.

**Given** an entity slice is in a coexistence phase
**When** write ownership is defined
**Then** exactly one authoritative writer is documented for that entity in that phase
**And** unrestricted dual-write is not introduced.

### Story 2.3: Preserve the Frozen v1 Contract and Frontend Adapter Insulation

As a frontend and API owner,
I want storage evolution to remain invisible at the v1 contract boundary,
So that route consumers do not break while the backend prepares relational cutover.

**Acceptance Criteria:**

**Given** a migration-sensitive backend change affects an existing route family
**When** the route is exercised through API tests or adapters
**Then** endpoint paths, methods, field presence, field types, and `organization_id` or `protocol_id` semantics remain unchanged
**And** target names such as `product_id`, `provider_user_id`, or `client_user_id` do not leak into v1 payloads.

**Given** frontend adapter code consumes these routes
**When** the backend internal storage source changes behind the route
**Then** the adapter-level contract remains stable for current frontend features
**And** migration-specific normalization logic stays out of React components.

### Story 2.4: Preserve Metric DSL Semantics at the Migration Boundary

As a platform maintainer,
I want metric DSL evolution isolated behind scoring and repository boundaries,
So that persistence migration does not accidentally rewrite current scoring behavior.

**Acceptance Criteria:**

**Given** existing metrics are exported, mirrored, or rehydrated during transition work
**When** metric configuration passes through the current and future persistence paths
**Then** existing score semantics remain equivalent unless an explicit versioned change is approved
**And** descriptive labels are not promoted into canonical logical keys.

**Given** a migration step touches scoring metadata or serialization
**When** validation runs
**Then** scoring behavior is verified through metric-level tests and representative runtime flows
**And** the migration is rejected if it changes current score behavior unintentionally.

## Epic 3: Build the Relational Mirror and Validate Cutover Readiness by Slice

Introduce relational persistence only where the target schema is already defined, keep it non-authoritative until validated, and use migration jobs and shadow reads to prove parity before any cutover is considered.

### Story 3.1: Add Relational Mirror Repositories for Direct-Target Entities Only

As a backend maintainer,
I want relational repositories introduced only for entity classes that already have target tables,
So that the migration mirror reflects the approved schema without inventing destinations for unresolved data.

**Acceptance Criteria:**

**Given** the target relational schema currently covers organizations, users, products, product pillars, product metrics, and enrollments
**When** relational repositories are added
**Then** only those entity classes receive relational repository implementations
**And** measurements, checkpoints, and measurement overalls do not receive relational repositories yet.

**Given** those repositories are introduced during coexistence
**When** application code uses them
**Then** they remain hidden behind service or migration boundaries
**And** they are not treated as runtime-authoritative writers until validation gates pass.

### Story 3.2: Build Controlled Export, Import, and Reconciliation Jobs

As a migration operator,
I want repeatable export/import jobs with reconciliation evidence,
So that relational mirrors are populated through controlled operations rather than ad hoc scripts.

**Acceptance Criteria:**

**Given** JSON remains authoritative in the current runtime
**When** migration jobs populate the relational mirror
**Then** export, import, and reconciliation operations produce manifests with row counts, target slice identifiers, and outcome evidence
**And** the jobs do not become part of request-time route handling.

**Given** a migration job reports success
**When** the evidence is reviewed
**Then** the reconciliation output proves semantic alignment between exported JSON/canonical records and inserted relational rows
**And** missing or divergent records are surfaced explicitly for correction.

### Story 3.3: Validate Shadow-Read Parity on Selected Current-Runtime Surfaces

As an architect,
I want shadow-read parity checks on selected admin/runtime surfaces,
So that the team can validate relational readiness before any slice is cut over.

**Acceptance Criteria:**

**Given** a relational mirror is populated for an approved entity slice
**When** selected admin or current-runtime surfaces are evaluated in shadow-read mode
**Then** relational/canonical outputs are compared against current JSON-backed responses for semantic parity
**And** parity review covers meaning and contract behavior, not only raw record presence.

**Given** parity defects are found during shadow validation
**When** the findings are triaged
**Then** the slice remains on JSON authority
**And** the defects are corrected in mapping, migration, or service boundaries before cutover is reconsidered.

### Story 3.4: Gate Controlled Cutover Per Entity Slice and Defer Unresolved Domains

As a platform owner,
I want cutover to happen only for validated slices with defined destinations,
So that unresolved entity classes do not get forced into the wrong relational shape.

**Acceptance Criteria:**

**Given** an entity slice has passed mapping, migration, and shadow-read validation
**When** a cutover decision is made
**Then** the slice is switched behind service and repository boundaries without changing the external v1 DTOs
**And** a rollback point is defined before the cutover executes.

**Given** the target relational schema does not yet include measures, checkpoints, or derived overalls
**When** implementation planning reaches those domains
**Then** they remain on JSON-backed persistence
**And** no story may force them into unrelated relational tables as a shortcut.

## Epic 4: Establish Rollback Discipline and Re-Open Readiness for Planning

Define the operational safeguards and artifact updates that must exist before sprint planning resumes, so the team can move from architecture approval into implementation with explicit gates instead of assumptions.

### Story 4.1: Define the Split Backup and Rollback Operating Model

As an operations owner,
I want a persistence-specific rollback model for JSON and relational phases,
So that recovery expectations remain accurate while both models coexist.

**Acceptance Criteria:**

**Given** Track 1 continues on JSON-backed persistence
**When** JSON-authoritative flows execute writes
**Then** they continue using `storage_maintenance.py` snapshot and restore semantics
**And** those semantics are documented as JSON-only recovery behavior.

**Given** a relational migration or cutover slice is planned
**When** rollback expectations are defined
**Then** the slice has its own restore point, migration manifest, and reconciliation evidence
**And** JSON snapshot restore is not described as sufficient rollback for relational state.

### Story 4.2: Update Downstream Docs and Test Strategy for Coexistence

As a planning owner,
I want downstream architecture, integration, and test artifacts updated for coexistence,
So that readiness review and future implementation work use the same transition assumptions.

**Acceptance Criteria:**

**Given** the transition architecture is approved
**When** downstream artifacts are revised
**Then** frontend integration guidance covers semantic drift behind stable v1 DTOs, backend test strategy adds mapping and rollback gates, and sprint inputs stop assuming direct persistence replacement
**And** the revised artifacts distinguish Track 1 stabilization from Track 2 migration planning.

**Given** a future implementation story depends on those artifacts
**When** the story is reviewed
**Then** it references the updated coexistence boundaries and readiness gates
**And** it is rejected if it still assumes feature-only expansion on the old single-persistence model.

### Story 4.3: Publish the Next Implementation-Readiness Validation Gate

As a scrum and architecture lead,
I want the exact next validations listed before sprint re-entry,
So that the team knows what must be green before implementation planning resumes.

**Acceptance Criteria:**

**Given** the revised epics and stories are accepted
**When** implementation readiness is prepared
**Then** the next required validations are explicitly recorded as:
**And** current JSON-backed API regression is green.
**And** entity mapping rules are documented and testable.
**And** canonical export/import reconciliation evidence exists for the direct-target relational entities.
**And** the backup and rollback procedure is approved for the persistence slice under review.
**And** contract-compatibility checks and selected shadow-read parity checks are complete.

**Given** one or more of those validations is still missing
**When** sprint planning is proposed
**Then** sprint planning does not resume for migration-sensitive implementation
**And** the missing gate is treated as the next planning blocker to resolve.

## Implementation Readiness - Next Validation Targets

The next implementation-readiness review must explicitly validate the following before sprint planning and migration-sensitive development resume:

1. The current JSON-backed API regression baseline is green again.
2. The current-to-target entity mapping contract is documented and backed by tests.
3. Canonical export, import, and reconciliation evidence exists for organizations, users, products, product pillars, product metrics, and enrollments.
4. The rollback procedure for the next persistence slice is approved and differentiates JSON recovery from relational recovery.
5. Frozen v1 contract compatibility has been re-verified for the affected route families.
6. Shadow-read parity has been reviewed for the selected current-runtime surfaces before any cutover is approved.
