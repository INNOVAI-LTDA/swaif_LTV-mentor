---
name: BMAD Dev / Review / Fix
about: Implement, review, or fix one already-bounded batch
labels: [bmad:dev, awaiting-codex]
---

# BMAD Batch Request

## Mode
Choose one:
- dev
- review
- fix

## Story or batch reference
`<story-id or batch-id>`

## Required files
- `_bmad-output/project-context.md`
- approved story file
- architecture sections for touched boundary
- previous review findings if mode = fix

## Rules
- keep original batch boundary
- smallest valid change set only
- update tests/docs/templates if operator contract changes
- do not expand scope

## Done when
- mode dev: code + tests + summary are ready
- mode review: approved or changes requested with smallest valid fix set
- mode fix: original review findings are re-checked
