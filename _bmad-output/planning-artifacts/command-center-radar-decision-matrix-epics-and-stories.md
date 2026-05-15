---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/command-center-radar-decision-matrix-architecture.md
  - _bmad-output/project-context.md
  - docs/architecture/platform_architecture_operational_model.md
  - docs/mvp-mentoria/contracts-freeze-v1.md
  - docs/mvp-mentoria/contracts-command-center.md
  - docs/mvp-mentoria/contracts-radar.md
  - docs/mvp-mentoria/contracts-renewal-matrix.md
  - docs/mvp-mentoria/frontend-integration-architecture.md
workflowType: epics-and-stories
project_name: swaif_LTV-mentoria
user_name: dmene
date: 2026-05-09
lastStep: 4
status: complete
completedAt: 2026-05-09
scope: command-center-radar-decision-matrix
---

# swaif_LTV-mentoria - Epic Breakdown

## Overview

This document decomposes the approved PRD and architecture baseline for Command Center, Evolution Radar, and Decision Matrix into implementable epics and stories.

The plan preserves the frozen v1 contracts, keeps the current route -> service -> repository layering, and organizes implementation around the approved architecture slices:

- authoritative current-state facts
- append-only history
- rebuildable projection tables
- synchronous Radar refresh
- asynchronous Command Center and Decision Matrix refresh
- migration and backfill from JSON-backed stores
- operational rebuild, retry, and failure handling

## Requirements Inventory

### Functional Requirements

FR1: The platform must preserve the frozen v1 endpoints, response fields, field types, and mentoring vocabulary for Command Center, Evolution Radar, and Decision Matrix while moving implementation behind new fact, history, and projection repositories.

FR2: The platform must persist authoritative current-state facts for product assignments, current metric measures, current checkpoint state, and assignment score state required by all three analytical views.

FR3: The platform must append immutable history rows for every meaningful measurement, checkpoint, and assignment-score mutation from day one.

FR4: The platform must persist scoring-rule and projection-formula version metadata with derived outputs so historical results remain explainable and unchanged after future scoring changes.

FR5: The platform must serve Evolution Radar from dedicated assignment-by-pillar projection tables that support both current serving and immutable historical comparison.

FR6: The platform must synchronously refresh the affected assignment Radar projection after writes so mentor-visible Radar output reflects student changes within the approved 1-second tolerance.

FR7: The platform must serve Command Center from a dedicated assignment projection refreshed asynchronously after writes that affect urgency, days left, checkpoints, engagement, progress, or anomaly hints.

FR8: The platform must serve Decision Matrix from a dedicated assignment projection refreshed asynchronously after writes that affect progress, engagement, urgency, LTV, classification, or renewal reasoning, while keeping `decision_matrix_status` as helper state only.

FR9: The platform must persist product-level Radar history as aggregated assignment pillar outputs by product, pillar, and aggregation window.

FR10: Initial migration must backfill current-state facts, append-only history, score state, and projections from the existing JSON-backed measurement, checkpoint, and overall-score stores, marking seeded lineage explicitly.

FR11: Projection execution must log every refresh, rebuild, and failure attempt and allow targeted or full replay from authoritative facts plus history.

FR12: Operational handling must support retryable projection failures, manual intervention for terminal failures, and rebuild workflows that do not roll back already committed facts.

### NonFunctional Requirements

NFR1: Preserve the frozen v1 contract, including endpoint paths, field presence, field types, and the standardized error envelope `{ error: { status, code, message, details } }`.

NFR2: Keep the solution brownfield and layered: routes stay thin, services own orchestration, and repositories own persistence details.

NFR3: Meet the approved freshness targets for normal operations: Assignment Radar `<= 1 second`, Command Center `<= 15 seconds`, and Decision Matrix `<= 60 seconds` from committed write to refreshed assignment output.

NFR4: Projection refreshes and rebuilds must be idempotent and retryable.

NFR5: History tables and projection history tables must be append-only and must never rewrite past analytical outputs in place after scoring-rule changes.

NFR6: History retention for measurements, checkpoints, scores, and Radar history must last for the lifetime of the assignment with no v1 TTL.

NFR7: Initial backfill must stamp seeded rows with `seed_backfill` lineage and record projection rebuild execution so migrated state is auditable.

NFR8: Projections remain disposable read models and must never become the only authoritative source of business truth or historical evidence.

NFR9: Frontend-facing semantics must remain compatible with the existing adapter strategy, including canonical `student` normalization, `programName` compatibility, and optional field handling defined in the frontend integration architecture.

NFR10: Implementation must add nearest-layer automated coverage for repository persistence, service orchestration, API contract preservation, projection freshness, and rebuild/retry behavior.

### Additional Requirements

- Introduce authoritative fact tables for `product_assignments`, `metric_measures_current`, `journey_checkpoints_current`, and `assignment_score_state`.
- Introduce append-only history tables for `metric_measure_history`, `journey_checkpoint_history`, `assignment_score_history`, and `projection_run_log`.
- Introduce rebuildable projections for `command_center_assignment_projection`, `decision_matrix_assignment_projection`, `radar_axis_projection_current`, `radar_axis_projection_history`, and `product_radar_projection_history`.
- Use the approved assignment-scoped write contract: persist fact change, append history, recalculate score state, append score history, synchronously refresh Radar, then enqueue asynchronous Command Center and Decision Matrix refresh.
- Treat snapshots as optional derived artifacts for reporting or safety, not as the primary source of truth.
- Use product-level Radar aggregation as equal-weight assignment pillar averages per `product_id + pillar_id + window` unless a later approved change revises that rule.
- Seed backfill from the current JSON-backed `measurements`, `checkpoints`, and `measurement_overalls` stores and log projection rebuild provenance.
- Failed projection refreshes must not roll back committed facts; recovery occurs through retry or rebuild from facts plus history.
- `decision_matrix_status` may remain as a compatibility or filter helper, but Decision Matrix behavior must be driven by the richer projection model.

### UX Design Requirements

No standalone UX design document was revised for this scope. UX work remains constrained by the frozen contracts and the frontend integration architecture:

UX-DR1: Keep the existing view-service and adapter boundaries stable for Command Center, Radar, and Renewal Matrix while backend persistence changes behind the contract boundary.

UX-DR2: Preserve current adapter-level normalization rules such as `student` entity naming, `programName` canonicalization, numeric parsing, and optional field fallbacks instead of moving alias logic into components.

UX-DR3: Preserve Portuguese user-facing copy and current loading, error, and empty-state conventions for the three analytical surfaces.

UX-DR4: Keep the existing v1 payload shapes compatible with current UI expectations for Command Center summary/detail fields, Radar `axisScores`, and Decision Matrix portfolio rows.

### FR Coverage Map

FR1: Epic 1 - Establish authoritative facts behind the unchanged v1 analytical surfaces.

FR2: Epic 1 - Persist authoritative current-state facts and shared score state.

FR3: Epic 2 - Capture append-only lineage for measurements, checkpoints, and scores from day one.

FR4: Epic 2 - Preserve immutable version traceability for historical analytical outputs.

FR5: Epic 3 - Serve Evolution Radar from dedicated current and history projections.

FR6: Epic 3 - Enforce synchronous assignment-scoped Radar refresh within the 1-second tolerance.

FR7: Epic 4 - Serve Command Center from an asynchronous assignment projection.

FR8: Epic 4 - Serve Decision Matrix from an asynchronous assignment projection with non-authoritative helper status.

FR9: Epic 3 - Add product-level Radar aggregation history.

FR10: Epic 5 - Backfill facts, history, score state, and projections from JSON-backed stores.

FR11: Epic 6 - Log projection execution and support targeted or full replay.

FR12: Epic 6 - Provide retry, manual intervention, and rebuild handling without fact rollback.

## Epic List

### Epic 1: Stabilize the Analytical Surfaces on Authoritative Facts
Mentors and operators continue using the frozen v1 Command Center, Radar, and Decision Matrix APIs while the backend gains authoritative current-state facts and shared score state.
**FRs covered:** FR1, FR2

### Epic 2: Preserve Historical Lineage and Version Traceability
Mentors, operators, and future support workflows can explain how analytical outputs were produced because every meaningful mutation and score change is captured immutably from day one.
**FRs covered:** FR3, FR4

### Epic 3: Deliver Low-Latency Evolution Radar Projections
Students and mentors get current and historical Radar outputs from dedicated projections, with assignment updates reflected within the approved synchronous latency target.
**FRs covered:** FR5, FR6, FR9

### Epic 4: Deliver Scalable Command Center and Decision Matrix Projections
Mentors can monitor operational risk and renewal priorities from projection-backed Command Center and Decision Matrix views that refresh asynchronously after relevant assignment changes.
**FRs covered:** FR7, FR8

### Epic 5: Migrate Existing Analytical Data into the New Fact and History Model
The platform preserves existing JSON-backed analytical data by backfilling it into authoritative facts, append-only history, and seeded projections with explicit migration lineage.
**FRs covered:** FR10

### Epic 6: Make Projection Recovery and Rebuild Operationally Safe
Operators can detect failed projection work, retry targeted refreshes, and rebuild projections safely from facts plus history without corrupting authoritative data.
**FRs covered:** FR11, FR12

## Epic 1: Stabilize the Analytical Surfaces on Authoritative Facts

Introduce the shared authoritative write model that all three analytical surfaces depend on, while keeping the frozen v1 APIs and frontend-facing semantics intact.

### Story 1.1: Add Authoritative Assignment Fact Persistence

As a platform maintainer,
I want assignment facts persisted in an authoritative repository layer,
So that the analytical surfaces stop depending on ad hoc derived state.

**Acceptance Criteria:**

**Given** the current analytical services still read from legacy storage assumptions
**When** authoritative persistence for `product_assignments` is introduced behind repository boundaries
**Then** route handlers continue calling services without direct persistence knowledge
**And** frozen v1 endpoint paths and DTO field names remain unchanged.

**Given** an assignment is created or updated for an active mentor-student-product relationship
**When** the authoritative fact repository persists it
**Then** the row includes the baseline fields required by the architecture
**And** the persisted assignment row follows the seed and lifecycle rules fixed in Appendix C of the architecture baseline
**And** the service can resolve the same business state without reading from a projection table.

### Story 1.2: Persist Current Measures and Checkpoints as Shared Facts

As a platform maintainer,
I want current metric measures and checkpoint state persisted as first-class facts,
So that Radar, Command Center, and Decision Matrix all derive from the same current business truth.

**Acceptance Criteria:**

**Given** a measurement or checkpoint write for an assignment
**When** the service commits the write
**Then** the latest state is stored in `metric_measures_current` or `journey_checkpoints_current`
**And** uniqueness rules prevent duplicate current rows for the same assignment scope.

**Given** the current-state facts exist for an assignment
**When** the analytical services request the latest measures or checkpoints
**Then** they resolve current values from the fact repositories
**And** no view-specific projection is treated as the source of truth.

### Story 1.3: Introduce Shared Assignment Score State for All Three Views

As a mentor-facing platform,
I want progress, engagement, and overall score state recalculated into a shared current table,
So that all three analytical surfaces use the same latest score basis.

**Acceptance Criteria:**

**Given** an assignment has current measures and checkpoint state
**When** score recomputation runs after a relevant write
**Then** `assignment_score_state` stores progress, engagement, overall, pillar summary, and version metadata for that assignment
**And** the latest score state is available to Radar, Command Center, and Decision Matrix services.

**Given** a v1 Command Center, Radar, or Decision Matrix endpoint is called after the score state change
**When** the service assembles the response
**Then** it uses the shared score state behind the service boundary
**And** the response preserves the frozen field presence and types expected by the frontend adapters.

## Epic 2: Preserve Historical Lineage and Version Traceability

Capture immutable operational evidence so historical analytical outputs stay explainable even as the current-state model and scoring logic continue to evolve.

### Story 2.1: Append Measurement and Checkpoint History from Day One

As an operator,
I want every meaningful measurement and checkpoint mutation written to append-only history,
So that historical lineage exists from the first production-ready release of the new model.

**Acceptance Criteria:**

**Given** a measurement or checkpoint write succeeds for an assignment
**When** the write pipeline completes
**Then** a matching append-only history row is written with captured timestamps, source metadata, and change type
**And** the previous history rows remain untouched.

**Given** the same assignment field is updated more than once
**When** history is queried for lineage
**Then** each mutation appears as a separate history entry in capture order
**And** the latest current-state row can be reconciled back to its recorded mutation chain.

### Story 2.2: Append Immutable Score History with Version Metadata

As a support and analytics team member,
I want each score recalculation preserved with scoring and projection versions,
So that past outputs remain explainable after future formula changes.

**Acceptance Criteria:**

**Given** assignment score state is recalculated after a relevant write
**When** the recalculation succeeds
**Then** a new `assignment_score_history` row is appended with progress, engagement, overall, pillar summary, `scoring_rule_version`, `projection_formula_version`, and time context
**And** the current-state table is updated separately from the immutable history row.

**Given** scoring rules change after prior analytical outputs were produced
**When** historical score lineage is inspected
**Then** prior history rows still reference the original versions used at calculation time
**And** no existing history row is rewritten to the new rule version.

### Story 2.3: Preserve Lineage Contracts for Downstream Projection Consumers

As a projection service,
I want immutable lineage and version metadata available from repositories,
So that current rebuilds and historical explanations both use the same evidence chain.

**Acceptance Criteria:**

**Given** a projection or support workflow requests historical evidence for one assignment
**When** the relevant repositories are called
**Then** they can return measurement, checkpoint, and score lineage without reading mutable projection rows
**And** the lineage includes the metadata required by the approved architecture.

**Given** a developer or operator needs to compare current state to historical lineage
**When** both repository families are queried
**Then** the current-state facts and append-only history can be correlated by assignment and source context
**And** the API contract remains unchanged because the lineage stays behind service boundaries.

## Epic 3: Deliver Low-Latency Evolution Radar Projections

Build the dedicated Radar read model that satisfies the 1-second assignment refresh target while preserving immutable historical comparison and product-level trend reporting.

### Story 3.1: Build Assignment Radar Current and History Projections

As a mentor,
I want the Evolution Radar served from dedicated assignment-by-pillar projections,
So that current and historical Radar views remain fast and consistent.

**Acceptance Criteria:**

**Given** authoritative facts and score state exist for an assignment
**When** the Radar projection service computes the assignment output
**Then** it writes one current row per assignment and pillar into `radar_axis_projection_current`
**And** it appends immutable history rows into `radar_axis_projection_history` for the same calculation event.

**Given** the existing Radar endpoint is called for a student assignment
**When** the service assembles `axisScores`
**Then** it reads from the Radar current projection
**And** it preserves the Appendix B contract map, including `axisKey`, `axisLabel`, `axisSub`, numeric compatibility, and `insight` handling.

### Story 3.2: Enforce Synchronous Assignment-Scoped Radar Refresh

As a mentor,
I want student Radar updates reflected almost immediately,
So that the mentor-visible Radar stays within the approved 1-second tolerance.

**Acceptance Criteria:**

**Given** a measurement or checkpoint write commits for one assignment
**When** the write pipeline completes
**Then** Radar projection recomputation for the affected assignment runs synchronously in the same operational flow
**And** the refreshed assignment payload is eligible to become mentor-visible within the approved latency budget.

**Given** the synchronous Radar refresh fails after the facts were committed
**When** the failure is logged
**Then** the committed facts remain authoritative
**And** the failure is surfaced for retry or rebuild without silently serving rewritten historical rows.

### Story 3.3: Add Product-Level Radar Trend Aggregation

As a product operator,
I want product-level Radar history aggregated from assignment pillar outputs,
So that product maturity can be tracked over time without recalculating from raw metrics at read time.

**Acceptance Criteria:**

**Given** assignment Radar history exists for a product and aggregation window
**When** the product-level Radar aggregation job runs
**Then** it writes one immutable row per `product_id + pillar_id + window` into `product_radar_projection_history`
**And** the averages follow the approved equal-weight aggregation rule.

**Given** historical product maturity is queried for reporting or analysis
**When** the aggregation repository is used
**Then** the data is served from `product_radar_projection_history`
**And** the source version metadata remains traceable to the underlying assignment calculations.

## Epic 4: Deliver Scalable Command Center and Decision Matrix Projections

Build asynchronous, assignment-scoped projections for the mentor's operational and portfolio views without making those read models authoritative business state.

### Story 4.1: Build Command Center Assignment Projection Serving

As a mentor,
I want Command Center rows served from a dedicated projection,
So that risk, timing, checkpoint, and anomaly-oriented views stay fast under higher load.

**Acceptance Criteria:**

**Given** authoritative assignment facts, checkpoints, and score state exist
**When** the Command Center projection service computes the current row
**Then** it writes the required list/detail serving fields into `command_center_assignment_projection`
**And** the projection stores anomaly hints only as projection data for this phase.

**Given** the v1 Command Center endpoints are called after the projection refresh
**When** the service assembles list or detail payloads
**Then** it reads from the Command Center projection plus the required detail sources behind service boundaries
**And** the API response remains compatible with the frozen Command Center contract as mapped in Appendix B, including the dedicated timeline or anomaly payload family.

### Story 4.2: Build Decision Matrix Assignment Projection Serving

As a mentor,
I want Decision Matrix rows served from a dedicated projection,
So that renewal prioritization remains scalable and consistent.

**Acceptance Criteria:**

**Given** authoritative assignment facts and score state exist
**When** the Decision Matrix projection service computes the current row
**Then** it writes quadrant, renewal reasoning, suggestion, markers, urgency, days left, and LTV fields into `decision_matrix_assignment_projection`
**And** `decision_matrix_status` remains only a compatibility or filter helper outside the authoritative projection logic.

**Given** the existing Renewal Matrix endpoint is called with supported filters
**When** the service assembles the portfolio payload
**Then** it reads from the Decision Matrix projection
**And** the response preserves the frozen v1 item shape, KPI semantics, and filter behavior fixed in Appendix B.

### Story 4.3: Add Assignment-Scoped Async Refresh for Command Center and Decision Matrix

As a platform operator,
I want Command Center and Decision Matrix projections refreshed asynchronously after relevant writes,
So that portfolio-oriented views stay current without blocking the synchronous Radar path.

**Acceptance Criteria:**

**Given** a write changes data that affects Command Center or Decision Matrix inputs
**When** the write flow completes after fact persistence and Radar refresh
**Then** an assignment-scoped projection job is enqueued for the affected projection targets
**And** the job is idempotent and replayable.

**Given** the asynchronous refresh completes under normal operating conditions
**When** the affected assignment is queried later through Command Center or Decision Matrix
**Then** the refreshed output becomes visible within the approved latency budget for that surface
**And** execution is recorded in the projection run log.

## Epic 5: Migrate Existing Analytical Data into the New Fact and History Model

Move current JSON-backed analytical evidence into the new architecture without losing lineage, breaking contracts, or hiding the migration provenance.

### Story 5.1: Backfill Current Facts and History from JSON Sources

As a migration operator,
I want existing JSON-backed measurements, checkpoints, and score inputs migrated into facts and history,
So that the new model starts with preserved current state and traceable seed lineage.

**Acceptance Criteria:**

**Given** the migration runner reads the approved JSON-backed stores
**When** the backfill executes
**Then** current records are seeded into the corresponding fact tables
**And** `product_assignments` and compatibility identifiers follow the source rules fixed in Appendix C
**And** matching append-only history rows are written with `change_type = seed_backfill`.

**Given** a seeded assignment has backfilled facts and history
**When** the migration lineage is inspected
**Then** operators can identify that the rows originated from the seed run
**And** the seed metadata is sufficient to audit which source records were migrated.

### Story 5.2: Seed Assignment Score State and Projection Rows During Backfill

As a migration operator,
I want score state and analytical projections seeded from the migrated inputs,
So that the three mentor views become usable immediately after migration.

**Acceptance Criteria:**

**Given** current facts were backfilled successfully for an assignment
**When** the migration pipeline seeds analytical outputs
**Then** `assignment_score_state` and its matching history are created from the migrated inputs
**And** current and historical projection rows are generated for Radar, Command Center, and Decision Matrix as applicable.

**Given** the seed projection rebuild runs during migration
**When** it completes or fails
**Then** the execution is recorded in `projection_run_log`
**And** the logged run follows the schema and generation semantics fixed in Appendix A
**And** later operators can identify the seed rebuild as distinct from normal refresh traffic.

### Story 5.3: Validate Post-Backfill Parity Against Frozen v1 Contracts

As a release owner,
I want parity checks after backfill,
So that migrated data serves the same frozen v1 payloads expected by the frontend.

**Acceptance Criteria:**

**Given** backfilled facts and projections exist for the migrated scope
**When** the contract and service parity checks run against Command Center, Radar, and Decision Matrix endpoints
**Then** the responses preserve frozen field presence, types, and semantics for supported records
**And** the parity review is evaluated against Appendix B and Appendix C rather than ad hoc field inference
**And** any mismatch is surfaced as a migration blocker.

**Given** parity validation identifies differences between source-backed and projection-backed outputs
**When** the comparison results are reviewed
**Then** the discrepancies are traceable to assignment-level migrated evidence
**And** the team can resolve them without bypassing the new repository boundaries.

## Epic 6: Make Projection Recovery and Rebuild Operationally Safe

Add the run logging, retry, and manual rebuild discipline needed to keep projection-backed serving reliable once normal writes and migration flows are active.

### Story 6.1: Persist Projection Run Logging and Failure States

As an operator,
I want every projection refresh and rebuild attempt recorded,
So that I can trace success, failure, and replay state for each assignment or batch execution.

**Acceptance Criteria:**

**Given** a projection refresh or rebuild starts for Radar, Command Center, Decision Matrix, or product-level Radar
**When** the execution is recorded
**Then** `projection_run_log` captures the projection target, scope, start time, completion state, and relevant version context
**And** the log row follows the required schema defined in Appendix A of the architecture baseline
**And** the log entry is durable even if the projection later fails.

**Given** a projection execution fails
**When** the failure state is written
**Then** the log distinguishes retryable failures from terminal failures
**And** the failure record is linked to the affected assignment, product, or rebuild scope.

### Story 6.2: Add Targeted Retry and Rebuild Operations from Facts Plus History

As an operator,
I want targeted retry and rebuild tooling,
So that projection failures can be recovered without changing committed facts.

**Acceptance Criteria:**

**Given** a retryable projection failure exists for one assignment or batch scope
**When** a retry or rebuild is requested
**Then** the projection service replays from authoritative facts plus append-only history
**And** the operation does not require rolling back committed fact rows.

**Given** a full rebuild is requested for a projection family
**When** the rebuild completes
**Then** current projection rows are regenerated from the approved source order
**And** immutable projection history rows remain append-only and only gain new rows through the replacement-generation policy fixed in Appendix A.

### Story 6.3: Add Automated Validation for Refresh, Retry, and Recovery Paths

As a release owner,
I want automated coverage for projection operations,
So that rebuild and retry behavior stays safe as the analytical architecture evolves.

**Acceptance Criteria:**

**Given** repository, service, and API tests run for this scope
**When** the automated suites execute
**Then** they cover current fact persistence, append-only lineage, synchronous Radar refresh, asynchronous Command Center and Decision Matrix refresh, backfill lineage, and retry/rebuild behavior
**And** contract guard tests confirm the frozen v1 responses remain intact.

**Given** a change regresses projection freshness or recoverability
**When** the nearest-layer automated tests run
**Then** the regression is detected before release
**And** the failing test identifies whether the defect is in repositories, services, or API contract preservation.