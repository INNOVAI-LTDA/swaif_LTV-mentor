# BMAD Operator Kit

This repository includes a local BMAD operator kit for running a supervised development loop with `codex` from the terminal.

The kit is designed for:

- local execution from VSCode or a terminal
- artifact-first status tracking
- human-approved progression between `story`, `dev`, `review`, `fix`, and `done`
- minimal operational documentation instead of tracker sprawl

## Solution Overview

The operator kit treats `_bmad-output/implementation-artifacts/` as the single source of truth for execution status.

The operating model is:

1. Story artifacts define the current implementation truth.
2. The local operator state file controls which BMAD phase can run next.
3. Command contracts optionally define structured inputs, outputs, and artifact writers.
4. The phase runner or command runner selects the right BMAD command and prompt profile.
5. `codex` executes the selected phase locally.
6. The runner validates the structured response, writes any declared artifacts, and appends an event log.
7. The human operator decides whether to advance, fix, or stop.

Core files:

- `_bmad-output/project-context.md`: global engineering rules and constraints
- `_bmad-output/implementation-artifacts/`: story artifacts and release-side artifacts
- `ops/bmad_operator.py`: reusable operator core
- `ops/contracts/`: BMAD command contracts for structured production-line runs
- `ops/get_bmad_status.py`: artifact-first status report
- `ops/run_bmad_command.py`: local BMAD command runner
- `ops/run_bmad_phase.py`: local BMAD phase runner
- `ops/run_bmad_workflow.py`: state-aware workflow orchestrator for one-line workflow runs
- `ops/state/workflow_state.local.json`: local execution state
- `ops/prompts/`: prompt templates per workflow and phase
- `Makefile`: convenience commands
- `docs/operator-kit-bmad-workflows.md`: BMAD-recommended workflow playbooks for the operator kit
- `docs/operator-kit-workflow-manual.md`: step-by-step manual runs with input/output examples

## Prerequisites

- Python 3.13 or compatible Python 3 environment
- `codex` CLI installed and authenticated locally
- BMAD already installed in this repository under `_bmad/`
- A valid `_bmad-output/project-context.md`

Optional:

- `make`
- PowerShell
- bash

## Prepare

If this repository already has BMAD installed, preparation is lightweight:

1. Confirm `_bmad-output/project-context.md` exists.
2. Confirm `_bmad-output/implementation-artifacts/` contains your story artifacts.
3. Confirm `codex -h` works locally.
4. Create or update `ops/state/workflow_state.local.json` to reflect the active batch.

Recommended local state pattern:

```json
{
  "workflow": "story_loop",
  "current_batch": "D",
  "batches": {
    "D": {
      "route": "done",
      "map": "done",
      "story": "done",
      "dev": "done",
      "review": "locked"
    }
  }
}
```

## Install

No extra package install is required for the operator kit itself beyond Python and `codex`.

To validate the local Python tooling:

```powershell
python -m py_compile ops/run_bmad_phase.py ops/get_bmad_status.py ops/bmad_operator.py
python -m pytest ops/tests -q
```

## Configure

### 1. Artifact Truth

Story files under `_bmad-output/implementation-artifacts/` are the canonical execution truth.

Each story should expose at least:

- `# Story ...`
- `Status: ...`
- acceptance criteria
- validation steps

### 2. Local Operator State

`ops/state/workflow_state.local.json` is execution state, not business truth.

Use it to control:

- current batch
- allowed next phase
- whether `fix` is unlocked after a failed review

### 3. Context Files

The runner automatically includes `_bmad-output/project-context.md` if it exists.

You can inject extra context files with repeated `--context-file` arguments, for example:

```powershell
--context-file _bmad-output/implementation-artifacts/4-4b-batch-d-domain-contract-correction.md
```

### 4. Codex CLI

The runner uses local `codex exec` when `--execute` is passed.

If `codex` is not on `PATH`, set a different executable:

```powershell
--codex-bin C:\path\to\codex.exe
```

### 5. Prompt Profiles And Contracts

The command runner supports two execution styles:

- `plain`: the classic freeform BMAD prompt
- `contracted`: the prompt includes an explicit input/output contract and expects a structured JSON response

When `--prompt-profile auto` is used, the runner switches to `contracted` automatically for commands that have a contract under `ops/contracts/`.

The current contracted command set includes the core delivery commands plus the planning commands used by the workflow sets, including:

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

Each contracted run can:

- validate the structured response
- materialize declared output artifacts
- write an event log under `_bmad-output/operator-events/`
- infer the next recommended command

## Run

### Check Current Artifact Status

```powershell
python ops/get_bmad_status.py
```

Or:

```powershell
make bmad-status
```

This reports:

- current active artifact
- current status
- status counts
- active non-done artifacts
- planning/current-state inputs discovered outside the implementation ledger

### Dry Run a BMAD Phase

Example for a review on Batch D:

```powershell
python ops/run_bmad_phase.py `
  --workflow story_loop `
  --batch D `
  --phase review `
  --state ops/state/workflow_state.local.json `
  --context-file _bmad-output/implementation-artifacts/4-4b-batch-d-domain-contract-correction.md `
  --execute `
  --dry-run
```

This prints:

- the selected BMAD command
- the operator prompt
- the resolved context files
- the final execution prompt that would be sent to `codex`

### Execute a BMAD Phase Locally

```powershell
python ops/run_bmad_phase.py `
  --workflow story_loop `
  --batch D `
  --phase review `
  --state ops/state/workflow_state.local.json `
  --context-file _bmad-output/implementation-artifacts/4-4b-batch-d-domain-contract-correction.md `
  --execute
```

By default, the command executes locally through `codex` and leaves the state file unchanged.

If the underlying BMAD command has a contract, the phase runner also:

- captures the final response body
- validates the JSON contract response
- writes declared artifacts
- appends an event log

### Record the Outcome

If the review is approved:

```powershell
python ops/run_bmad_phase.py `
  --workflow story_loop `
  --batch D `
  --phase review `
  --state ops/state/workflow_state.local.json `
  --context-file _bmad-output/implementation-artifacts/4-4b-batch-d-domain-contract-correction.md `
  --execute `
  --state-result approved
```

If the review returns changes requested:

```powershell
python ops/run_bmad_phase.py `
  --workflow story_loop `
  --batch D `
  --phase review `
  --state ops/state/workflow_state.local.json `
  --context-file _bmad-output/implementation-artifacts/4-4b-batch-d-domain-contract-correction.md `
  --execute `
  --state-result changes_requested
```

### Run a Fix Loop

Once review is marked `changes_requested`:

```powershell
python ops/run_bmad_phase.py `
  --workflow fix_loop `
  --batch D `
  --phase fix `
  --state ops/state/workflow_state.local.json `
  --context-file _bmad-output/implementation-artifacts/4-4b-batch-d-domain-contract-correction.md `
  --execute
```

## Make Targets

- `make bmad-smoke`: local preflight plus route dry-run
- `make bmad-status`: current artifact-first status report
- `make bmad-route WORKFLOW=... BATCH=...`
- `make bmad-story WORKFLOW=... BATCH=...`
- `make bmad-dev WORKFLOW=... BATCH=...`
- `make bmad-review WORKFLOW=... BATCH=...`
- `make bmad-fix WORKFLOW=... BATCH=...`

Direct command targets also accept:

- `PROFILE=plain` to force freeform prompting
- `PROFILE=contracted` to require a contract-backed response
- `EVENT_ROOT=...` to override the event-log directory
- `OUTPUT=...` to choose where the final response message is captured

Example:

```powershell
make bmad-create-story CONTEXT="docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md" EXECUTE=1 PROFILE=contracted
```

Workflow set targets are now state-aware orchestrators. They consume event-log outputs, switch context to produced artifacts when available, and honor approval gates with `APPROVAL=stop|continue`.

Example:

```powershell
make bmad-flow-brownfield CONTEXT="docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md" EXECUTE=1 PROFILE=contracted APPROVAL=stop
```

## Event Logs And Production-Line Mode

When a contracted command executes successfully, the kit writes:

1. the captured final response message
2. any declared output artifacts
3. one structured event log under `_bmad-output/operator-events/`

The event log records:

- command
- prompt profile
- execution mode
- input artifacts
- output artifacts
- summary
- risks
- approval requirement
- next recommended command

This is the maintainable “production line” ledger. It improves traceability without forcing every step to create a new markdown document.

## Suggested Workflow Discipline

Use the following rules:

- artifact file is the immediate truth
- local state file is operator truth
- `review` means implementation is waiting for adversarial review
- `done` means review passed and the story was accepted
- release/deploy readiness is a separate gate, not a story status

Recommended phase progression:

1. `story`
2. `dev`
3. `review`
4. `fix` if needed
5. `review` again
6. `done`

## Test Coverage

The operator kit currently includes tests for:

- artifact-first status retrieval
- local shell command execution through the reusable command caller

Run:

```powershell
python -m pytest ops/tests -q
```

## Notes

- `sprint-status.yaml` can be retained as a summary, but the operator kit does not need to trust it.
- The implementation artifacts folder is the authoritative execution ledger.
- The kit is intentionally human-supervised. It reduces operational friction but does not remove the approval gate.
