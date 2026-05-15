# Command Center, Evolution Radar, and Decision Matrix Sprint Plan

Date: 2026-05-09
Scope: command-center-radar-decision-matrix
Primary inputs:
- _bmad-output/planning-artifacts/prd.md
- _bmad-output/planning-artifacts/command-center-radar-decision-matrix-architecture.md
- _bmad-output/planning-artifacts/command-center-radar-decision-matrix-epics-and-stories.md
- _bmad-output/planning-artifacts/implementation-readiness-report-2026-05-09-rerun.md

## Planning Basis

This sprint plan assumes implementation readiness is READY and sequences the work in the approved brownfield priority order:

1. authoritative facts and shared score state
2. append-only history and version traceability
3. synchronous Radar projections
4. asynchronous Command Center and Decision Matrix projections
5. migration/backfill and parity validation
6. projection recovery, retry, and rebuild operations

The architecture baseline remains binding. Appendix A, Appendix B, and Appendix C are normative constraints for implementation, review, and release gates.

## Normative Constraints (Must Hold in Every Wave)

- Appendix A (projection runs and rebuild generations): every projection execution is logged, immutable projection history uses append_only_replacement_generation, and failed runs never supersede a successful generation.
- Appendix B (frozen v1 contracts): endpoint paths, response fields, field types, and semantics for Command Center, Radar, and Decision Matrix stay preserved during all backend refactors.
- Appendix C (backfill and reconstruction): assignment seed source, seed order, compatibility identifier preservation, and display-field reconstruction rules are mandatory for migration and parity checks.

## Story Execution Order (Authoritative)

1. Story 1.1 Add Authoritative Assignment Fact Persistence
2. Story 1.2 Persist Current Measures and Checkpoints as Shared Facts
3. Story 1.3 Introduce Shared Assignment Score State for All Three Views
4. Story 2.1 Append Measurement and Checkpoint History from Day One
5. Story 2.2 Append Immutable Score History with Version Metadata
6. Story 2.3 Preserve Lineage Contracts for Downstream Projection Consumers
7. Story 3.1 Build Assignment Radar Current and History Projections
8. Story 3.2 Enforce Synchronous Assignment-Scoped Radar Refresh
9. Story 3.3 Add Product-Level Radar Trend Aggregation
10. Story 4.1 Build Command Center Assignment Projection Serving
11. Story 4.2 Build Decision Matrix Assignment Projection Serving
12. Story 4.3 Add Assignment-Scoped Async Refresh for Command Center and Decision Matrix
13. Story 5.1 Backfill Current Facts and History from JSON Sources
14. Story 5.2 Seed Assignment Score State and Projection Rows During Backfill
15. Story 5.3 Validate Post-Backfill Parity Against Frozen v1 Contracts
16. Story 6.1 Persist Projection Run Logging and Failure States
17. Story 6.2 Add Targeted Retry and Rebuild Operations from Facts Plus History
18. Story 6.3 Add Automated Validation for Refresh, Retry, and Recovery Paths

## Wave Plan (Safe Brownfield Sequencing)

### Wave 1 - Authoritative Facts and Shared Score State

Purpose: establish write-authoritative facts without changing frozen endpoint contracts.

Stories:
- 1.1
- 1.2 (depends on 1.1)
- 1.3 (depends on 1.2)

Primary dependencies:
- Existing service boundaries remain intact (routes thin, services orchestration, repositories persistence).
- Fact repositories introduced before projection-serving changes.

Validation gate G1:
- Writes persist to product_assignments, metric_measures_current, journey_checkpoints_current, assignment_score_state.
- Services can resolve latest state from fact repositories without relying on projections as source of truth.
- Contract-preservation checkpoint C1: spot-check all three endpoint families still conform to Appendix B field map.

### Wave 2 - Append-Only History and Version Traceability

Purpose: make lineage immutable and version-aware before projection behavior is expanded.

Stories:
- 2.1 (depends on 1.2)
- 2.2 (depends on 1.3 and 2.1)
- 2.3 (depends on 2.1 and 2.2)

Primary dependencies:
- Current-state facts available from Wave 1.
- Version metadata available for scoring and projection formulas.

Validation gate G2:
- Every meaningful mutation appends history rows; no in-place history rewrite.
- Score history rows carry scoring_rule_version, projection_formula_version, calculated_at, source_effective_at.
- Contract-preservation checkpoint C2: API responses remain unchanged while lineage stays internal.

### Wave 3 - Synchronous Radar Projections

Purpose: switch Radar serving to dedicated projections while meeting the 1-second assignment freshness target.

Stories:
- 3.1 (depends on 1.3 and 2.3)
- 3.2 (depends on 3.1)
- 3.3 (depends on 3.1, can run in parallel after 3.2 start)

Primary dependencies:
- Assignment score state and lineage available.
- Projection history generation rules aligned with Appendix A.

Validation gate G3:
- Radar endpoint serves axisScores from radar_axis_projection_current with Appendix B mappings (axisKey, axisLabel, axisSub, numeric compatibility, insight behavior).
- Synchronous refresh path keeps assignment Radar freshness within <= 1 second target under normal operations.
- Contract-preservation checkpoint C3: Radar response shape and context fields preserved exactly as Appendix B.

### Wave 4 - Asynchronous Command Center and Decision Matrix Projections

Purpose: move operational and portfolio reads to async assignment projections with idempotent post-write refresh.

Stories:
- 4.1 (depends on 1.3, 2.3)
- 4.2 (depends on 1.3, 2.3)
- 4.3 (depends on 4.1 and 4.2)

Primary dependencies:
- Radar synchronous path from Wave 3 must remain unaffected.
- Async projection jobs are assignment-scoped and replayable.

Validation gate G4:
- Command Center and Decision Matrix endpoints serve projection-backed rows and preserve frozen v1 behavior.
- decision_matrix_status remains helper-only, never authoritative workflow state.
- Latency targets achieved in normal operations: Command Center <= 15 seconds, Decision Matrix <= 60 seconds.
- Contract-preservation checkpoint C4: Command Center list/detail/timeline and Decision Matrix field families match Appendix B.

### Wave 5 - Migration/Backfill and Parity Validation

Purpose: migrate JSON-backed data into fact/history/projection model with auditable lineage and frozen contract parity.

Stories:
- 5.1 (depends on Waves 1-4 baseline availability)
- 5.2 (depends on 5.1)
- 5.3 (depends on 5.2)

Primary dependencies:
- Seed sources and reconstruction rules fixed by Appendix C.
- Projection families already working for current writes.

Migration/backfill checkpoints:
- M1 Source fidelity: product_assignments seeded from enrollments.json according to Appendix C.1 mapping.
- M2 Seed order: enforce Appendix C.2 order (assignments -> current facts -> score state -> history seed_backfill -> projection rebuild run log).
- M3 Compatibility reconstruction: Appendix C.3 read-time reconstruction for name, initials, programName, plan, mentorName, protocol fields, axis fields.
- M4 Seed lineage audit: change_type = seed_backfill rows and projection_run_log scope_type = seed_backfill are queryable.

Validation gate G5:
- Post-backfill parity comparison across Command Center, Radar, and Decision Matrix against Appendix B contract map.
- Any field/type/semantic mismatch is release-blocking.

### Wave 6 - Projection Recovery, Retry, and Rebuild Operations

Purpose: harden operational reliability after migration and projection cutover.

Stories:
- 6.1 (depends on Waves 3-5 projection execution paths)
- 6.2 (depends on 6.1)
- 6.3 (depends on 6.2)

Primary dependencies:
- Projection refresh/rebuild operations already present from Waves 3-5.
- Append-only replacement-generation semantics must remain intact.

Validation gate G6:
- projection_run_log captures lifecycle, failure class, retry linkage, generation linkage, and version lineage.
- Targeted retry and rebuild replay from facts plus history without fact rollback.
- Immutable history projections corrected only through higher rebuild_generation linked to successful run ids.
- Automated tests cover refresh, retry, rebuild, and contract guard behavior.

## Dependency Map (Story-Level)

- 1.1 -> none
- 1.2 -> 1.1
- 1.3 -> 1.2
- 2.1 -> 1.2
- 2.2 -> 1.3, 2.1
- 2.3 -> 2.1, 2.2
- 3.1 -> 1.3, 2.3
- 3.2 -> 3.1
- 3.3 -> 3.1
- 4.1 -> 1.3, 2.3
- 4.2 -> 1.3, 2.3
- 4.3 -> 4.1, 4.2
- 5.1 -> 1.1, 1.2, 1.3, 2.1, 2.2, 2.3
- 5.2 -> 5.1, 3.1, 4.1, 4.2
- 5.3 -> 5.2
- 6.1 -> 3.1, 3.2, 4.3, 5.2
- 6.2 -> 6.1
- 6.3 -> 6.2

## Contract-Preservation Checkpoints

- C0 Pre-wave baseline capture: freeze reference payload snapshots for all frozen endpoints.
- C1 After Wave 1: facts introduced, no API contract drift.
- C2 After Wave 2: lineage added, no API contract drift.
- C3 After Wave 3: Radar projection cutover preserves Appendix B field mapping.
- C4 After Wave 4: Command Center and Decision Matrix cutover preserve Appendix B list/detail/timeline/filter semantics.
- C5 After Wave 5: parity validation is pass/fail gate for release.
- C6 After Wave 6: recovery paths do not alter frozen response contracts.

## Recommended Slice Boundaries

- Slice A (write model foundation): 1.1 + 1.2 + 1.3 in backend repositories/services, no endpoint shape changes.
- Slice B (lineage foundation): 2.1 + 2.2 + 2.3 with queryable audit lineage and immutable guarantees.
- Slice C (Radar current path): 3.1 + 3.2 for assignment-level synchronous refresh and <= 1s target.
- Slice D (Radar product trend): 3.3 as independent aggregate-history slice after Slice C is stable.
- Slice E (portfolio projections): 4.1 + 4.2 + 4.3 with async assignment job semantics and latency targets.
- Slice F (migration cutover): 5.1 + 5.2 + 5.3 with Appendix C seed controls and Appendix B parity enforcement.
- Slice G (operational hardening): 6.1 + 6.2 + 6.3 for logging, retry, rebuild, and automated resilience checks.

## Exit Criteria for Sprint Plan Completion

- All waves satisfy their validation gates.
- Appendix A/B/C checkpoints are recorded and approved at each wave boundary.
- Frozen v1 contracts and standardized error envelope remain unchanged.
- Migration parity is complete and release blockers are resolved before operational hardening sign-off.
