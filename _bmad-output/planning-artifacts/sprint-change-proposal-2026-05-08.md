# Sprint Change Proposal: Major Architecture and API Replan for Data Structure Refactor

Date: 2026-05-08
Project: swaif_LTV-mentoria
Requested by: dmene
Mode: Batch
Revision basis: `docs/architecture/new_database_architecture.md`
Change scope: Major
Recommended path: Hybrid of Option 1 (direct corrective stabilization) + Option 3 (architecture/PRD/story replan)

## 1. Issue Summary

### Trigger
The original proposal assumed a limited runtime refactor around metric scoring and normalization. The newly provided architecture document shows the change is broader and structural:

- a new relational database architecture is being introduced for users, organizations, products, product pillars, product metrics, and enrollments
- the runtime metric grammar is being redesigned into a more formal DSL with explicit `input`, `scoring`, and `normalization` blocks
- the current backend still runs on JSON repositories and legacy domain boundaries such as `protocol`, `mentor`, `student`, and file-backed stores

This means the platform is not only changing how scores are computed. It is changing:

- persistence model
- entity model and naming boundaries
- route/service/repository assumptions
- operational backup/restore assumptions
- API contract semantics in admin, mentor, and student surfaces

### Concrete evidence already observed
The current codebase already surfaced a route/service drift failure:

- `StudentVinculoService.__init__() got an unexpected keyword argument 'contacts'`

That defect is important because it confirms the system already contains stale integration assumptions at route level. With the new architecture, this class of issue is expected to widen unless the refactor is treated as a coordinated platform migration rather than a local service change.

### Revised problem statement
This is no longer a moderate API review following a scoring change. It is a major architecture transition with platform-wide API impact. The current implementation and planning artifacts underestimate the scope because they do not yet account for:

- migration from JSON-backed runtime repositories to relational tables
- mapping between current domain model and new database entities
- frozen v1 route compatibility during model migration
- persistence-layer differences affecting backup, rollback, and operational tooling
- the fact that the metric DSL itself is now an explicit architectural concern rather than a local configuration detail

## 2. Checklist Summary

### Section 1: Understand the Trigger and Context
- [x] Done: Trigger revised from local scoring refactor to major architecture transition.
- [x] Done: Core problem classified as technical and architectural divergence between current runtime and target data architecture.
- [x] Done: Supporting evidence includes stale route wiring, new relational schema definitions, and metric DSL redesign requirements.

### Section 2: Epic Impact Assessment
- [!] Action-needed: Current epic assumptions are no longer sufficient.
- [!] Action-needed: New work must be split between stabilization of current API and planned migration toward the new database/domain model.
- [!] Action-needed: Future epics depending on current JSON repositories, route wiring, or metric semantics are affected.
- [!] Action-needed: Epic order and priorities must change.

### Section 3: Artifact Conflict and Impact Analysis
- [x] Done: Existing architecture documents are now incomplete relative to the stated target database model.
- [x] Done: Frontend integration documentation must be updated because the domain model behind API payloads may change even when route names do not.
- [x] Done: Testing strategy must explicitly cover coexistence and migration between JSON and relational persistence.
- [!] Action-needed: Planning artifacts, architecture docs, and story definitions need revision before further implementation beyond local fixes.

### Section 4: Path Forward Evaluation
- [x] Done: Option 1 is only partially viable for immediate stabilization.
- [ ] N/A: Full rollback is still not recommended.
- [x] Done: Option 3 is now required, not optional.
- [x] Done: Recommended approach revised to a major hybrid replan.

### Section 5: Proposal Components
- [x] Done: Revised issue summary provided.
- [x] Done: Revised impact analysis documented.
- [x] Done: Revised path forward and handoff plan documented.

### Section 6: Final Review and Handoff
- [!] Action-needed: User approval required before planning artifacts and sprint tracking are updated.
- [!] Action-needed: If approved, this should be routed as a major scope change with Product Manager / Architect involvement.

## 3. Impact Analysis

### 3.1 Architectural Impact

#### Current backend reality
The backend currently relies heavily on `JsonRepository` and file-backed repositories across the main domain entities, including:

- users
- students
- mentors
- organizations
- protocols
- pillars
- metrics
- enrollments
- measurements
- checkpoints
- measurement overalls

This is visible across `backend/app/storage/**` and route wiring in `backend/app/api/routes/**`.

#### Target architecture from the new document
The provided architecture introduces relational tables such as:

- `deva_accmed_users`
- `deva_accmed_organizations`
- `deva_accmed_products`
- `deva_accmed_product_pillars`
- `deva_accmed_product_metrics`
- `deva_accmed_enrollments`

That is not a storage implementation detail. It implies a new canonical domain backbone.

#### Architectural conclusion
The proposal must now account for a dual problem:

1. Stabilize the current JSON-backed API so development is not blocked.
2. Replan the migration path from current runtime entities to the new relational architecture.

### 3.2 Domain Model Impact

The new architecture introduces or emphasizes different canonical concepts:

- `provider_user_id` and `client_user_id` instead of mentor/student pairing through current repository shape
- `product_id` and `product_metrics` rather than the existing `protocol`-centric naming in major parts of the backend
- `organization_id` on users and products in ways that may not map 1:1 to the current service assumptions

This creates direct risk in:

- admin CRUD routes
- auth and role resolution
- student/mentor linkage logic
- command center and matrix queries
- canonical repository adapters

### 3.3 Metric DSL Impact

The new document also reframes the metric grammar itself:

- `condition` is considered semantically overloaded
- `description` should stop acting as logical identity
- `and` should stop acting as implicit range syntax
- `score_type` currently carries too much behavior
- normalization should become a formal policy contract

This aligns with the implemented v2 direction, but it also means the DSL is now an architectural artifact, not just a code implementation detail.

### 3.4 Affected Route Surfaces

#### Admin route family
- `/admin/alunos`
- `/admin/alunos/{student_id}/vincular-mentoria`
- `/admin/mentorias/{organization_id}/alunos`
- `/admin/alunos/{student_id}/indicadores/carga-inicial`
- `/admin/alunos/{student_id}/detalhe`
- `/admin/centro-comando/alunos`
- `/admin/centro-comando/alunos/{student_id}`
- `/admin/centro-comando/alunos/{student_id}/timeline-anomalias`
- `/admin/radar/alunos/{student_id}`
- `/admin/matriz-renovacao`
- admin metrics routes
- admin method configuration routes
- admin product, pillar, mentor, mentoria, and client routes

#### Mentor route family
- mentor command center routes
- mentor radar routes
- mentor matrix routes
- mentor metric detail routes

#### Student route family
- student workspace radar
- student workspace measurement updates
- any self-service route reading normalized metric state

#### Auth route family
- login and identity resolution are affected indirectly because role, organization/product affiliation, and user identity are part of the new data architecture.

### 3.5 Service and Repository Dependency Impact

#### Immediately affected services
- `app/services/metric_score_service.py`
- `app/services/student_workspace_service.py`
- `app/services/admin_metric_service.py`
- `app/services/method_config_service.py`
- `app/services/student_vinculo_service.py`
- `app/services/admin_student_service.py`
- `app/services/admin_student_link_service.py`
- `app/services/indicator_carga_service.py`

#### Immediately affected repositories
- all `JsonRepository`-backed domain repositories
- canonical repository adapters that bridge current domain naming
- snapshot/restore logic in `app/operations/storage_maintenance.py`

#### Why this is major
The new database architecture is not a drop-in replacement for one repository. It affects the central storage abstraction pattern of the backend.

## 4. Contract Risks

### Frozen v1 contract risk remains active
The frozen contract still forbids:

- removing existing response fields
- changing existing response field types
- renaming existing endpoints

### Revised risk categories
1. Persistence migration can alter ordering, defaults, missing/null behavior, and related-object resolution in existing responses.
2. Domain renaming pressure from `protocol`/`mentor`/`student` to `product`/`provider_user`/`client_user` can leak into routes or adapters in breaking ways.
3. Metric DSL changes can alter score semantics while preserving the same endpoint shape.
4. Backup/rollback assumptions currently built around JSON snapshots do not automatically carry over to relational persistence.
5. Existing tests centered on current repository semantics may become false positives or false negatives during migration unless explicitly reworked.

## 5. Path Forward Evaluation

### Option 1: Direct Adjustment
Status: Partially viable
Effort: Medium
Risk: High

This remains viable only for immediate blockers in the current architecture, such as route wiring defects and API regressions in the JSON-backed runtime.

### Option 2: Potential Rollback
Status: Not viable
Effort: High
Risk: High

Rollback is still not recommended because the target direction is now clearer, not weaker. The issue is not lack of direction; it is mismatch between plan and architectural scope.

### Option 3: PRD / MVP / Architecture Review
Status: Required
Effort: High
Risk: Medium

This is now required because the architecture document materially changes the system design assumptions. The current planning and architecture artifacts are no longer sufficient.

### Recommended Approach
Selected approach: Hybrid with major replan

Rationale:
- keep current stabilization work moving in the existing runtime
- stop treating the change as a local implementation detail
- update architecture, planning, and test strategy before committing to further migration-sensitive implementation
- explicitly split short-term stabilization from long-term persistence migration

## 6. Detailed Change Proposals

### 6.1 Story / Backlog Changes

#### Proposal A: Split work into two tracks

OLD:
- Continue implementation as a single scoring/API stabilization effort.

NEW:
- Track 1: Stabilize the current JSON-backed API and restore full regression confidence.
- Track 2: Plan and sequence migration toward the new relational architecture and canonical domain model.

Rationale:
These are different kinds of work with different risks. Mixing them without separation will blur validation and handoff.

#### Proposal B: Add migration planning stories

NEW stories required:
- data model mapping story: current JSON entities -> target relational entities
- repository migration strategy story
- contract compatibility story for migration phase
- operational tooling story for backup/restore beyond JSON snapshots
- API adapter/coexistence story if both runtime models must temporarily coexist

### 6.2 Architecture Changes

Artifact: `_bmad-output/planning-artifacts/batch-g-data-ingestion-admin-architecture.md`

OLD:
- architecture centered on ingestion preview/apply around existing JSON-backed stores

NEW:
- add explicit note that this architecture currently describes the JSON-backed runtime, not the newly proposed relational persistence target
- add a section defining migration assumptions and what remains in current runtime versus target runtime
- add explicit incompatibility note around snapshot/restore tooling and route/repository assumptions

Rationale:
The architecture document must stop implying that current storage boundaries are the long-term system shape if the project is now moving toward relational persistence.

### 6.3 Planning Artifact Changes

Artifacts affected:
- epics and stories
- sprint planning artifacts
- implementation readiness assumptions

OLD:
- validation tasks assume local brownfield expansion without fundamental storage change

NEW:
- add explicit major-change note that persistence architecture and domain backbone are being revised
- resequence work so stabilization and migration planning precede additional feature expansion
- update readiness criteria to require migration-path clarity before implementation that depends on target relational model

### 6.4 Frontend Integration Changes

Artifact: `docs/mvp-mentoria/frontend-integration-architecture.md`

OLD:
- frontend assumes stable backend DTOs normalized through adapters

NEW:
- add guidance that backend semantic drift may come from persistence/domain migration, not only route changes
- require adapter-level and service-level verification when backend canonical entities shift behind existing endpoint families

### 6.5 Test Strategy Changes

Artifact: `docs/mvp-mentoria/backend-test-strategy.md`

OLD:
- regression strategy assumes a single persistence model per milestone

NEW:
- add explicit gates for migration-sensitive changes:
  - current-runtime API regression must remain green
  - migration mapping tests must exist before repository swaps
  - backup/rollback behavior must be revalidated for any non-JSON persistence path
  - E2E smoke must be rerun after route wiring and domain mapping changes

## 7. Required Regression and Validation Work

### Immediate stabilization tests in current runtime
1. `backend/tests/api/test_admin_students_api.py`
2. `backend/tests/api/test_admin_indicator_load_api.py`
3. `backend/tests/api/test_admin_metrics_api.py`
4. `backend/tests/api/test_admin_method_config_api.py`
5. `backend/tests/api/test_student_workspace_api.py`
6. `backend/tests/api/test_radar_api.py`
7. `backend/tests/api/test_matrix_api.py`
8. `backend/tests/api/test_command_center_api.py`
9. `backend/tests/api/test_error_payload_api.py`
10. `backend/tests/e2e/test_smoke_mvp_flow.py`

### Additional tests now required by the revised architecture
1. mapping tests between current domain objects and target relational entities
2. migration tests for metric metadata fields and DSL serialization expectations
3. repository abstraction tests if coexistence between JSON and relational backends is introduced
4. backup/restore strategy tests for post-JSON persistence
5. contract-semantic tests ensuring current endpoints still satisfy frozen v1 assumptions during migration

## 8. MVP Impact and High-Level Action Plan

### MVP impact
MVP is still potentially achievable, but the current plan no longer provides enough control to guarantee it safely. This is now a planning and architecture problem, not just a validation problem.

### High-level action plan
1. Fix immediate route/service wiring blockers in the current runtime so validation is possible.
2. Run current-runtime API regression suite and restore a trustworthy baseline.
3. Update planning artifacts to distinguish current runtime from target relational architecture.
4. Produce a domain mapping document from existing entities to the new database entities.
5. Define repository migration strategy and coexistence rules.
6. Reassess stories/epics that assume current JSON storage or current domain naming.
7. Only after that, continue implementation against an approved migration plan.

## 9. Implementation Handoff

### Scope classification
Major

### Handoff recipients and responsibilities

#### Development team
- fix immediate route/service incompatibilities
- restore green regression baseline in the current runtime
- surface concrete integration blockers caused by architecture drift

#### Product Owner / Scrum Master
- create separate stabilization and migration-planning tracks
- resequence sprint work to reflect the major change
- update sprint tracking and story priorities

#### Product Manager / Architect
- review and approve the target data architecture against current runtime realities
- define the migration path and scope boundaries
- decide which target architectural changes are in-sprint, post-sprint, or post-MVP

#### QA / Test ownership
- expand regression strategy to cover both current-runtime stability and migration-sensitive behavior

### Success criteria
- current JSON-backed runtime is stable and regression-tested
- planning artifacts distinguish present-state implementation from target-state architecture
- migration path is explicitly defined
- no further feature work proceeds on hidden assumptions about persistence or canonical domain naming
- frozen v1 contract risk is actively controlled during the transition

## 10. Approval Request

This revised Sprint Change Proposal supersedes the earlier moderate-scope version. The newly provided architecture shows a major change that requires replan and architectural coordination, not only API review.

Approval requested:
- Approve this revised proposal as-is
- Revise specific sections
- Reject and choose a different path
