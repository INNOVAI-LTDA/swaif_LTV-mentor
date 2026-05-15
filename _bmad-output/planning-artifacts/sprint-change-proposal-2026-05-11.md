# Sprint Change Proposal: Supabase/Postgres-Only Runtime Replan

Date: 2026-05-11
Project: swaif_LTV-mentoria
Requested by: dmene
Mode: Batch
Change scope: Major
Recommended path: Hybrid of Option 1 (direct adjustment) + Option 3 (MVP/architecture review)

## 1. Issue Summary

### Trigger
The team needs to stop planning for JSON-plus-relational coexistence and formalize a single runtime direction: Supabase/Postgres-only persistence for production paths.

### Revised problem statement
Current planning artifacts still assume extended JSON authority and phased coexistence. That now conflicts with the requested runtime direction and increases risk of duplicated implementation effort. Stories, acceptance criteria, and risks must be updated before deeper coding continues.

### Evidence
- `docs/architecture/new_database_architecture.md` defines the target relational table model.
- `_bmad-output/planning-artifacts/batch-g-data-ingestion-admin-epics-and-stories.md` still contains JSON-authoritative assumptions.
- `_bmad-output/planning-artifacts/batch-g-data-ingestion-admin-architecture.md` still contains coexistence and JSON-first sequencing.

## 2. Checklist Summary

### Section 1: Understand Trigger and Context
- [x] Done: Trigger identified as strategic runtime direction change.
- [x] Done: Problem categorized as strategic pivot plus architecture correction.
- [x] Done: Evidence recorded from architecture and planning artifacts.

### Section 2: Epic Impact Assessment
- [x] Done: Current epics require scope and acceptance-criteria changes.
- [x] Done: Epic ordering must change to prioritize Postgres runtime baseline.
- [x] Done: Future stories that assume JSON authority are now invalid.

### Section 3: Artifact Conflict and Impact Analysis
- [x] Done: PRD remains usable but requires an explicit runtime decision addendum.
- [x] Done: Architecture and epics/stories artifacts require direct revisions.
- [x] Done: Test strategy and rollout readiness gates require persistence-direction updates.

### Section 4: Path Forward Evaluation
- [x] Option 1 (Direct Adjustment): Viable for immediate story and gate updates.
- [ ] Option 2 (Rollback): Not viable; reversion would lose valid architecture work.
- [x] Option 3 (MVP Review): Required to lock scope and avoid rework.
- [x] Selected approach: Hybrid (Option 1 + Option 3).

### Section 5 and 6: Proposal and Handoff
- [x] Done: Change proposal with explicit story deltas prepared.
- [!] Action-needed: User approval required before rewriting epic/source artifacts and sprint status.

## 3. Impact Analysis

### 3.1 Epic impact
- Epic 1 in current plan overweights JSON stabilization as long-term runtime.
- Epic 2/3 migration stories include coexistence assumptions that are no longer target behavior.
- Epic 4 rollback and readiness gates must shift from dual-model language to Postgres-runtime go-live controls.

### 3.2 Artifact conflicts
- PRD requires a runtime decision addendum: "Supabase/Postgres is the sole production runtime persistence."
- Architecture document must remove "JSON runtime remains authoritative" from target-state path.
- Epics/stories must remove acceptance criteria that preserve JSON as production authority.

### 3.3 Technical impact
- Service/repository boundaries remain valid, but repository implementations and tests should target Postgres runtime behavior.
- Contract freeze constraints remain unchanged.
- Backup/rollback process must be redefined for Postgres operational reality, not JSON snapshots.

## 4. Recommended Approach

### Selected approach
Hybrid: immediate planning correction plus architecture-level MVP review.

### Rationale
- Keeps momentum while preventing wrong-track implementation.
- Avoids partial coding on assumptions that will be replaced.
- Preserves frozen v1 contract and layered boundaries while changing runtime persistence direction.

### Effort and timeline impact
- Effort: Medium for planning changes, High for implementation sequence realignment.
- Timeline impact: Moderate short-term delay, high rework avoidance.

## 5. Detailed Change Proposals (Stories and Acceptance Criteria)

## 5.1 Story-level deltas

Story: Epic 1 / Story 1.2 `Keep Batch G Ingestion JSON-Authoritative in Track 1`  
Section: Story title + Acceptance Criteria

OLD:
- "Keep Batch G Ingestion JSON-Authoritative in Track 1"
- AC requires writes to remain in approved JSON-backed targets.

NEW:
- "Keep Batch G Ingestion Contract-Stable While Switching Runtime Persistence to Supabase/Postgres"
- AC:
  - Given preview/apply ingestion flows run in the current admin surface
  - When operator submits and confirms ingestion
  - Then authoritative writes persist in Supabase/Postgres targets aligned to approved schema
  - And the v1 endpoint contract, payload shape, and error envelope remain unchanged
  - And no production write path depends on JSON files as system-of-record.

Rationale: Removes runtime contradiction and keeps contract stability.

Story: Epic 1 / Story 1.3 `Re-Establish the Current-Runtime Regression Baseline`  
Section: Acceptance Criteria

OLD:
- Regression baseline defined against JSON-backed runtime.

NEW:
- Regression baseline defined against Supabase/Postgres runtime for production paths.
- AC adds:
  - Given runtime regression suites execute
  - When admin, mentor, student, command center, radar, and matrix suites run
  - Then all pass with Postgres-backed repositories and frozen v1 contract compliance
  - And parity checks against legacy JSON fixtures are informational only, not runtime authority checks.

Rationale: Aligns quality gate with requested runtime.

Story: Epic 2 / Story 2.2 `Harden Canonical Adapters and Migration-Aware Service Boundaries`  
Section: Acceptance Criteria

OLD:
- Coexistence and migration-aware boundaries with one writer per phase.

NEW:
- Canonical adapter boundaries remain, but remove long-lived coexistence assumptions.
- AC adds:
  - Given service boundaries are updated
  - When routes call services
  - Then services use Postgres repositories for production runtime data
  - And canonical adapters remain internal translation seams, not dual-runtime orchestration seams
  - And any temporary import tooling is isolated from request-time runtime flows.

Rationale: Preserves architecture layering while narrowing runtime model.

Story: Epic 3 / Story 3.1 `Add Relational Mirror Repositories for Direct-Target Entities Only`  
Section: Story intent + Acceptance Criteria

OLD:
- Relational repositories treated as non-authoritative mirror.

NEW:
- "Implement Supabase/Postgres Repositories as Runtime Authority for Direct-Target Entities"
- AC:
  - Given direct-target entities are in schema
  - When repositories are wired
  - Then Postgres repositories are authoritative for production reads/writes for those entities
  - And unresolved domains (measurements/checkpoints/overalls) are explicitly gated with documented interim behavior
  - And unresolved domains must not silently fall back to JSON in production mode.

Rationale: Converts mirror model into runtime model with explicit unresolved-domain handling.

Story: Epic 3 / Story 3.3 `Validate Shadow-Read Parity on Selected Current-Runtime Surfaces`  
Section: Acceptance Criteria

OLD:
- Shadow-read parity to validate mirror before cutover.

NEW:
- Contract and semantic regression validation against frozen v1 using Postgres as runtime.
- AC:
  - Given runtime storage is Postgres-backed
  - When route-level and service-level tests run
  - Then semantic and contract assertions pass against frozen v1 expectations
  - And shadow-read comparisons, if kept, are migration-audit artifacts only.

Rationale: Keeps verification objective while removing dependency on mirror strategy.

Story: Epic 4 / Story 4.1 `Define the Split Backup and Rollback Operating Model`  
Section: Acceptance Criteria

OLD:
- JSON snapshot rollback + relational rollback split.

NEW:
- "Define Postgres-Centric Backup and Rollback Operating Model"
- AC:
  - Given production runtime is Supabase/Postgres
  - When backup/rollback controls are defined
  - Then restore points, migration manifests, and reconciliation evidence are specified for Postgres operations
  - And JSON snapshot restore is classified as legacy/offline migration utility only
  - And operator runbooks clearly separate production rollback from historical import tooling.

Rationale: Operational control must follow runtime authority.

## 5.2 New/updated acceptance criteria themes across impacted stories
- Runtime authority must explicitly be Supabase/Postgres for production paths.
- Frozen v1 contract compatibility remains mandatory.
- No hidden JSON production fallback.
- Unresolved schema areas must be explicitly gated and documented.
- Operational rollback must be Postgres-native.

## 6. Risk Register (Updated)

### R1: Hidden JSON dependency in production code paths
- Probability: High
- Impact: High
- Mitigation: Add explicit "no JSON production fallback" acceptance criteria and integration tests.

### R2: Contract drift while switching repository implementations
- Probability: Medium
- Impact: High
- Mitigation: Keep strict route-level contract tests for v1 payload shape/types and error envelope.

### R3: Unresolved domains (measurements/checkpoints/overalls) block full cutover
- Probability: High
- Impact: Medium/High
- Mitigation: Define interim domain handling explicitly in stories before coding deeper.

### R4: Rollback ambiguity during persistence transition
- Probability: Medium
- Impact: High
- Mitigation: Publish Postgres-centric rollback runbook with restore point checklist and rehearsal evidence.

### R5: Team executes obsolete coexistence stories
- Probability: Medium
- Impact: Medium
- Mitigation: Re-baseline sprint artifacts and mark superseded stories clearly before implementation resumes.

## 7. Implementation Handoff

### Scope classification
Major

### Routing
- Product Owner / Scrum Master: update epic/story source artifact and sprint sequencing.
- Architect: update transition architecture to reflect Postgres runtime authority and unresolved-domain gates.
- Development: pause deep coding on coexistence assumptions; implement only after story acceptance criteria are updated and approved.
- QA: update regression strategy to treat Postgres as runtime baseline.

### Success criteria
- Updated planning artifacts explicitly reflect Supabase/Postgres-only runtime for production.
- Story acceptance criteria reflect runtime direction and risk controls.
- Risks are documented with concrete mitigations and validation gates.
- Sprint resumes only after artifact updates are approved.

## 8. Approval Request

Requested decision:
- Approve this change proposal and proceed with artifact rewrites.
- Request edits to specific story deltas or risks before approval.
