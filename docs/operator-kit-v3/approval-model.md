# Operator Kit V3 Approval Model

## Purpose

Define which workflow transitions remain human-controlled in V3.

## Core Rule

V3 is supervised by design.

Automation may route and prepare work, but it should not silently cross risk boundaries that require engineering judgment.

## Approval Classes

### Planning Approval

Examples:

- product brief accepted
- PRD accepted
- architecture accepted

Why manual:

- these decisions shape later implementation scope and constraints

### Execution Approval

Examples:

- story accepted before implementation
- review findings accepted as resolved

Why manual:

- these decisions affect code quality and scope discipline

### Operational Approval

Examples:

- deploy allowed
- real data ingestion confirmed
- rollback executed

Why manual:

- these decisions have production and business impact

## Recommended Gates

At minimum, V3 should expose approval gates for:

- architecture
- story readiness
- review completion
- deploy signoff
- destructive data operation confirmation

## Event Representation

Approval-relevant steps should surface:

- `approval_required`
- summary of what is being approved
- artifact references to inspect

## Default Behavior

The workflow engine should stop when:

- the current step requires approval
- approval mode is `stop`

## Override Behavior

The operator may choose `APPROVAL=continue` when:

- the workflow is low-risk
- the operator explicitly accepts reduced pause points
- the workflow does not contain destructive operations

## Explicit Non-Goals

V3 should not:

- auto-approve deploys
- auto-approve destructive data changes
- auto-approve major architecture changes
