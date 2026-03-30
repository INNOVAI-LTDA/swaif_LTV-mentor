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

FR10: Admin/support users must be able to retrieve a structured ingestion execution report by `execution_id`.

FR11: The system must support the documented operator-assisted rollback path and record rollback outcome linked to the execution log.

FR12: The feature must ship with nearest-layer automated coverage and operational documentation for preview, apply, audit, backup, and rollback-sensitive behavior.

### NonFunctional Requirements

NFR1: Preserve the existing role-based admin boundary in frontend and backend (`RequireAdmin` and `require_admin_user`) and do not depend on a literal admin email.

NFR2: Keep FastAPI route handlers thin and place orchestration in `backend/app/services` and persistence in `backend/app/storage`.

NFR3: Preserve the standardized API error envelope `{ error: { status, code, message, details } }` for request-level failures.

NFR4: Keep the solution brownfield and incremental by extending the existing student indicator-load flow rather than creating a generic ingestion subsystem.

NFR5: Keep writes constrained to `measurements`, `checkpoints`, and `ingestion_executions`; do not widen scope to other JSON stores.

NFR6: Preserve frontend service/adapter boundaries, TypeScript strict mode, `AppError`, centralized env access, and existing admin shell/page patterns.

NFR7: Do not expose filesystem paths, snapshot directories, or server storage details in the UI.

NFR8: Keep raw API payload handling and alias normalization out of React components.

NFR9: Preserve Portuguese user-facing copy and established loading, error, empty, and success state conventions.

NFR10: Reuse the existing snapshot and restore tooling instead of introducing parallel backup logic.

NFR11: Add or extend nearest-layer backend and frontend tests for all new behavior touched by the feature.

NFR12: Preserve frozen v1 contract compatibility by keeping the existing `/admin/alunos/{student_id}/indicadores/carga-inicial` path available as a compatibility bridge during migration.

### Additional Requirements

- No new starter template or parallel architecture is allowed; this is a brownfield extension of the current React + FastAPI + JSON repository stack.
- Batch G is intentionally narrow: one selected student enrollment at a time inside the existing admin surface.
- The approved business write targets are `measurements` and `checkpoints`; the approved operational write target is `ingestion_executions`.
- The active MVP source mode is `manual_assisted`; `json_file` is reserved for future expansion and should not drive Batch G scope.
- The recommended frontend entry is a dedicated admin panel keyed by `panel=ingestao-dados` inside the existing `AdminPage` and `AdminShell`.
- The recommended backend endpoints are `POST /admin/alunos/{student_id}/indicadores/carga-inicial/preview`, `POST /admin/alunos/{student_id}/indicadores/carga-inicial/apply`, and `GET /admin/ingestoes/{execution_id}`.
- The legacy `POST /admin/alunos/{student_id}/indicadores/carga-inicial` endpoint should remain available and delegate to the new apply orchestration during migration.
- Preview writes only the execution log and never business stores.
- Apply must consume `preview_execution_id` rather than trusting a second ad hoc payload.
- Apply must create a backup through `storage_maintenance.create_backup_snapshot(...)` before changing business stores and attempt restore on post-snapshot failure.
- Rollback in MVP is operator-assisted, not a primary frontend action.
- Existing indicator-load API, service, and admin modal tests are the seed regression surface and should be extended rather than replaced.

### UX Design Requirements

No standalone UX specification was provided for this scope. UX work is constrained by the approved architecture and current admin patterns: keep the flow in the existing admin surface, preserve Portuguese operational copy, use preview-before-apply states, and avoid exposing sensitive technical details.

### FR Coverage Map

FR1: Epic 1 - Add the admin-only `Ingestao de Dados` panel inside the existing admin surface.

FR2: Epic 1 - Reuse selected-student context and capture source metadata for manual-assisted ingestion.

FR3: Epic 1 - Provide a backend preview flow that performs validation without business persistence.

FR4: Epic 1 - Validate selected-student ingestion payloads and replacement impact before apply.

FR5: Epic 1 - Return a structured preview report with execution ID, summary counts, conflicts, and rejections.

FR6: Epic 2 - Require explicit confirmation and a valid preview execution before apply.

FR7: Epic 2 - Revalidate, snapshot, and write only to the approved stores.

FR8: Epic 2 - Preserve `replace_enrollment` semantics for measurements and checkpoints.

FR9: Epic 2 - Persist execution audit records for preview and apply outcomes.

FR10: Epic 3 - Retrieve structured execution details by execution identifier.

FR11: Epic 3 - Support the documented operator-assisted rollback path and record rollback outcomes.

FR12: Epic 3 - Deliver regression coverage and operational documentation for stabilization.

## Epic List

### Epic 1: Admin Preview Workflow for Indicator Ingestion
Admin operators can open a dedicated ingestion flow for a selected student, submit a manual-assisted preview, and review validated impact before any write is possible.
**FRs covered:** FR1, FR2, FR3, FR4, FR5

### Epic 2: Controlled Apply with Backup and Audit
Admin operators can confirm a validated preview and apply it safely with snapshot protection, constrained writes, compatibility preservation, and durable execution evidence.
**FRs covered:** FR6, FR7, FR8, FR9

### Epic 3: Execution Follow-Up and Stabilization Readiness
Admin and support operators can inspect execution outcomes, follow the rollback procedure, and rely on documentation and tests that keep the feature safe during final stabilization.
**FRs covered:** FR10, FR11, FR12

## Epic 1: Admin Preview Workflow for Indicator Ingestion

Enable admins to start the Batch G ingestion flow from the existing admin area, use the selected-student context, and obtain a backend-validated preview before any business write can occur.

### Story 1.1: Expose the `Ingestao de Dados` Admin Panel (FR1)

As an admin operator,
I want to open `Ingestao de Dados` from the existing admin area,
So that I can start the ingestion workflow without leaving the established admin boundary.

**Acceptance Criteria:**

**Given** an authenticated admin user is on `/app/admin`
**When** the admin views the available admin operations
**Then** the UI exposes an `Ingestao de Dados` entry inside the existing `AdminShell` and `AdminPage`
**And** the entry is implemented as a panel selection within the current admin surface rather than a new top-level route family.

**Given** a non-admin user or unauthenticated visitor
**When** that user attempts to access the ingestion panel
**Then** the existing frontend and backend admin guards continue to block access
**And** no ingestion-specific access rule depends on `admin@swaif.local`.

### Story 1.2: Bind the Panel to Selected-Student Context and Source Metadata (FR2)

As an admin operator,
I want the ingestion panel to reuse the selected-student context and record source metadata,
So that preview operates on the intended enrollment with traceable origin information.

**Acceptance Criteria:**

**Given** the admin has selected a student within the current admin workflow
**When** the `Ingestao de Dados` panel is opened
**Then** the panel receives the selected student context needed for preview and apply
**And** it does not ask the operator to navigate to a separate route or reselect the same hierarchy outside existing admin patterns.

**Given** the admin prepares a preview request
**When** source metadata is collected
**Then** the request includes `source_type` and `source_label`
**And** Batch G activates `manual_assisted` as the allowed source mode while leaving `json_file` reserved for future scope.

### Story 1.3: Add the Preview Contract, Route, and Frontend Service Boundary (FR3)

As an admin operator,
I want a dedicated preview API and frontend service flow,
So that the system can validate ingestion input without mixing transport logic into page JSX.

**Acceptance Criteria:**

**Given** a selected student and a preview request payload
**When** the frontend submits the request
**Then** the call flows through a dedicated admin data ingestion service and contract boundary
**And** React components do not contain direct fetch logic, env access, or contract normalization.

**Given** the backend receives the preview request
**When** it reaches the admin route layer
**Then** a thin route in the existing admin student namespace validates the wrapper schema and delegates orchestration to a service
**And** malformed requests continue to use the standardized API error envelope.

### Story 1.4: Validate Preview Input and Produce Structured Diagnostics (FR3, FR4, FR5)

As an admin operator,
I want the backend to validate the full preview input and explain its impact,
So that I can detect data issues before confirming apply.

**Acceptance Criteria:**

**Given** a preview request for a selected student
**When** the ingestion service validates the request
**Then** it verifies student existence, active enrollment, active metrics, product-context compatibility, checkpoint field validity, and replacement impact counts
**And** it does so without persisting `measurements` or `checkpoints`.

**Given** the preview completes
**When** the backend returns the result
**Then** the response includes `execution_id`, student and enrollment identifiers, preview status, summary counts, conflicts, rejections, and `affected_stores`
**And** `affected_stores` is limited to approved logical store names instead of filesystem paths.

### Story 1.5: Render the Preview Report and Explicit Apply Gate (FR4, FR5)

As an admin operator,
I want to review preview findings before apply becomes available,
So that confirmation is based on backend-validated impact instead of local assumptions.

**Acceptance Criteria:**

**Given** a preview response is available
**When** the admin reviews the ingestion panel
**Then** the UI shows Portuguese copy for summary counts, conflicts, rejections, and affected stores using existing request-state conventions
**And** it does not expose raw server paths, snapshot directories, or internal repository names.

**Given** the preview has not been executed or contains blocking issues
**When** the admin attempts to proceed to apply
**Then** the confirm action remains unavailable or blocked with a controlled explanation
**And** apply is only enabled from a reviewed preview state tied to a preview execution.

## Epic 2: Controlled Apply with Backup and Audit

Allow admins to confirm a valid preview and apply it safely by reusing the current replace semantics, backup tooling, and execution logging boundaries.

### Story 2.1: Enforce Apply Preconditions from Preview Execution (FR6)

As an admin operator,
I want apply to require explicit confirmation and a valid preview execution,
So that writes cannot occur from stale or unreviewed input.

**Acceptance Criteria:**

**Given** an admin attempts to apply ingestion
**When** the backend receives the request
**Then** the request must include `preview_execution_id` and explicit confirmation
**And** the service rejects apply when the preview execution does not exist, is not `previewed`, or does not belong to the same student context.

**Given** a preview execution has already been consumed or invalidated
**When** apply is attempted again
**Then** the system returns a controlled conflict response through the standard error envelope
**And** no business write is performed.

### Story 2.2: Snapshot, Revalidate, and Apply Only Approved Writes (FR7, FR8)

As an admin operator,
I want the confirmed apply flow to rerun validation and snapshot before writing,
So that the system can fail safely while preserving approved persistence semantics.

**Acceptance Criteria:**

**Given** a valid apply request linked to a preview execution
**When** the service enters the apply flow
**Then** it reruns the same validation pipeline used by preview before any write occurs
**And** it creates a backup snapshot through `storage_maintenance.create_backup_snapshot(...)` before changing business stores.

**Given** the apply validation passes
**When** the service persists data
**Then** it writes only to `measurements` and `checkpoints`
**And** it preserves the existing `replace_for_enrollment(...)` / `replace_enrollment` behavior for the selected enrollment.

### Story 2.3: Persist Execution Audit and Failure-Recovery Outcomes (FR7, FR9)

As an operator responsible for supportability,
I want preview and apply executions recorded with backup and rollback evidence,
So that operational history survives the ingestion lifecycle.

**Acceptance Criteria:**

**Given** a preview or apply execution is processed
**When** the ingestion service persists execution metadata
**Then** the system records operator identity, timestamps, source metadata, summary counts, affected stores, status, and backup reference in the dedicated `ingestion_executions` store
**And** preview persists only execution evidence rather than business writes.

**Given** a failure occurs after snapshot creation
**When** the service handles the failure
**Then** it attempts restore through the existing backup utilities and records `rolled_back` or `rollback_failed` outcome in the execution log
**And** the recovery attempt does not invent a new error response shape.

### Story 2.4: Return the Final Apply Result and Preserve Legacy Endpoint Compatibility (FR8, FR9)

As an admin operator,
I want the final apply result and compatibility behavior to remain predictable,
So that the new orchestration can ship without breaking existing consumers.

**Acceptance Criteria:**

**Given** an apply execution completes successfully
**When** the backend returns the response
**Then** the result includes `execution_id`, `preview_execution_id`, mode, status, affected stores, counts, and a safe `backup_ref`
**And** the payload excludes internal snapshot paths.

**Given** the existing `POST /admin/alunos/{student_id}/indicadores/carga-inicial` endpoint is still in use during migration
**When** it is invoked
**Then** the endpoint remains available as a compatibility bridge to the new apply orchestration
**And** it preserves frozen-contract expectations until the frontend is fully moved.

### Story 2.5: Complete the Apply UX in the Admin Panel (FR6, FR9)

As an admin operator,
I want the admin panel to execute apply and render the final outcome cleanly,
So that I can complete the ingestion flow without leaving the established operational context.

**Acceptance Criteria:**

**Given** a reviewed preview is ready for confirmation
**When** the admin confirms apply
**Then** the frontend calls the apply service using the preview execution reference and existing `AppError` handling
**And** loading, success, and error states follow the current admin conventions.

**Given** the final apply response is received
**When** the completion state is rendered
**Then** the UI shows execution identifier, final status, summary counts, and safe backup reference details in Portuguese copy
**And** it continues to avoid raw transport payload binding in React components.

## Epic 3: Execution Follow-Up and Stabilization Readiness

Enable the operational follow-up needed after apply by exposing execution detail, documenting rollback handling, and locking the feature down with the nearest regression coverage.

### Story 3.1: Retrieve Structured Execution Details by Identifier (FR10)

As an admin or support operator,
I want to fetch an ingestion execution by `execution_id`,
So that I can inspect what happened after preview or apply.

**Acceptance Criteria:**

**Given** a valid recorded execution identifier
**When** an authenticated admin requests execution detail
**Then** the backend returns the stored structured execution report with source metadata, status, counts, affected stores, backup reference, and rollback fields
**And** missing execution identifiers continue to use the standardized API error envelope.

**Given** the frontend holds a completed preview or apply result
**When** the operator requests more detail for that execution
**Then** the UI can render the execution evidence using the established service/adapter pattern
**And** the response remains safe for UI display without exposing internal paths.

### Story 3.2: Document and Record the Operator-Assisted Rollback Path (FR11)

As an operations owner,
I want a documented rollback procedure linked to execution records,
So that recovery can be performed safely without inventing an unsafe self-service UI.

**Acceptance Criteria:**

**Given** an applied execution with a recorded backup reference
**When** an operator follows the rollback procedure
**Then** the documented path uses `execution_id`, the internal snapshot reference, and the existing restore command/tooling
**And** rollback remains operator-assisted rather than a primary frontend button in Batch G.

**Given** a rollback attempt succeeds or fails
**When** the outcome is recorded
**Then** the execution log stores rollback status and follow-up evidence
**And** operational documentation explains how to verify the restored state afterward.

### Story 3.3: Add Stabilization-Focused Automated Coverage (FR12)

As a release owner,
I want automated coverage at the nearest relevant layers,
So that the Batch G ingestion flow can be stabilized without regressions.

**Acceptance Criteria:**

**Given** the Batch G implementation is added
**When** automated tests run
**Then** backend API tests cover preview/apply permissions, error envelope behavior, and execution detail responses
**And** backend service or integration tests cover validation, snapshot-before-write, apply success, and restore-on-failure behavior.

**Given** the frontend panel flow is implemented
**When** frontend tests run
**Then** they cover admin-only access, preview rendering, apply confirmation, and final outcome states
**And** they extend the existing admin indicator-load baseline instead of replacing it with unrelated abstractions.

### Story 3.4: Publish the Batch G Operations Runbook (FR12)

As a release owner,
I want an explicit operations runbook for Batch G ingestion,
So that preview, apply, execution lookup, and rollback can be used consistently in local and staging environments.

**Acceptance Criteria:**

**Given** the feature is ready for final stabilization
**When** the supporting documentation is published
**Then** the repository includes a runbook that documents preview, apply, execution lookup, backup expectations, rollback procedure, and local/staging-first usage constraints
**And** the document references execution IDs and safe backup tokens instead of raw server paths.

**Given** future agents or operators use the artifact set
**When** they trace the implementation scope
**Then** the runbook remains aligned with the approved write targets, the Batch G architecture, and the existing deployment-readiness conventions
**And** it does not describe broader generic ingestion capabilities as if they already exist.
