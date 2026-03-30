# Operator Kit Workflow Manual

This manual describes how to run each workflow type in the operator kit, what kind of input it expects, what artifacts it should produce, and one concrete example for each path.

Use this together with:

- [README.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/README.md)
- [docs/operator-kit-bmad-workflows.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/operator-kit-bmad-workflows.md)
- [docs/operator-kit-v3/index.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/operator-kit-v3/index.md)
- [_bmad-output/project-context.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/project-context.md)

## Common Input Rules

All workflows can receive:

- one or more context files through `CONTEXT="path.md"`
- the shared project rules from `_bmad-output/project-context.md`
- optional contracted mode with `PROFILE=contracted`
- optional workflow auto-advance with `APPROVAL=continue`

Recommended default:

```powershell
PROFILE=contracted
APPROVAL=questionnaire
EXECUTE=1
```

Preferred V3 entrypoint:

```powershell
make bmad-run WORKFLOW=<workflow-type> CONTEXT="<context-file>" EXECUTE=1 PROFILE=contracted
```

## Common Output Rules

When a step runs in contracted mode, the expected structured response contains:

- `status`
- `summary`
- `decisions`
- `risks`
- `input_artifacts`
- `output_artifacts`
- `approval_required`
- optional `next_command`

Each contracted execution produces:

1. a captured response message
2. zero or more materialized artifacts
3. one event log under `_bmad-output/operator-events/`

## 1. Agile Delivery Workflow

Use when:

- a story or batch already exists
- you want the normal `story -> dev -> review` loop

Input format:

- preferred: one story artifact under `_bmad-output/implementation-artifacts/`
- accepted: one approved planning artifact if you still need to create the story

Output format:

- story artifact
- implementation report
- review report
- event logs for each executed step

One-line workflow:

```powershell
make bmad-run WORKFLOW=agile CONTEXT="_bmad-output/implementation-artifacts/4-6a-batch-f-csp-report-only-and-hsts-gating.md" EXECUTE=1 PROFILE=contracted APPROVAL=stop
```

Manual sequence:

1. `make bmad-create-story CONTEXT="...planning-or-story-file..." EXECUTE=1 PROFILE=contracted`
2. `make bmad-dev-story CONTEXT="_bmad-output/implementation-artifacts/<story-file>.md" EXECUTE=1 PROFILE=contracted`
3. `make bmad-code-review CONTEXT="_bmad-output/implementation-artifacts/<story-file>.md" EXECUTE=1 PROFILE=contracted`

## 2. Batching Workflow

Use when:

- the task is too large for one story
- you need staged execution with reviewable slices

Input format:

- one batch anchor or planning artifact that describes the larger scope

Output format:

- epics/stories planning output
- sprint planning output
- story artifact for the current batch
- implementation and review reports

One-line workflow:

```powershell
make bmad-run WORKFLOW=batching CONTEXT="docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md" EXECUTE=1 PROFILE=contracted APPROVAL=stop
```

Manual sequence:

1. `make bmad-create-epics-and-stories CONTEXT="..." EXECUTE=1`
2. `make bmad-sprint-planning CONTEXT="..." EXECUTE=1`
3. `make bmad-create-story CONTEXT="..." EXECUTE=1 PROFILE=contracted`
4. `make bmad-dev-story CONTEXT="_bmad-output/implementation-artifacts/<story-file>.md" EXECUTE=1 PROFILE=contracted`
5. `make bmad-code-review CONTEXT="_bmad-output/implementation-artifacts/<story-file>.md" EXECUTE=1 PROFILE=contracted`

## 3. Greenfield Workflow

Use when:

- there is no system yet
- you need requirements-to-plan preparation

Input format:

- one discovery or requirements document under `docs/discovery/`

Output format:

- product brief
- PRD
- architecture
- epics and stories
- sprint planning artifacts
- event logs for each step

One-line workflow:

```powershell
make bmad-run WORKFLOW=greenfield CONTEXT="docs/discovery/new-product-requirements.md" EXECUTE=1 APPROVAL=stop
```

Manual sequence:

1. `make bmad-create-product-brief CONTEXT="docs/discovery/new-product-requirements.md" EXECUTE=1`
2. `make bmad-create-prd CONTEXT="docs/discovery/new-product-requirements.md" EXECUTE=1`
3. `make bmad-create-architecture CONTEXT="docs/discovery/new-product-requirements.md" EXECUTE=1`
4. `make bmad-create-epics-and-stories CONTEXT="docs/discovery/new-product-requirements.md" EXECUTE=1`
5. `make bmad-check-implementation-readiness CONTEXT="docs/discovery/new-product-requirements.md" EXECUTE=1`
6. `make bmad-sprint-planning CONTEXT="docs/discovery/new-product-requirements.md" EXECUTE=1`

## 4. Brownfield Workflow

Use when:

- the codebase already exists
- you need to understand and stabilize it before changing behavior

Input format:

- one brownfield anchor file
- this can be a README, a current-state doc, or a scoped area document

Output format:

- current-state documentation
- project-context or architecture refresh
- planning outputs for the next sprint
- event logs

One-line workflow:

```powershell
make bmad-run WORKFLOW=brownfield CONTEXT="docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md" EXECUTE=1 PROFILE=contracted APPROVAL=stop
```

Manual sequence:

1. `make bmad-document-project CONTEXT="docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md" EXECUTE=1 PROFILE=contracted`
2. `make bmad-generate-project-context CONTEXT="docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md" EXECUTE=1`
3. `make bmad-create-architecture CONTEXT="docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md" EXECUTE=1`
4. `make bmad-create-epics-and-stories CONTEXT="docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md" EXECUTE=1`
5. `make bmad-check-implementation-readiness CONTEXT="docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md" EXECUTE=1`
6. `make bmad-sprint-planning CONTEXT="docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md" EXECUTE=1`

## 5. Build-From-Pieces Workflow

Use when:

- you are assembling a new solution from existing repos, modules, or patterns

Input format:

- one integration anchor doc that explains the source pieces and target outcome

Output format:

- PRD
- architecture
- epics/stories
- sprint planning
- event logs

One-line workflow:

```powershell
make bmad-run WORKFLOW=build-from-pieces CONTEXT="docs/discovery/integration-anchor.md" EXECUTE=1 APPROVAL=stop
```

Manual sequence:

1. `make bmad-document-project CONTEXT="docs/discovery/integration-anchor.md" EXECUTE=1 PROFILE=contracted`
2. `make bmad-generate-project-context CONTEXT="docs/discovery/integration-anchor.md" EXECUTE=1`
3. `make bmad-create-prd CONTEXT="docs/discovery/integration-anchor.md" EXECUTE=1`
4. `make bmad-create-architecture CONTEXT="docs/discovery/integration-anchor.md" EXECUTE=1`
5. `make bmad-create-epics-and-stories CONTEXT="docs/discovery/integration-anchor.md" EXECUTE=1`
6. `make bmad-check-implementation-readiness CONTEXT="docs/discovery/integration-anchor.md" EXECUTE=1`
7. `make bmad-sprint-planning CONTEXT="docs/discovery/integration-anchor.md" EXECUTE=1`

## 6. Quick Workflow

Use when:

- the task is small and low-risk
- no big architecture move is needed

Input format:

- one small-change anchor file or a directly scoped requirement

Output format:

- quick spec
- quick implementation output
- event logs

One-line workflow:

```powershell
make bmad-run WORKFLOW=quick CONTEXT="docs/discovery/small-change.md" EXECUTE=1 APPROVAL=stop
```

Manual sequence:

1. `make bmad-quick-spec CONTEXT="docs/discovery/small-change.md" EXECUTE=1`
2. `make bmad-quick-dev CONTEXT="docs/discovery/small-change.md" EXECUTE=1`

## 7. Course-Correction Workflow

Use when:

- review exposed bad decomposition
- architecture assumptions are now wrong
- the sprint path needs a reset

Input format:

- one drift, review, or failure anchor document

Output format:

- correction memo
- event log
- next recommended command for recovery

One-line workflow:

```powershell
make bmad-run WORKFLOW=correct-course CONTEXT="_bmad-output/operator-artifacts/4-6a-review-report.md" EXECUTE=1 PROFILE=contracted APPROVAL=stop
```

Manual sequence:

1. `make bmad-correct-course CONTEXT="_bmad-output/operator-artifacts/4-6a-review-report.md" EXECUTE=1 PROFILE=contracted`

## 8. Review Loop Example For Batch F

Current input:

- [batch-f-csp-and-hsts-current-state.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md)

Expected progression:

1. create story from the current-state doc
2. implement the story
3. review the story
4. if review fails, loop back to implementation with the review report as input

Example:

```powershell
make bmad-create-story CONTEXT="docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md" EXECUTE=1 PROFILE=contracted
make bmad-dev-story CONTEXT="_bmad-output/implementation-artifacts/4-6a-batch-f-csp-report-only-and-hsts-gating.md" EXECUTE=1 PROFILE=contracted
make bmad-code-review CONTEXT="_bmad-output/implementation-artifacts/4-6a-batch-f-csp-report-only-and-hsts-gating.md" EXECUTE=1 PROFILE=contracted
```

## Approval Mode

Workflow sets now accept:

- `APPROVAL=questionnaire`
  Presents an in-terminal approval questionnaire and continues immediately if you approve.

- `APPROVAL=stop`
  Persists the workflow session and exits after a contracted step reports `approval_required=true`.

- `APPROVAL=continue`
  Continues chaining even when the step asked for an approval gate.

Use `APPROVAL=questionnaire` as the default for interactive supervision.
Use `APPROVAL=stop` when you explicitly want to pause and review outside the terminal.

## Workflow Sessions And Resume

Every executed workflow stores a session JSON under `_bmad-output/operator-workflows/`.

The terminal prints:

- `session_id`
- `session_path`
- current progress

To resume an interrupted or pending-approval workflow:

```powershell
make bmad-resume RESUME="<session-id-or-json-path>" EXECUTE=1 PROFILE=contracted
```

The same resume path also works through the unified entrypoint:

```powershell
make bmad-run RESUME="<session-id-or-json-path>" EXECUTE=1 PROFILE=contracted
```

If the workflow predates session persistence, bootstrap a session from the last event log first:

```powershell
make bmad-sessionize WORKFLOW=<workflow-type> RESUME_EVENT="_bmad-output/operator-events/<event-file>.json" PROFILE=contracted
```
