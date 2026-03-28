# Story 4.6b: batch-f-release-gate-and-story-alignment-fix (Batch F)

Status: review

## Story

As a release operator,
I want the Batch F release-gate docs and story artifact to match the implemented CSP/HSTS rollout posture,
so that the deployment checklist, BMAD story state, and go/no-go decision all describe the same current reality.

## Background (Why This Exists)

Batch F implementation on [4-6a-batch-f-csp-report-only-and-hsts-gating.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/implementation-artifacts/4-6a-batch-f-csp-report-only-and-hsts-gating.md) landed the core mechanics:

- `frontend/vercel.json` now includes `Content-Security-Policy-Report-Only`
- `Strict-Transport-Security` remains intentionally disabled pending live HTTPS/domain verification
- `DEPLOY.md` and `docs/client-launch-runbook.md` describe the report-only CSP posture and the HSTS gate

Review found four remaining contract gaps:

1. `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` still represents the release gate as effectively green while the frontend test gate is red. The checklist still carries build/test evidence as done, but the current deploy contract in `DEPLOY.md` and `docs/client-launch-runbook.md` requires a green `npm run test` gate before deploy.
2. `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` still treats the security-hosting gate as a generic "baseline headers" check and does not explicitly cover:
   - `Content-Security-Policy-Report-Only` present on the HTML response
   - no CSP console violations on the hosted route set
   - `Strict-Transport-Security` absent until custom-domain HTTPS is verified stable
3. The background section in `4-6a-batch-f-csp-report-only-and-hsts-gating.md` still describes the pre-implementation state and says no committed CSP/HSTS header exists yet.
4. The batch should not be presented as deployment-ready while `npm run test` remains red unless that gate is fixed in a separate narrow batch or explicitly waived outside this story with release-tracker evidence.

This follow-up should correct the release gate and story-state drift without reopening CSP policy design or fixing unrelated test failures.

## Requirements

1. Update `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` so the release gate explicitly covers:
   - `Content-Security-Policy-Report-Only` present on the HTML response
   - no CSP console violations on the hosted route set
   - `Strict-Transport-Security` absent until custom-domain HTTPS is verified stable
2. Refresh the stale background section in `4-6a-batch-f-csp-report-only-and-hsts-gating.md` so it matches the implemented repo state.
3. Do not present Batch F as deployment-ready until the failing `npm run test` gate is either:
   - fixed in a separate narrow batch, or
   - formally waived outside this story with explicit release-tracker evidence

## Acceptance Criteria

1. The frontend deployment readiness checklist no longer presents Batch F as release-ready while `npm run test` is still failing.
2. The frontend deployment readiness checklist explicitly includes the new Batch F release-gate checks for report-only CSP and HSTS absence/gating.
3. The `4-6a` story background no longer claims the repo lacks CSP after implementation.
4. The Batch F story artifacts no longer imply deployment readiness while `npm run test` is still failing.
5. No runtime/config behavior changes are introduced beyond doc and artifact alignment.

## Implementation Notes (Keep Diffs Narrow)

- Treat this as a documentation and BMAD-artifact alignment fix only.
- Do not change `frontend/vercel.json`, CSP directives, HSTS behavior, or application runtime code.
- Do not fix the failing frontend tests in this story.
- Do not create a waiver inside this story; only make the unresolved test gate explicit and defer the actual waiver or fix to the proper follow-up path.

## Files Likely Touched

- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- `_bmad-output/implementation-artifacts/4-6a-batch-f-csp-report-only-and-hsts-gating.md`

## Tasks / Subtasks

### Task 1: Align The Release Gate Checklist (AC: 1, 2)

- [x] Update `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` so the hosted release gate explicitly checks:
  - `Content-Security-Policy-Report-Only` present on the HTML response
  - no CSP console violations on the hosted route set
  - `Strict-Transport-Security` absent until custom-domain HTTPS is verified stable
- [x] Remove or downgrade any checklist wording or check-state that currently presents Batch F as green while `npm run test` is still red.
- [x] Keep the wording consistent with `DEPLOY.md` and `docs/client-launch-runbook.md`.

### Task 2: Refresh The Implemented Story Background (AC: 3)

- [x] Update the background/current-state section in `4-6a-batch-f-csp-report-only-and-hsts-gating.md` so it reflects:
  - report-only CSP is already committed in `frontend/vercel.json`
  - HSTS remains intentionally disabled
- [x] Do not rewrite the whole story; only remove the stale pre-implementation drift.

### Task 3: Make The Red Test Gate Explicit Without Reopening It (AC: 1, 4, 5)

- [x] Add one explicit note in the Batch F story artifact that deployment readiness is still blocked while `npm run test` is failing.
- [x] State that the red test gate must be:
  - fixed in a separate narrow batch, or
  - formally waived outside this story with explicit release-tracker evidence
- [x] Do not attempt to repair or waive the tests inside this follow-up.

## Non-Goals / Guardrails

- Do not change runtime code, frontend config, or CSP/HSTS header values.
- Do not mix test fixes into this story.
- Do not introduce cache work or unrelated deploy cleanup.

## Validation Steps

1. Review `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` and confirm it now explicitly covers:
   - `Content-Security-Policy-Report-Only`
   - no hosted CSP console violations
   - `Strict-Transport-Security` absent until the HTTPS gate is closed
2. Review `_bmad-output/implementation-artifacts/4-6a-batch-f-csp-report-only-and-hsts-gating.md` and confirm:
   - the background matches the implemented repo state
   - the unresolved `npm run test` gate is explicit
3. Confirm no files outside the release-gate checklist and Batch F story artifact were changed.

## Dev Agent Record

### Completion Notes

- Updated the frontend release checklist so Batch F no longer reads as release-ready while `npm run test` is still failing.
- Expanded the hosted release gate to include `Content-Security-Policy-Report-Only`, hosted CSP-console validation, and explicit `Strict-Transport-Security` absence until the HTTPS gate is closed.
- Refreshed the `4-6a` background and added an explicit note that Batch F is still blocked for deploy-readiness until the test gate is fixed or formally waived outside this story.
- Re-ran `frontend/npm run test` and confirmed the gate remains red because of the existing failures in `src/shared/config/env.test.ts` and `src/test/mentor-shell-actions.test.tsx`; this follow-up does not attempt to repair them.

## File List

- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- `_bmad-output/implementation-artifacts/4-6a-batch-f-csp-report-only-and-hsts-gating.md`
- `_bmad-output/implementation-artifacts/4-6b-batch-f-release-gate-and-story-alignment-fix.md`

## Change Log

- Aligned the Batch F release checklist with the report-only CSP and HSTS gate contract.
- Removed the false green signal for the current red frontend test gate.
- Refreshed the Batch F implementation story so it no longer implies deploy-readiness.
