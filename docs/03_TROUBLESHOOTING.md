# Troubleshooting

## Problem: Codex went too wide
Likely cause:
- vague issue
- story too large
- project-context missing or weak

Fix:
- run Fix Loop or Correct-Course Loop
- tighten issue scope
- strengthen project-context rules

## Problem: Review keeps failing on hidden regressions
Likely cause:
- tests too shallow
- review prompt too soft
- contracts not documented

Fix:
- require nearest-layer tests
- escalate review reasoning for auth/routing/env/runtime work
- update docs/templates/examples if operator contract changed

## Problem: Wrong batch order
Likely cause:
- no state file
- no wrapper enforcement

Fix:
- use `ops/state/workflow_state.sample.json`
- run through wrappers only

## Problem: Phone flow feels confusing
Fix:
- always start with a GitHub issue
- use labels
- use the copy-paste prompt that matches the issue type
- ask Codex to stop at the next approval gate
