# BMAD Operator Workflows

This guide translates the BMAD workflows installed in this repository into practical operator flows for the local kit.

Use this document together with:

- [README.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/README.md)
- [docs/operator-kit-workflow-manual.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/operator-kit-workflow-manual.md)
- [_bmad-output/project-context.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/project-context.md)
- [ops/get_bmad_status.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/ops/get_bmad_status.py)
- [ops/run_bmad_command.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/ops/run_bmad_command.py)
- [ops/run_bmad_phase.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/ops/run_bmad_phase.py)

## Core Rule

The operator kit uses this priority order:

1. Story artifacts in `_bmad-output/implementation-artifacts/`
2. Project rules in `_bmad-output/project-context.md`
3. Local execution state in `ops/state/workflow_state.local.json`
4. Optional summary trackers such as `sprint-status.yaml`

## Contracted Production-Line Mode

The operator kit now supports a contract-driven execution mode for selected BMAD commands.

In this mode:

1. a command contract defines the expected inputs and output artifact types
2. the prompt requires a structured JSON response
3. the runner validates that response
4. declared artifacts are materialized
5. one event log is written under `_bmad-output/operator-events/`

Use this to keep execution precise without creating document flood.

Current core contracted commands:

- `bmad-document-project`
- `bmad-generate-project-context`
- `bmad-create-product-brief`
- `bmad-create-prd`
- `bmad-create-architecture`
- `bmad-create-epics-and-stories`
- `bmad-check-implementation-readiness`
- `bmad-sprint-planning`
- `bmad-create-story`
- `bmad-dev-story`
- `bmad-code-review`
- `bmad-quick-spec`
- `bmad-quick-dev`
- `bmad-correct-course`

Use `PROFILE=contracted` to force this mode, or omit it and let the runner use `auto`.

## Default Agile Delivery Loop

Use this as the standard implementation loop for work that has already been planned.

BMAD sequence:

1. `bmad-create-story`
2. `bmad-dev-story`
3. `bmad-code-review`
4. `bmad-dev-story` again only if review fails
5. optional `bmad-retrospective` at epic end

Operator kit interpretation:

1. Create or update one story artifact.
2. Set the local batch state to allow `story` or `dev`.
3. Run the phase locally with `ops/run_bmad_phase.py`.
4. Move the story to `review`.
5. If approved, mark the story `done`.
6. If not approved, set `review` to `changes_requested` and run `fix_loop`.

Use when:

- planning already exists
- scope is already bounded
- you want normal sprint execution

Operator-kit calls:

```powershell
make bmad-flow-agile CONTEXT="_bmad-output/implementation-artifacts/<story-file>.md"
```

Or step by step:

```powershell
make bmad-create-story CONTEXT="_bmad-output/implementation-artifacts/<story-file>.md"
make bmad-dev-story CONTEXT="_bmad-output/implementation-artifacts/<story-file>.md"
make bmad-code-review CONTEXT="_bmad-output/implementation-artifacts/<story-file>.md"
```

Recommended contracted version:

```powershell
make bmad-create-story CONTEXT="_bmad-output/implementation-artifacts/<story-file>.md" EXECUTE=1 PROFILE=contracted
make bmad-dev-story CONTEXT="_bmad-output/implementation-artifacts/<story-file>.md" EXECUTE=1 PROFILE=contracted
make bmad-code-review CONTEXT="_bmad-output/implementation-artifacts/<story-file>.md" EXECUTE=1 PROFILE=contracted
```

## How To Break Work Into Batches

Use BMAD batching when a task is too large to be implemented and reviewed safely as one story.

Recommended batch rules:

- one deployable concern per batch
- one contract boundary per batch when possible
- one dominant risk per batch
- one reviewable diff size
- do not mix unrelated frontend, backend, infra, and docs changes unless the contract requires it

Preferred decomposition order:

1. contract and environment boundary
2. backend/service boundary
3. frontend integration boundary
4. operator/documentation boundary
5. release evidence or deploy boundary

BMAD sequence:

1. `bmad-create-epics-and-stories`
2. `bmad-sprint-planning`
3. repeated story loop:
   - `bmad-create-story`
   - `bmad-dev-story`
   - `bmad-code-review`

Use when:

- a feature spans multiple modules
- a release requires staged hardening
- you need explicit review gates between slices

Operator-kit calls:

```powershell
make bmad-flow-batching CONTEXT="_bmad-output/implementation-artifacts/<batch-anchor>.md"
```

## Greenfield Project Workflow

Use this when building a project from zero.

Recommended BMAD path:

1. optional discovery:
   - `bmad-brainstorming`
   - `bmad-market-research`
   - `bmad-domain-research`
   - `bmad-technical-research`
2. `bmad-create-product-brief`
3. `bmad-create-prd`
4. optional `bmad-create-ux-design`
5. `bmad-create-architecture`
6. `bmad-create-epics-and-stories`
7. `bmad-check-implementation-readiness`
8. `bmad-sprint-planning`
9. implementation loop:
   - `bmad-create-story`
   - `bmad-dev-story`
   - `bmad-code-review`

Artifacts expected:

- product brief
- PRD
- UX plan if applicable
- architecture
- epics and stories
- readiness report
- story artifacts

Use when:

- there is no codebase yet
- there is no existing architecture to inherit
- scope and constraints still need to be shaped

Operator-kit calls:

```powershell
make bmad-flow-greenfield CONTEXT="docs/discovery/<requirements-file>.md"
```

## Brownfield Refactor Workflow

Use this when the project already exists and you need to refactor or stabilize it safely.

Recommended BMAD path:

1. `bmad-document-project`
2. `bmad-generate-project-context`
3. optional `bmad-technical-research`
4. choose one path:
   - narrow refactor: `bmad-quick-dev` or `bmad-quick-dev-new-preview`
   - broad refactor: `bmad-create-architecture` then `bmad-create-epics-and-stories`
5. if using broad refactor:
   - `bmad-check-implementation-readiness`
   - `bmad-sprint-planning`
   - normal story loop
6. if implementation reveals wrong scope:
   - `bmad-correct-course`

Use when:

- architecture exists but needs correction
- you must preserve an existing system
- you need to document before changing
- refactor risk is higher than feature risk

Operator-kit calls:

```powershell
make bmad-flow-brownfield CONTEXT="<brownfield-anchor-file>"
```

Recommended contracted entry:

```powershell
make bmad-document-project CONTEXT="<brownfield-anchor-file>" EXECUTE=1 PROFILE=contracted
```

## Build A Project From Pieces Of Other Projects

Use this when reusing code, concepts, patterns, or modules from other repositories.

Recommended BMAD path:

1. run `bmad-document-project` on the source projects or source modules
2. run `bmad-generate-project-context` on the target project
3. optional `bmad-technical-research` if integration risk is non-trivial
4. `bmad-create-prd`
5. `bmad-create-architecture`
6. `bmad-create-epics-and-stories`
7. `bmad-check-implementation-readiness`
8. `bmad-sprint-planning`
9. run the story loop batch by batch

Primary design rule:

- reuse concepts and well-bounded pieces
- do not copy undocumented assumptions across repos
- normalize contracts before implementation
- prefer adapter boundaries over direct transplant

Use when:

- you are combining proven components from multiple projects
- you want a new product assembled from known pieces
- integration and contract clarity matter more than raw coding speed

Operator-kit calls:

```powershell
make bmad-flow-build-from-pieces CONTEXT="<integration-anchor-file>"
```

## Small Change / Quick Flow Workflow

Use this when the task is genuinely small, local, and low-risk.

Recommended BMAD path:

1. `bmad-quick-spec` if you want a lightweight spec first
2. `bmad-quick-dev` for a standard quick flow
3. or `bmad-quick-dev-new-preview` for a unified end-to-end run

Use when:

- the task fits one bounded change
- existing patterns are already well established
- no major architecture movement is required

Do not use when:

- a PRD or architecture decision is still missing
- the task crosses multiple risky boundaries
- the work must be split into multiple reviewable batches

Operator-kit calls:

```powershell
make bmad-flow-quick CONTEXT="<small-change-anchor-file>"
```

## Course Correction Workflow

Use this when the implementation path is no longer valid.

Recommended BMAD path:

1. `bmad-correct-course`
2. then one or more of:
   - update PRD
   - redo architecture
   - regenerate epics/stories
   - rerun readiness
   - restart sprint planning

Use when:

- review exposes scope drift
- architecture assumptions are wrong
- stories were decomposed badly
- multiple batches are now invalid

Operator-kit calls:

```powershell
make bmad-flow-correct-course CONTEXT="<course-correction-anchor-file>"
```

## Operator Kit Mapping

Translate BMAD into the local kit like this:

| BMAD intent | Operator-kit call | Typical local phase |
|---|---|---|
| planning from requirements | `make bmad-route WORKFLOW=plan_solution BATCH=A` | `route` |
| standard story cycle | `make bmad-story`, `make bmad-dev`, `make bmad-review` | `story`, `dev`, `review` |
| review follow-up | `make bmad-fix WORKFLOW=fix_loop BATCH=<batch>` | `fix` |
| artifact-first status check | `make bmad-status` | status retrieval |
| direct BMAD command execution | `make bmad-<command>` | command preview or execute |
| correction after drift | `make bmad-correct-course CONTEXT="<file>"` | anytime |

## Direct BMAD Command Targets

These make targets call the BMAD skill locally through `ops/run_bmad_command.py`.

All command targets default to preview mode. To actually execute them through local `codex`, pass `EXECUTE=1`.
To force the structured production-line path, also pass `PROFILE=contracted`.

Examples:

```powershell
make bmad-document-project CONTEXT="README.md"
make bmad-create-prd CONTEXT="docs/discovery/client-alpha-requirements.md"
make bmad-code-review CONTEXT="_bmad-output/implementation-artifacts/4-4b-batch-d-domain-contract-correction.md"
make bmad-code-review CONTEXT="_bmad-output/implementation-artifacts/4-4b-batch-d-domain-contract-correction.md" EXECUTE=1
make bmad-create-story CONTEXT="docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md" EXECUTE=1 PROFILE=contracted
```

Available direct command targets:

- `make bmad-help`
- `make bmad-brainstorming`
- `make bmad-market-research`
- `make bmad-domain-research`
- `make bmad-technical-research`
- `make bmad-create-product-brief`
- `make bmad-create-prd`
- `make bmad-create-ux-design`
- `make bmad-create-architecture`
- `make bmad-create-epics-and-stories`
- `make bmad-check-implementation-readiness`
- `make bmad-sprint-planning`
- `make bmad-sprint-status`
- `make bmad-create-story`
- `make bmad-validate-story`
- `make bmad-dev-story`
- `make bmad-code-review`
- `make bmad-retrospective`
- `make bmad-document-project`
- `make bmad-generate-project-context`
- `make bmad-quick-spec`
- `make bmad-quick-dev`
- `make bmad-quick-dev-new-preview`
- `make bmad-correct-course`

## Workflow Set Targets

These are now state-aware workflow runners. They preview or execute an ordered BMAD sequence, consume event-log outputs, and can stop at approval gates.

- `make bmad-flow-agile CONTEXT="<story-file>"`
- `make bmad-flow-batching CONTEXT="<batch-anchor-file>"`
- `make bmad-flow-greenfield CONTEXT="<requirements-file>"`
- `make bmad-flow-brownfield CONTEXT="<brownfield-anchor-file>"`
- `make bmad-flow-build-from-pieces CONTEXT="<integration-anchor-file>"`
- `make bmad-flow-quick CONTEXT="<small-change-anchor-file>"`
- `make bmad-flow-correct-course CONTEXT="<course-correction-anchor-file>"`

Useful workflow flags:

- `PROFILE=contracted`
- `APPROVAL=stop`
- `APPROVAL=continue`

## Suggested Decision Tree

Start with `bmad-help` when unclear.

Then use this routing:

1. New product or major new initiative:
   - Greenfield workflow
2. Existing system needs understanding first:
   - Brownfield refactor workflow
3. Existing project, already planned, just execute next story:
   - Agile delivery loop
4. Small local change:
   - Quick flow workflow
5. Work assembled from multiple previous projects:
   - Build-from-pieces workflow
6. Current plan is breaking down:
   - Course correction workflow

## Anti-Patterns

Avoid:

- using `quick-dev` for architecture-heavy work
- creating broad stories that mix multiple review boundaries
- trusting a stale summary tracker over story artifacts
- treating `workflow_state.local.json` as business truth
- skipping review because the implementation "looks done"
- creating documentation layers that duplicate story truth

## Recommended Minimal Deliverables

To stay robust without documentation flood, keep only:

- `project-context.md`
- core architecture and contract docs
- one active sprint summary if useful
- story artifacts in `implementation-artifacts`
- targeted validation evidence when risk justifies it
- deploy and release docs only at the release boundary

## Event Log Discipline

Treat `_bmad-output/operator-events/` as the operator execution ledger.

- story artifacts remain the implementation truth
- event logs record command-level execution truth
- planning/current-state docs remain upstream inputs

That separation keeps Agile flow, SDD, and operator traceability aligned.
