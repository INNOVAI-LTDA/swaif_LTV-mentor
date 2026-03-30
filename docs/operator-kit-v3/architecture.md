# Operator Kit V3 Architecture

## Overview

V3 is structured as a supervised orchestration layer above BMAD skills and command prompts.

It is composed of four layers:

1. artifact layer
2. event layer
3. workflow layer
4. approval layer

## 1. Artifact Layer

The artifact layer contains the domain and planning outputs used across workflows.

Primary artifact classes:

- project context
- current-state docs
- PRD
- architecture docs
- epics and stories
- sprint plans
- story artifacts
- implementation reports
- review reports
- correction memos
- deploy and readiness docs

Design rule:

- artifacts represent engineering truth
- artifacts should remain human-readable
- artifacts should not be duplicated unnecessarily

## 2. Event Layer

The event layer records every BMAD execution step.

Each event is a structured JSON record that stores:

- workflow
- command
- execution id
- step id
- input artifacts
- output artifacts
- status
- summary
- risks
- approval requirement
- next recommended command

Design rule:

- events represent execution truth
- events should be machine-readable and resumable
- event logs should summarize results, not duplicate large artifacts

## 3. Workflow Layer

The workflow layer uses the current context plus event history to decide:

- what command can run next
- what artifact should be promoted as next context
- whether execution should continue or stop
- whether the step should retry
- whether approval is required

Design rule:

- workflow logic is deterministic wherever possible
- workflow logic stops at human approval boundaries
- workflow logic should be explainable in one concise operator summary

## 4. Approval Layer

The approval layer defines explicit decision points that remain human-controlled.

Examples:

- architecture accepted
- story accepted
- review findings accepted
- deploy allowed
- data ingestion confirmed

Design rule:

- risky transitions always require human confirmation
- approval points should be visible in event summaries
- approval is part of the workflow model, not an informal habit

## Storage Model

Recommended locations:

- `_bmad-output/implementation-artifacts/` for implementation truth
- `_bmad-output/planning-artifacts/` for planning outputs
- `_bmad-output/operator-events/` for execution logs
- `_bmad-output/operator-artifacts/` for reports produced by the operator layer
- `docs/operator-kit-v3/` for V3 design documentation

## Runtime Responsibilities

### Command runner

- execute one BMAD command
- validate the contract
- materialize artifacts
- write one event log

### Workflow runner

- orchestrate multiple command steps
- promote output artifacts into next-step context
- follow next-step routing
- stop at approval boundaries

### Status reporter

- summarize active artifacts
- summarize active workflows
- surface the latest non-terminal execution state

## Non-Goals

V3 does not aim to:

- replace BMAD itself
- become a CI/CD platform
- remove approval from sensitive operations
- manage infrastructure provisioning directly
