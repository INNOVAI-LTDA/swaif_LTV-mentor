---
name: BMAD Plan a Solution
about: Turn a requirements file into PRD, architecture, and first implementation story
labels: [bmad:planning, awaiting-codex]
---

# BMAD Solution Request

## Goal
Turn a requirements file extracted from a client conversation into a deployable V1 solution plan.

## Input file
`docs/discovery/client-alpha-requirements.md`

## Source context
This file came from a client conversation. Treat it as raw discovery input.

## Start with
`bmad-help`

## Required outputs
- PRD
- architecture
- epics and stories
- readiness check
- first narrow implementation story

## Rules
- do not invent unsupported features
- keep V1 minimal and deployable
- prefer simple full-stack structure
- respect project-context.md if present
- optimize for practical deployment and low operator confusion

## Exclusions
- billing integration
- AI assistant features
- patient portal

## Done when
- planning artifacts exist
- readiness is checked
- first implementation story is ready
- next exact step is explicit
