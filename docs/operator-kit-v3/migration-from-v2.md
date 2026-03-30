# Operator Kit V3 Migration From V2

## Purpose

Describe how to evolve from the current V2 operator kit into the V3 supervised orchestration model without breaking existing usage.

## Current V2 Strengths

V2 already has:

- command contracts
- event logs
- direct command execution
- workflow orchestration
- contracted prompt support
- documentation for workflows and manual runs

## Current V2 Gaps

V2 still has partial dependence on:

- manual interpretation of workflow state
- mixed reliance on local state files
- limited explicit approval modeling
- documentation spread across multiple top-level docs

## Migration Strategy

### Phase 1 - Documentation Alignment

- publish the V3 design pack
- align terminology across current docs
- clarify event vs artifact truth

### Phase 2 - State Refactor

- reduce handwritten local state
- derive more workflow state from artifacts and events

### Phase 3 - Approval Model

- make approval gates explicit in contracts and event logs
- surface operator stop conditions clearly

### Phase 4 - Resume And Recovery

- improve resume from last successful event
- improve repair retry handling

### Phase 5 - Operator Ergonomics

- improve summaries
- improve runbook guidance
- improve failure diagnostics

## Compatibility Rule

V3 should preserve:

- existing `make bmad-*` usage where practical
- existing artifact directories
- existing contracted-command behavior

while improving:

- orchestration clarity
- resumability
- approval discipline

## Non-Breaking Principle

Where possible, V3 should layer on top of V2 behavior instead of replacing it abruptly.
