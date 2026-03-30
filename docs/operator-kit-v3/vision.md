# Operator Kit V3 Vision

## Purpose

Define the target operating model for V3 of the local BMAD operator kit.

V3 is intended to improve orchestration quality, execution traceability, and operator ergonomics without converting the system into a fully autonomous agent.

## Problem Statement

The current operator kit already supports:

- local BMAD command execution
- contracted prompts
- artifact materialization
- event logging
- basic workflow chaining

However, V2 still depends on a meaningful amount of operator memory and coordination for:

- deciding the next step
- identifying the best next context artifact
- interpreting whether a workflow should stop
- reconciling event logs with workflow state
- understanding where the human approval boundary sits

## Vision

V3 should become a supervised workflow engine for BMAD.

It should:

- read artifacts and event logs as first-class execution truth
- route commands with less manual intervention
- summarize execution in operator-ready terms
- stop predictably at approval boundaries
- make resumability and auditability straightforward

## Desired Operator Experience

The operator should be able to:

1. choose a workflow or a starting command
2. provide an initial context artifact
3. run the flow locally
4. inspect concise event summaries instead of raw model reasoning
5. approve, reject, or resume confidently

## Design Principles

- supervised, not autonomous
- event-driven, not memory-driven
- artifact-first, not tracker-first
- contract-validated, not prompt-assumed
- resumable, not ephemeral
- explicit approval gates, not implicit trust

## Success Criteria

V3 is successful if it reduces:

- manual context handoff
- manual status bookkeeping
- ambiguity about next command
- noisy response output
- operator uncertainty after interruptions

while preserving:

- BMAD workflow discipline
- human approval control
- minimal documentation sprawl
- local execution simplicity
