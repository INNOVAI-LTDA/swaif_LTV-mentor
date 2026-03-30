# Operator Kit V3 Artifact Model

## Purpose

Define the artifact taxonomy used by V3 so workflows can reason about inputs and outputs consistently.

## Artifact Categories

### Foundation Artifacts

- project context
- core architecture docs
- frozen contract docs

These provide stable project rules and should be read but not churned often.

### Planning Artifacts

- current-state docs
- product brief
- PRD
- architecture
- epics and stories
- sprint plan
- readiness report

These shape what implementation should do.

### Execution Artifacts

- story artifact
- implementation report
- review report
- correction memo

These represent the active build loop.

### Release Artifacts

- deploy checklists
- readiness evidence
- rollback notes
- smoke test evidence

These represent go-live and operational safety.

## Canonical Locations

Recommended layout:

- `_bmad-output/project-context.md`
- `_bmad-output/planning-artifacts/`
- `_bmad-output/implementation-artifacts/`
- `_bmad-output/operator-artifacts/`
- `_bmad-output/operator-events/`

## Promotion Rules

Artifact promotion should be deterministic where possible.

Examples:

- current-state doc -> create-story input
- story artifact -> dev-story input
- story artifact -> code-review input
- review report with changes requested -> correction input
- architecture + PRD + epics/stories -> readiness input

## Artifact Rules

- one artifact should have one dominant purpose
- avoid duplicating the same truth in multiple docs
- use event logs for execution state, not large markdown notes
- preserve human-readable markdown for planning and execution outputs

## V3 Naming Guidance

Use explicit names that make routing obvious.

Examples:

- `<scope>-current-state.md`
- `<scope>-prd.md`
- `<scope>-architecture.md`
- `<scope>-epics-and-stories.md`
- `<scope>-sprint-plan.md`
- `<story-slug>.md`
- `<story-slug>-implementation-report.md`
- `<story-slug>-review-report.md`
- `<scope>-correction-memo.md`

## Single Source Of Truth Guidance

- implementation status truth belongs to story artifacts plus event logs
- workflow state should be derived from artifacts and events where practical
- optional trackers should never override artifact truth
