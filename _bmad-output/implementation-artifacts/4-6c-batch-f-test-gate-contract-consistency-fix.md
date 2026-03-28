# Story 4.6c: batch-f-test-gate-contract-consistency-fix (Batch F)

Status: review

## Story

As a release operator,
I want the Batch F release checklist to match the current operator-facing deploy contract for the frontend test gate,
so that the deploy workflow speaks with one rule about whether a red `npm run test` can block or be bypassed.

## Background (Why This Exists)

The follow-up alignment in [4-6b-batch-f-release-gate-and-story-alignment-fix.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/implementation-artifacts/4-6b-batch-f-release-gate-and-story-alignment-fix.md) correctly made the Batch F checklist stop reading as green while the frontend test gate is red and correctly added explicit CSP/HSTS hosted checks.

One contract gap remains:

1. [frontend-deployment-readiness-checklist.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/frontend-deployment-readiness-checklist.md) now introduces a waiver path for a red frontend test gate in operator-facing checklist text.
2. [DEPLOY.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/DEPLOY.md) and [client-launch-runbook.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md) still use the stricter contract: frontend release requires a green `npm run test`.
3. That leaves the operator contract internally inconsistent even though the intended Batch F fix is smaller: keep the operator-facing contract strict, and if a waiver path is ever needed, record it only as an internal BMAD/release-tracker escalation path rather than as checklist guidance.

This follow-up should remove that operator-facing waiver drift without reopening CSP/HSTS rollout decisions, frontend tests, or broader release policy changes.

## Requirements

1. Remove the waiver wording from [frontend-deployment-readiness-checklist.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/mvp-mentoria/frontend-deployment-readiness-checklist.md) so the checklist aligns with the current stricter deploy contract:
   - `npm run test` must be green before deploy
2. Keep the existing Batch F CSP/HSTS hosted checks intact in the checklist.
3. Do not broaden the change into DEPLOY/runbook edits if the chosen fix is to preserve the stricter existing operator contract.

## Acceptance Criteria

1. The operator-facing checklist no longer mentions an exception or waiver path for a red frontend test gate.
2. The checklist remains aligned with [DEPLOY.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/DEPLOY.md) and [client-launch-runbook.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md), both of which require green frontend tests before deploy.
3. The Batch F CSP report-only and HSTS absence checks added in the previous follow-up remain present.
4. No runtime/config behavior changes are introduced.

## Implementation Notes (Keep Diffs Narrow)

- Treat this as a checklist-contract fix only.
- Do not change `frontend/vercel.json`, CSP directives, HSTS behavior, or frontend code.
- Do not fix or waive the failing frontend tests in this story.
- Do not add a new exception path to `DEPLOY.md` or `docs/client-launch-runbook.md`; the smallest valid fix is to remove the checklist waiver wording instead.

## Files Likely Touched

- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`

## Tasks / Subtasks

### Task 1: Remove Operator-Facing Waiver Drift (AC: 1, 2)

- [x] Remove the note in `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` that suggests a dispense/waiver path for a red `npm run test` gate.
- [x] Remove the checklist evidence line that suggests a formal waiver can satisfy the red test gate.
- [x] Keep the checklist wording aligned with the stricter current contract in `DEPLOY.md` and `docs/client-launch-runbook.md`.

### Task 2: Preserve The Batch F Hosted Security Checks (AC: 3, 4)

- [x] Confirm the checklist still explicitly includes:
  - `Content-Security-Policy-Report-Only` present on the HTML response
  - no hosted CSP console violations
  - `Strict-Transport-Security` absent until the HTTPS custom-domain gate is closed
- [x] Do not remove or dilute those Batch F checks while fixing the test-gate wording.

## Non-Goals / Guardrails

- Do not edit `DEPLOY.md` or `docs/client-launch-runbook.md` in this story.
- Do not change the failing frontend tests or their current status.
- Do not reopen any CSP/HSTS design decision.
- Do not introduce a broader release-waiver policy in operator docs.

## Validation Steps

1. Review `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` and confirm:
   - no waiver/dispense wording remains for a red `npm run test` gate
   - the checklist still requires green tests before deploy
2. Confirm `DEPLOY.md` and `docs/client-launch-runbook.md` remain unchanged and still require green `npm run test`.
3. Confirm the Batch F hosted checks for CSP report-only and HSTS absence are still present in the checklist.

## Dev Agent Record

### Completion Notes

- Removed the two operator-facing waiver references from the frontend deployment readiness checklist so it now matches the stricter current deploy contract.
- Preserved the existing Batch F hosted checks for `Content-Security-Policy-Report-Only` and `Strict-Transport-Security` absence.
- Re-ran `frontend/npm run test` to confirm the gate remains red and therefore still matters operationally; this story does not change or waive those failures.
- Reviewed the resulting diff against the original fix set and found no further changes needed in scope.

## File List

- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- `_bmad-output/implementation-artifacts/4-6c-batch-f-test-gate-contract-consistency-fix.md`

## Change Log

- Removed operator-facing waiver wording for the red frontend test gate from the deployment checklist.
- Kept the Batch F CSP/HSTS hosted checks intact while restoring contract consistency with `DEPLOY.md` and `docs/client-launch-runbook.md`.
