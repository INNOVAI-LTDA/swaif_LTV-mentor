---
name: BMAD Create a Story
about: Create one narrow implementation story from approved planning artifacts
labels: [bmad:story, awaiting-codex]
---

# BMAD Story Request

## Goal
Create one narrow implementation story only.

## Inputs to read
- `_bmad-output/project-context.md`
- approved PRD
- approved architecture
- `sprint-status.yaml` if present

## Scope
Describe only the boundary to implement next.

## Output must include
- exact scope
- likely files/modules
- acceptance criteria
- tests to add/update
- out-of-scope items
- regression risks

## Rules
- keep diffs narrow
- do not mix boundaries
- avoid unrelated refactors
