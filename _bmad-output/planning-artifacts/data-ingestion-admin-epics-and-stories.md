---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - C:\Users\dmene\Projetos\innovai\repos\swaif_LTV-mentoria\_bmad-output\planning-artifacts\data-ingestion-admin-architecture.md
  - C:\Users\dmene\Projetos\innovai\repos\swaif_LTV-mentoria\_bmad-output\project-context.md
  - C:\Users\dmene\Projetos\innovai\repos\swaif_LTV-mentoria\docs\mvp-mentoria\batch-g-data-ingestion-admin-current-state.md
  - C:\Users\dmene\Projetos\innovai\repos\swaif_LTV-mentoria\docs\discovery\data-ingestion-admin-brief.md
workflowType: epics-and-stories
project_name: swaif_LTV-mentoria
user_name: dmene
date: 2026-03-30
lastStep: 4
status: complete
completedAt: 2026-03-30
scope: data-ingestion-admin
---

# swaif_LTV-mentoria - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for `data-ingestion-admin`, decomposing the brief, brownfield current state, and approved architecture into implementable stories that stay inside the MVP boundary for indicator batch ingestion.

## Requirements Inventory

### Functional Requirements

FR1: Admin users must be able to access an `Ingestao de Dados` operation from the existing admin area without creating a parallel auth path.

FR2: The admin workflow must accept an approved structured JSON source with source metadata for ingestion.

FR3: The backend must support a `dry_run` / preview mode that performs full validation without persisting domain writes.

FR4: The preview result must report validation diagnostics, including received, valid, rejected, and conflicting loads plus affected students, enrollments, and stores.

FR5: The admin must explicitly confirm apply only after reviewing the preview result in the admin workflow.

FR6: The apply flow must revalidate the batch and create a backup snapshot before any domain write occurs.

FR7: The MVP apply flow must write only to the approved indicator targets and preserve replace-per-enrollment semantics for measurements and checkpoints.

FR8: The apply flow must remain all-or-nothing for blocking validation failures and return structured diagnostics instead of partial silent writes.

FR9: The system must persist a minimal execution audit trail with operator, timestamps, source metadata, payload hash, counts, affected targets, and backup references.

FR10: Operators must be able to retrieve a structured execution report by `execution_id`.

FR11: Operators must be able to execute a rollback from a recorded backup reference and persist rollback evidence.

FR12: The final apply response must include execution status, execution identifier, summary counts, issues, affected targets, and a safe backup reference token.

### NonFunctional Requirements

NFR1: Preserve the existing role-based admin boundary in frontend and backend (`RequireAdmin` and `require_admin_user`).

NFR2: Keep FastAPI route handlers thin and place orchestration in services and repositories.

NFR3: Preserve the standardized API error envelope `{ error: { status, code, message, details } }` for request-level failures.

NFR4: Do not expose filesystem paths, snapshot directories, or repository-internal paths in the UI.

NFR5: Keep raw ingestion payloads as `unknown` at the frontend boundary and keep normalization out of React components.

NFR6: Preserve TypeScript strict-mode, `AppError`, centralized env access, and established admin shell/page patterns.

NFR7: Keep the change brownfield and incremental by reusing the existing indicator-load flow as the seed pattern.

NFR8: Constrain writes to explicitly approved JSON targets and do not introduce a generic write-any-JSON endpoint.

NFR9: Reuse the existing snapshot and restore tooling, while keeping the audit store outside the registered snapshot set.

NFR10: Add or extend nearest-layer coverage for admin UI, API, service, and repository behavior touched by the feature.

NFR11: Provide operational documentation that supports local/staging-first rollout and controlled production validation later.

NFR12: Preserve Portuguese user-facing copy and safe operational UX conventions already used in the admin area.

### Additional Requirements

- No starter template or parallel scaffold is allowed; this is a brownfield extension of the existing React + FastAPI + JSON repository stack.
- The MVP scope is intentionally narrow: only student indicator initial-load batches are in scope.
- Approved write targets are `measurements.json` and `checkpoints.json`; the audit trail is stored separately in `ingestion_executions.json`.
- Approved read-only validation targets are `students.json`, `enrollments.json`, `organizations.json`, `protocols.json`, `pillars.json`, and `metrics.json`.
- The official MVP source type is `uploaded_json`.
- The frontend may parse the uploaded file for transport purposes, but the payload remains `unknown` until backend schema normalization.
- Backend API coverage for this capability includes preview, apply, execution detail, and rollback endpoints under the admin area.
- Validation rules must include supported `schema_version`, batch kind, uniqueness of `student_id`, `metric_id`, and `week`, active enrollment checks, product ownership checks, allowed checkpoint statuses, and numeric field validation.
- Apply must reuse the existing backup utilities for snapshot, verification, and restore rather than introducing parallel backup logic.
- The audit repository must remain outside the registered snapshot set so rollback does not erase operational evidence.
- The UI must show only safe operational data: file name, summary counts, issues, affected targets, execution id, and backup reference token.
- Existing `replace_for_enrollment(...)` semantics remain the persistence rule for measurements and checkpoints in the MVP.
- Existing admin indicator-load tests are the seed coverage surface and should be extended rather than replaced.
- A dedicated operational runbook is required for preview, apply, and rollback usage.

### UX Design Requirements

No standalone UX design document was provided for this scope. UX requirements are constrained by the brief and architecture: keep the interaction inside the existing admin surface, use a confirmation-after-review flow, preserve Portuguese operational copy, and avoid exposing sensitive technical details.

### FR Coverage Map

FR1: Epic 1 - Expose the admin-only `Ingestao de Dados` entry inside the existing admin surface.

FR2: Epic 1 - Accept a structured uploaded JSON source with source metadata.

FR3: Epic 1 - Provide a server-side preview flow that does not persist domain data.

FR4: Epic 1 - Return validation counts, issues, conflicts, and affected targets in the preview report.

FR5: Epic 1 - Gate apply behind an explicit review and confirmation step.

FR6: Epic 2 - Revalidate and snapshot before any apply write.

FR7: Epic 2 - Restrict writes to approved indicator targets using replace-per-enrollment semantics.

FR8: Epic 2 - Enforce all-or-nothing apply behavior with structured diagnostics.

FR9: Epic 2 - Persist execution audit evidence separately from domain snapshots.

FR10: Epic 3 - Retrieve structured execution details by execution identifier.

FR11: Epic 3 - Restore from the recorded snapshot and record rollback evidence.

FR12: Epic 2 - Return a final structured execution result with safe backup reference data.

## Epic List

### Epic 1: Safe Admin Preview for Batch Intake
Admin operators can enter a dedicated ingestion workflow, upload an approved batch, and obtain a backend-validated preview before any write occurs.
**FRs covered:** FR1, FR2, FR3, FR4, FR5

### Epic 2: Controlled Apply with Backup and Audit
Admin operators can confirm a validated batch and apply it safely with snapshot protection, constrained writes, and durable execution evidence.
**FRs covered:** FR6, FR7, FR8, FR9, FR12

### Epic 3: Execution Recovery and Operational Readiness
Admin and support operators can inspect completed executions, execute rollback when needed, and operate the feature with documented safeguards and regression coverage.
**FRs covered:** FR10, FR11

## Epic 1: Safe Admin Preview for Batch Intake

Enable admins to start the ingestion workflow from the existing admin area, submit an approved batch file, and receive a backend-validated preview before any write is possible.

### Story 1.1: Expose the Admin Ingestao de Dados Entry (FR1)

As an admin operator,
I want to open `Ingestao de Dados` from the existing admin area,
So that I can start a controlled ingestion flow without leaving the established admin boundary.

**Acceptance Criteria:**

**Given** an authenticated admin user is on `/app/admin`
**When** the admin views the available operations
**Then** the UI shows an `Ingestao de Dados` entry within the existing admin surface
**And** the entry reuses the current admin shell and role-based access model instead of introducing a parallel route family.

**Given** a non-admin authenticated user or unauthenticated visitor
**When** that user attempts to access the ingestion operation
**Then** the frontend and backend continue to enforce the existing admin guard behavior
**And** no ingestion-specific access rule depends on a literal admin email.

### Story 1.2: Upload an Approved Batch File for Preview (FR2)

As an admin operator,
I want to select a structured JSON file and source metadata for preview,
So that the backend can validate a known ingestion source safely.

**Acceptance Criteria:**

**Given** the admin opens the ingestion workflow
**When** the admin selects a JSON file and optional source label
**Then** the UI displays the chosen file name and keeps the parsed payload at the transport boundary until submission
**And** no React component embeds normalization or contract-migration logic for the file contents.

**Given** the selected file cannot be parsed as valid JSON
**When** the admin attempts to continue to preview
**Then** the UI blocks the request with a controlled error message
**And** request and parsing failures continue to flow through the existing `AppError` handling conventions.

### Story 1.3: Add the Admin Preview Contract and Route (FR2, FR3)

As an admin operator,
I want a dedicated preview API for ingestion batches,
So that the system can validate incoming data without writing domain state.

**Acceptance Criteria:**

**Given** an authenticated admin submits a preview request with source metadata and `raw_payload`
**When** the request reaches the backend
**Then** a thin admin ingestion route validates the wrapper contract and delegates orchestration to a dedicated service
**And** malformed requests still use the standard API error envelope.

**Given** the request is a valid preview request
**When** the backend processes it
**Then** the service executes the preview path without persisting measurements or checkpoints
**And** the response shape is structured for preview reporting rather than ad hoc route-specific output.

### Story 1.4: Implement Batch Normalization and Preview Diagnostics (FR3, FR4)

As an admin operator,
I want the system to validate the full batch and explain what would happen,
So that I can detect data issues before confirming apply.

**Acceptance Criteria:**

**Given** a preview request with supported schema version and batch kind
**When** the service normalizes and validates the batch
**Then** it enforces uniqueness rules for `student_id`, `metric_id`, and `week`
**And** it validates active student, enrollment, metric, and product ownership constraints defined by the architecture.

**Given** the preview completes
**When** the response is returned
**Then** the result includes received, valid, rejected, and conflicting counts plus affected students, enrollments, and stores
**And** each rejected or conflicting load includes a diagnostic that can be rendered in the admin UI.

### Story 1.5: Render the Preview Report and Explicit Apply Gate (FR4, FR5)

As an admin operator,
I want to review preview findings before apply is enabled,
So that confirmation is based on validated backend impact rather than local form assumptions.

**Acceptance Criteria:**

**Given** a preview response is available
**When** the admin reviews the report
**Then** the UI shows counts, issues, conflicts, affected targets, and safe source details using Portuguese operational copy
**And** it does not display filesystem paths, snapshot directories, or repository-internal file names.

**Given** the preview contains blocking issues or has not been run yet
**When** the admin attempts to apply
**Then** the confirm action remains unavailable or blocked with a controlled explanation
**And** explicit confirmation is only possible from a reviewed preview state.

## Epic 2: Controlled Apply with Backup and Audit

Allow admins to apply a validated batch safely by reusing current backup and persistence patterns, while producing durable execution evidence and a final structured report.

### Story 2.1: Persist Ingestion Execution Audit Records (FR9)

As an operator responsible for supportability,
I want every preview and apply execution recorded in a dedicated audit store,
So that operational evidence survives snapshot restore activity.

**Acceptance Criteria:**

**Given** a preview or apply execution is started
**When** the ingestion service records execution metadata
**Then** the system persists an audit record with operator identity, timestamps, source metadata, payload hash, summary counts, affected targets, and status
**And** the repository is separate from the registered domain snapshot set.

**Given** a rollback or failed apply occurs
**When** the audit record is updated
**Then** the execution history preserves the original execution evidence and the recovery outcome
**And** no rollback erases prior audit records.

### Story 2.2: Revalidate and Snapshot Before Apply (FR6, FR8)

As an admin operator,
I want apply to rerun validation and create a backup snapshot before any write,
So that the system can fail safely and avoid stale preview assumptions.

**Acceptance Criteria:**

**Given** an admin confirms apply for a previously previewed batch
**When** the backend receives the apply request
**Then** the service reruns the same validation pipeline used by preview before any persistence occurs
**And** apply stops with structured diagnostics if blocking validation errors remain.

**Given** the batch passes apply-time validation
**When** the service begins the write path
**Then** it creates a backup snapshot through the existing storage maintenance utilities before changing domain stores
**And** unrecoverable transport-level or apply-level failures still surface through the standard API error envelope.

### Story 2.3: Apply the Batch Only to Approved Indicator Targets (FR7, FR8)

As an admin operator,
I want the confirmed batch applied only to the approved indicator stores,
So that the MVP stays within the explicit write boundary and preserves current replacement semantics.

**Acceptance Criteria:**

**Given** a valid apply request
**When** the service writes batch results
**Then** it updates only `measurements` and `checkpoints` for the resolved active enrollments
**And** the persistence path preserves existing `replace_for_enrollment(...)` semantics.

**Given** a failure occurs after snapshot creation but before a successful apply completes
**When** the service handles the failure
**Then** it treats the execution as all-or-nothing and attempts restore using the recorded snapshot
**And** it does not leave silent partial writes across enrollments.

### Story 2.4: Return and Render the Final Apply Report (FR12)

As an admin operator,
I want a final structured apply report after confirmation,
So that I have execution evidence for operations and support follow-up.

**Acceptance Criteria:**

**Given** an apply execution completes
**When** the backend returns the final result
**Then** the response includes execution id, mode, status, summary counts, issues, affected targets, and a safe backup reference token
**And** the payload avoids exposing internal snapshot paths.

**Given** the frontend receives the final result
**When** it renders completion state
**Then** the admin sees the execution identifier and outcome details in the ingestion workflow
**And** the UI uses the established request-state conventions for loading, error, and success handling.

## Epic 3: Execution Recovery and Operational Readiness

Enable the operational follow-up needed after apply by adding execution lookup, rollback support, and the minimum documentation and regression coverage needed for safe stabilization.

### Story 3.1: Retrieve Execution Details by Identifier (FR10)

As an admin or support operator,
I want to fetch an execution report by `execution_id`,
So that I can investigate what happened after preview or apply.

**Acceptance Criteria:**

**Given** a valid execution identifier for a recorded ingestion run
**When** an authenticated admin requests execution details
**Then** the backend returns the stored structured execution report with source metadata, summary counts, affected targets, status, and safe backup reference information
**And** missing execution identifiers continue to use the standardized API error envelope.

**Given** the frontend has a completed apply or preview state
**When** the operator requests more detail for that execution
**Then** the UI can render the execution evidence without requiring raw filesystem details
**And** the detail contract remains consistent with the apply report shape.

### Story 3.2: Roll Back an Applied Execution from the Recorded Snapshot (FR11)

As an admin or support operator,
I want to restore the pre-apply snapshot for a selected execution,
So that I can recover safely from a bad ingestion.

**Acceptance Criteria:**

**Given** an applied execution with a recorded backup reference
**When** an authenticated admin invokes rollback
**Then** the backend verifies the snapshot and restores through the existing storage maintenance utilities
**And** the rollback path remains inside backend service boundaries rather than UI-only logic.

**Given** rollback succeeds or fails
**When** the operation completes
**Then** the system records rollback status, linkage to the restored execution, and any follow-up diagnostic evidence in the audit trail
**And** the API response continues to avoid exposing raw backup paths.

### Story 3.3: Publish the Operational Runbook and Regression Coverage (NFR10, NFR11)

As a release owner,
I want documented operating steps and nearest-layer regression coverage for the ingestion lifecycle,
So that preview, apply, detail lookup, and rollback remain safe during final stabilization.

**Acceptance Criteria:**

**Given** the feature scope is ready for implementation
**When** the team prepares it for stabilization
**Then** the repository includes an operational runbook that documents preview, apply, execution lookup, rollback expectations, and local/staging-first usage constraints
**And** the runbook references execution ids and backup tokens rather than raw snapshot paths.

**Given** the new ingestion behavior is implemented
**When** automated validation runs
**Then** backend API, backend service, backend repository, and frontend admin-flow tests cover the nearest relevant behavior for preview, apply, detail, rollback, and admin-only access
**And** those tests extend the current indicator-load baseline rather than replacing it with unrelated abstractions.
