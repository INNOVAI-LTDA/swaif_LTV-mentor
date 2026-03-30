# Batch G Data Ingestion Admin Sprint Plan

Date: 2026-03-30
Scope: `batch-g-data-ingestion-admin`
Primary inputs:
- `_bmad-output/planning-artifacts/batch-g-data-ingestion-admin-implementation-readiness.md`
- `_bmad-output/planning-artifacts/batch-g-data-ingestion-admin-epics-and-stories.md`
- `_bmad-output/planning-artifacts/batch-g-data-ingestion-admin-architecture.md`

## Planning Basis

This sprint plan sequences the Batch G epics as a constrained brownfield extension of the current admin indicator-load flow.

Planning assumptions held from the authoritative bundle:

- keep the feature inside the existing `/app/admin` surface and selected-student workflow
- keep FastAPI routes thin, service orchestration in `backend/app/services`, and JSON persistence in repositories
- preserve the standardized API error envelope and frozen v1 compatibility expectations
- keep approved write targets limited to `measurements`, `checkpoints`, and `ingestion_executions`
- keep Batch G scoped to `manual_assisted` ingestion for one selected student enrollment at a time

## Current Snapshot

- Batch G epics and stories are fully decomposed, but no Batch G story files exist yet under `_bmad-output/implementation-artifacts`.
- The existing `_bmad-output/implementation-artifacts/sprint-status.yaml` belongs to the production-readiness track and was not reused for this scope.
- The current codebase already provides the admin boundary, the selected-student indicator-load flow, and snapshot tooling, but it does not yet provide Batch G preview/apply/audit orchestration.
- The readiness assessment for this bundle is `needs-work`, not `ready`.

## Pre-Sprint Approval Gate

Do not start implementation stories until the following planning issues are explicitly closed in the planning bundle:

1. Freeze the Batch G scope in a formal PRD addendum or equivalent approval artifact so the discovery brief and architecture no longer disagree on source mode and allowed targets.
2. Define the exact compatibility behavior of `POST /admin/alunos/{student_id}/indicadores/carga-inicial`, including request mapping, response shape, and error behavior during migration.
3. Resolve the persistence-rule conflict between Batch G `replace_enrollment` semantics and the admin CRUD spec language about preserving historical measurements.
4. Define how rollback outcome updates are written back to `ingestion_executions` after the operator-assisted restore step.
5. Decide whether execution-detail frontend rendering is in current scope or remains backend-only for Batch G.

Until those items are approved, all implementation stories remain `backlog` and the plan should be treated as conditional sequencing rather than execution authorization.

## Sprint 1 - Preview Foundation

Purpose: establish the backend and frontend contract boundary for preview without widening scope beyond the current admin/student flow.

| Story | Status | Why in this sprint | Dependencies | Exit criteria |
| ----- | ------ | ------------------ | ------------ | ------------- |
| `1-2-bind-the-panel-to-selected-student-context-and-source-metadata` | `backlog` | Freezes the selected-student context and source metadata that every later story depends on | approval gate closed | Selected student context and `source_type` / `source_label` are fixed for Batch G |
| `1-3-add-the-preview-contract-route-and-frontend-service-boundary` | `backlog` | Establishes the preview transport boundary before UI state work grows | `1-2` | Preview request/response contract exists through route, schema, service, adapter, and frontend service layers |
| `1-4-validate-preview-input-and-produce-structured-diagnostics` | `backlog` | Delivers the main backend value of Batch G without business writes | `1-3` | Preview validates the selected enrollment and returns execution ID, counts, conflicts, rejections, and approved affected stores |
| `1-1-expose-the-ingestao-de-dados-admin-panel` | `backlog` | Safe UI entry once the contract direction is fixed | approval gate closed | Existing admin surface exposes the new panel without adding a new top-level route |
| `1-5-render-the-preview-report-and-explicit-apply-gate` | `backlog` | Closes the preview loop and blocks apply until backend preview exists | `1-1`, `1-4` | Admin can review preview output and cannot apply without a reviewed preview execution |

Sprint 1 exit:

- preview works end to end without persisting business writes
- execution identifiers exist for preview
- the UI entry remains inside the existing admin shell and selected-student flow

## Sprint 2 - Controlled Apply and Compatibility

Purpose: make apply safe and auditable while preserving frozen-contract compatibility.

| Story | Status | Why in this sprint | Dependencies | Exit criteria |
| ----- | ------ | ------------------ | ------------ | ------------- |
| `2-1-enforce-apply-preconditions-from-preview-execution` | `backlog` | Prevents unsafe direct apply and freezes the preview-to-apply state machine | `1-5` | Apply only accepts explicit confirmation plus a valid preview execution in the same student context |
| `2-2-snapshot-revalidate-and-apply-only-approved-writes` | `backlog` | Introduces the core safety guarantee before any broader UX work | `2-1` | Apply reruns validation, snapshots before write, and only writes approved stores |
| `2-3-persist-execution-audit-and-failure-recovery-outcomes` | `backlog` | Makes preview/apply operationally supportable | `2-2` | Execution evidence, backup reference, and rollback outcome fields are persisted consistently |
| `2-4-return-the-final-apply-result-and-preserve-legacy-endpoint-compatibility` | `backlog` | Keeps the migration safe for frozen consumers | `2-2`, `2-3`, approval gate item 2 closed | Apply response is stable and legacy endpoint behavior is explicitly preserved |
| `2-5-complete-the-apply-ux-in-the-admin-panel` | `backlog` | Completes the user-visible apply loop after backend safety is real | `2-4` | Admin can confirm apply and review final outcome using the established service/adapter pattern |

Sprint 2 exit:

- apply requires a valid preview execution
- snapshot-before-write is enforced
- legacy endpoint compatibility is frozen and implemented
- preview/apply execution evidence is durable enough for support

## Sprint 3 - Follow-Up, Quality, and Operations

Purpose: expose execution follow-up safely and harden the slice for final stabilization.

| Story | Status | Why in this sprint | Dependencies | Exit criteria |
| ----- | ------ | ------------------ | ------------ | ------------- |
| `3-1-retrieve-structured-execution-details-by-identifier` | `backlog` | Adds operator follow-up after preview/apply is stable | `2-3`, approval gate item 5 closed | Execution detail retrieval is contract-defined and safe for its approved scope |
| `3-2-document-and-record-the-operator-assisted-rollback-path` | `backlog` | Closes the operational recovery loop | `2-3`, approval gate item 4 closed | Rollback procedure and rollback-status recording are both explicit and testable |
| `3-3-add-stabilization-focused-automated-coverage` | `backlog` | Hardens the slice before calling it ready | `1-5`, `2-5`, `3-1`, `3-2` | Nearest-layer backend and frontend tests cover preview, apply, rollback-sensitive behavior, and error envelopes |
| `3-4-publish-the-batch-g-operations-runbook` | `backlog` | Makes the feature operable in local/staging-first mode | `3-2` | Runbook covers preview, apply, execution lookup, backup expectations, and rollback verification |

Sprint 3 exit:

- operators can inspect execution outcomes in the approved scope
- rollback remains operator-assisted but documented and recordable
- test and runbook coverage match the approved Batch G behavior

## Recommended Execution Order

1. Close the pre-sprint approval gate.
2. `1-2-bind-the-panel-to-selected-student-context-and-source-metadata`
3. `1-3-add-the-preview-contract-route-and-frontend-service-boundary`
4. `1-4-validate-preview-input-and-produce-structured-diagnostics`
5. `1-1-expose-the-ingestao-de-dados-admin-panel`
6. `1-5-render-the-preview-report-and-explicit-apply-gate`
7. `2-1-enforce-apply-preconditions-from-preview-execution`
8. `2-2-snapshot-revalidate-and-apply-only-approved-writes`
9. `2-3-persist-execution-audit-and-failure-recovery-outcomes`
10. `2-4-return-the-final-apply-result-and-preserve-legacy-endpoint-compatibility`
11. `2-5-complete-the-apply-ux-in-the-admin-panel`
12. `3-1-retrieve-structured-execution-details-by-identifier`
13. `3-2-document-and-record-the-operator-assisted-rollback-path`
14. `3-3-add-stabilization-focused-automated-coverage`
15. `3-4-publish-the-batch-g-operations-runbook`

## Immediate Next Step

Recommended next command: `bmad-correct-course`

Reason:

- the authoritative bundle is not yet implementation-ready
- the next move is to close the documented planning contradictions, not to materialize an implementation story prematurely
- once the approval gate is closed, the first story to create should be `1-2-bind-the-panel-to-selected-student-context-and-source-metadata`

## Stop Conditions

- Do not create implementation stories while the pre-sprint approval gate remains open.
- Do not start Epic 2 before Sprint 1 delivers a real preview execution contract.
- Do not mark Batch G ready for stabilization while legacy endpoint compatibility and rollback recording remain ambiguous.
