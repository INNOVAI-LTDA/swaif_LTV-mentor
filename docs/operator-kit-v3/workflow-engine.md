# Operator Kit V3 Workflow Engine

## Purpose

Define how the V3 workflow engine should route, continue, retry, or stop a BMAD execution flow.

## Engine Inputs

The engine reads:

- selected workflow type
- initial context artifact
- command contracts
- event history
- output artifacts from the previous step
- operator overrides

## Engine Outputs

The engine decides:

- current command
- next context artifact
- whether approval is required
- whether the workflow should continue
- whether the workflow should stop
- whether a repair retry should run

## Base Loop

For each execution step:

1. resolve current workflow
2. choose current command
3. assemble context
4. execute command
5. validate output contract
6. materialize artifacts
7. write event log
8. read `status`, `approval_required`, and `next_command`
9. choose next action

## Continue Rules

The engine may continue automatically when:

- output contract is valid
- no approval is required
- status is not terminal-blocking
- next step is deterministic

## Stop Rules

The engine must stop when:

- `approval_required = true` and approval mode is `stop`
- status is `blocked`
- status is `failed`
- status is `needs_input`
- a required output artifact is missing
- the response contract cannot be repaired

## Retry Rules

If a contracted command returns invalid structured output:

1. issue one repair prompt
2. require contract-only output
3. if still invalid, write failure event and stop

This keeps the workflow resilient without hiding failures.

## Context Promotion Rules

Default rule:

- promote output artifacts from the last successful step

Fallback rule:

- preserve the previous context bundle

## Loop Prevention

The engine should protect against bad loops by:

- capping total step count
- refusing same-step infinite repetition without operator override
- surfacing repeated `changes_requested` patterns clearly

## Approval Mode

Supported approval modes:

- `stop`
- `continue`

Default:

- `stop`

This preserves supervised operation as the normal mode.
