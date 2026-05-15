---
stepsCompleted: []
inputDocuments:
  - _bmad-output/planning-artifacts/research/technical-command-center-radar-decision-matrix-data-architecture-research-2026-05-08.md
  - docs/architecture/platform_architecture_operational_model.md
  - docs/mvp-mentoria/frontend-integration-architecture.md
  - docs/mvp-mentoria/contracts-freeze-v1.md
  - docs/mvp-mentoria/contracts-command-center.md
  - docs/mvp-mentoria/contracts-radar.md
  - docs/mvp-mentoria/contracts-renewal-matrix.md
  - docs/mvp-mentoria/naming-and-domain-notes.md
workflowType: 'prd'
status: 'draft'
---

# Product Requirements Document - Command Center, Evolution Radar, and Decision Matrix

**Author:** dmene / GitHub Copilot
**Date:** 2026-05-09
**Document Type:** Minimum PRD baseline for architecture continuation

## 1. Purpose

This PRD converts the exploratory research note `_bmad-output/planning-artifacts/research/technical-command-center-radar-decision-matrix-data-architecture-research-2026-05-08.md` into a minimum decision baseline for three analytical surfaces:

- Command Center
- Evolution Radar
- Decision Matrix

The goal is not to finalize every implementation detail. The goal is to make the product requirements and architecture-driving constraints explicit enough that architecture work can proceed without reopening already answered questions.

## 2. Scope

This PRD covers:

- product behavior and data expectations for Command Center, Evolution Radar, and Decision Matrix
- freshness, history, versioning, and scalability requirements that materially shape storage and projection design
- what is decided now versus what remains open for architecture design

This PRD does not redefine frozen v1 API contracts. All architecture work must preserve the existing contract boundaries in `docs/mvp-mentoria/contracts-freeze-v1.md` and the current Command Center, Radar, and Decision Matrix contracts.

## 3. Product Context

The platform already treats Command Center, Evolution Radar, and Decision Matrix as core analytical views layered on top of the mentoring product. These views are read-oriented, calculation-heavy, and operationally important. The exploratory research established that the current relational baseline is not enough by itself because the product also depends on:

- measurement facts
- checkpoint facts
- derived scores
- historical evolution
- view-specific read models

This PRD locks the product baseline needed to decide how those data classes must be stored and served.

## 4. Decision Baseline from Section 11 Answers

| Question | Decision | PRD implication |
| --- | --- | --- |
| Q1 | History capture from day one | History is not a later optimization. Measurement and checkpoint changes must be traceable from initial implementation. |
| Q2 | Student Radar updates must become visible to the mentor with at least 1 second tolerance | Radar update propagation must support near-real-time visibility for the same enrollment context. |
| Q3 | `decision_matrix_status` is only a convenience and can be ignored as workflow state | Decision Matrix status is a cache/helper only, not authoritative business workflow state. |
| Q4 | Radar needs historical data for student progression, mentor follow-up, and product maturity over time | Radar history is a first-class feature, not a reporting nice-to-have. Historical and aggregate product views must be supported. |
| Q5 | Anomalies are temporary visual hints; important but not urgent | Command Center anomalies matter in UX, but anomaly durability is not a blocking architecture driver for this phase. |
| Q6 | Old outputs remain unchanged after scoring-rule changes, but each output must show which rule version produced it | Derived outputs require version traceability and historical immutability. |
| Q7 | Dedicated projection tables are required now because load has increased substantially | Live-query-only architecture is insufficient. Projection-backed serving is required for scale. |

## 5. Product Requirements

### 5.1 Cross-View Requirements

1. The system must preserve the frozen v1 API contracts for Command Center, Evolution Radar, and Decision Matrix.
2. The system must support history capture from the first production-ready implementation of measurement and checkpoint data, not in a later migration phase.
3. The system must preserve historical analytical outputs even when scoring rules change later.
4. Every derived analytical output that depends on scoring logic must expose or be traceable to the rule version used to calculate it.
5. The system must scale beyond current load by serving the three views from dedicated read-optimized projections instead of relying only on expensive live aggregation queries.

### 5.2 Command Center Requirements

1. Command Center must remain an operational mentor view focused on exception-based follow-up.
2. Command Center must continue to support enrollment-level summary data required by the frozen contract, including urgency, days left, progress, engagement, checkpoints, and anomaly-oriented cues.
3. Command Center must consume projection-backed enrollment summaries so list and detail reads remain operational under increased load.
4. Command Center anomaly indicators may be implemented as temporary or computed visual hints in this phase; they do not need to become durable business records before architecture work continues.
5. Command Center must remain compatible with existing mentor vocabulary and stable contract naming.

### 5.3 Evolution Radar Requirements

1. Evolution Radar must support baseline, current, and projected values by axis or pillar for an enrollment.
2. Evolution Radar must support historical comparison as a first-class capability from the first architecture iteration.
3. From the student perspective, Radar must show progression during the period that the student is consuming the product.
4. From the mentor perspective, Radar must show how each student performed over time.
5. From the product perspective, Radar must support how the product itself performed over time because pillar scores define product maturity.
6. When a student updates metrics on Radar View, the mentor-facing result for that enrollment must reflect the change with a target propagation tolerance of 1 second.
7. Radar history must not be destroyed or recomputed into different past outputs when future scoring rules change.

### 5.4 Decision Matrix Requirements

1. Decision Matrix must remain a portfolio prioritization view based on progress, engagement, quadrant logic, renewal reasoning, and related mentor actions.
2. Decision Matrix must be served from dedicated projection tables suitable for increased query volume.
3. The existing `decision_matrix_status` field may exist as a convenience cache or filter helper, but it must not be treated as the authoritative business state for Decision Matrix behavior.
4. Decision Matrix outputs affected by scoring rules or classification rules must retain the version metadata required to explain historical results.

## 6. Architectural Requirements

### 6.1 Required Data Capabilities

1. The architecture must distinguish between authoritative transactional facts, historical evidence, and disposable read projections.
2. Measurement facts and checkpoint facts must be represented in a way that supports both current-state serving and full day-one historical traceability.
3. The architecture must support dedicated projection tables for:
   - Command Center enrollment summaries
   - Radar axis and history views
   - Decision Matrix portfolio rows
4. Projection-serving design must be compatible with the current backend layering and stable API boundaries.

### 6.2 Freshness and Propagation

1. Radar updates for the same student enrollment must propagate to the mentor-visible view with a target tolerance of 1 second.
2. Architecture decisions for Radar must therefore support immediate or near-immediate projection refresh for the affected enrollment.
3. Command Center and Decision Matrix must also use projection-backed serving, but their exact latency budgets remain open as long as the architecture supports scalable near-real-time refresh patterns.

### 6.3 History and Immutability

1. Historical measurement and checkpoint evidence must be captured from day one.
2. Historical Radar outputs must remain explainable across time for student, mentor, and product views.
3. If scoring rules change, historical derived outputs must remain as originally produced rather than being silently rewritten.
4. The system must store sufficient metadata to identify which rule version and projection logic version produced each persisted output.

### 6.4 Versioning Requirements

At minimum, architecture must support version metadata equivalent to:

- scoring rule version used for score derivation
- projection formula version used for view output generation
- calculation timestamp
- effective or source time context for the output

The final physical schema may rename these fields, but this traceability requirement is mandatory.

## 7. Decided Now

The following are treated as decided requirements and should not be reopened during architecture exploration unless a blocking contradiction is found:

- History capture starts on day one.
- Radar requires historical data as a first-class feature.
- Radar student-to-mentor update visibility target is 1 second tolerance.
- Dedicated projection tables are required now, not later.
- `decision_matrix_status` is non-authoritative convenience state.
- Old analytical outputs remain immutable after scoring-rule changes.
- Every persisted derived output needs rule-version traceability.
- Command Center anomalies are important, but durable anomaly records are not required to unblock this phase.

## 8. Still Open

The following remain open architecture decisions:

1. Exact physical schema for current-state facts, history tables, and projection tables.
2. Whether history is modeled as append-only fact history, event-like records, snapshots, or a hybrid of these.
3. Exact refresh mechanism for projections, including whether Radar uses synchronous recompute, post-write projection, or another low-latency pattern.
4. Exact latency targets for Command Center and Decision Matrix beyond the requirement to use scalable projections.
5. Retention, rebuild, and backfill policy for Radar history and other projections.
6. Exact product-maturity aggregation rules for product-level Radar views.
7. Exact storage and lifecycle model for anomaly hints if they are later promoted from temporary cues into durable operational signals.

## 9. Non-Goals for This PRD

This PRD does not yet define:

- detailed database DDL
- queue or event-bus technology choices
- frontend redesign
- endpoint redesign or contract version bump
- implementation plan, epics, or sprint scope

## 10. Minimum Acceptance Baseline for Next Architecture Step

Architecture work may proceed when the proposed design shows all of the following:

1. A clear write/read boundary between transactional facts, historical evidence, and view projections.
2. A day-one history strategy for measurements and checkpoints.
3. A Radar-serving strategy that can meet the 1-second mentor visibility target for student updates.
4. Dedicated projection-table strategy for Command Center and Decision Matrix.
5. Output version-traceability strategy that preserves historical results after scoring-rule changes.
6. Explicit confirmation that stable v1 contracts remain intact.

## 11. Recommended Architecture Direction from This PRD

This PRD does not lock a full implementation design, but it does establish a minimum direction:

- normalized or authoritative current-state facts for core domain data
- history capture from day one for measurement and checkpoint evolution
- dedicated projection tables for Command Center, Evolution Radar, and Decision Matrix
- versioned derived outputs that remain historically stable

Any architecture proposal that omits one of those four elements should be treated as non-compliant with this baseline.