# Story 4.6d: batch-f-frontend-test-gate-restoration (Batch F)

Status: review

## Story

As a release operator,
I want the remaining red frontend tests brought back into alignment with the current runtime and UI contract,
so that the Batch F release gate can return to a true green `npm run test` without reopening deploy-scope decisions.

## Background (Why This Exists)

The follow-up on [4-6c-batch-f-test-gate-contract-consistency-fix.md](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/implementation-artifacts/4-6c-batch-f-test-gate-contract-consistency-fix.md) restored the operator-facing rule that frontend tests must be green before deploy.

That story also confirmed the remaining blocker is now technical, not contractual:

1. `frontend/npm run test` still fails in:
   - [env.test.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/shared/config/env.test.ts)
   - [mentor-shell-actions.test.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/test/mentor-shell-actions.test.tsx)
2. Current investigation suggests both failures are stale-test drift, not yet a confirmed runtime or page-behavior regression:
   - [env.test.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/shared/config/env.test.ts) still expects the runtime import to fail when `VITE_DEPLOY_TARGET` is missing, but the current local/test baseline now injects `local` through:
     - [setup.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/test/setup.ts)
     - [vite.config.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vite.config.ts)
     - the committed local baseline in `frontend/.env`
   - [mentor-shell-actions.test.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/test/mentor-shell-actions.test.tsx) still asserts older page headings that no longer match:
     - [RadarPage.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/radar/pages/RadarPage.tsx)
     - [CommandCenterPage.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/command-center/pages/CommandCenterPage.tsx)
3. The smallest valid next step is to restore the test gate by aligning these tests with the current intended contract, not by reopening Batch F deploy docs, CSP/HSTS behavior, or unrelated frontend code.

## Requirements

1. Restore a green frontend `npm run test` gate for the currently failing specs.
2. Keep the local/test environment baseline intact unless investigation proves the runtime behavior is wrong.
3. Preserve the real purpose of the affected tests:
   - env contract validation still proves `VITE_DEPLOY_TARGET` is required at the normalization boundary
   - mentor shell tests still prove header actions were removed from the relevant pages
4. Avoid reopening Batch F deploy docs, CSP/HSTS config, or unrelated UI copy work.

## Acceptance Criteria

1. `cd frontend && npm run test` passes.
2. [env.test.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/shared/config/env.test.ts) no longer fails because it assumes a missing `VITE_DEPLOY_TARGET` runtime state that is incompatible with the current local/test baseline.
3. [mentor-shell-actions.test.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/test/mentor-shell-actions.test.tsx) asserts the current intended page render state while still checking that the old header actions remain absent.
4. No deploy docs, `frontend/vercel.json`, CSP/HSTS behavior, or unrelated runtime code is changed unless the developer finds a real contract bug and documents why a test-only fix is insufficient.

## Implementation Notes (Keep Diffs Narrow)

- Prefer the narrowest valid fix that restores the test gate.
- Treat the current local/test baseline as intentional unless proven otherwise:
  - [setup.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/test/setup.ts) stubs `VITE_DEPLOY_TARGET=local`
  - [vite.config.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vite.config.ts) falls back to `local` in test mode
  - `frontend/.env` currently supplies a local deploy target for developer runs
- Preserve the helper-level contract coverage in [envContract.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/shared/config/envContract.ts), where missing `VITE_DEPLOY_TARGET` is still rejected.
- For the mentor shell tests, prefer asserting current stable headings or other current page landmarks rather than reverting page copy just to satisfy stale test strings.
- If implementation reveals a genuine runtime defect instead of stale-test drift, stop at the smallest code fix and document why the runtime contract had to change.

## Files Likely Touched

- [env.test.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/shared/config/env.test.ts)
- [mentor-shell-actions.test.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/test/mentor-shell-actions.test.tsx)

Reference files to inspect before editing:

- [env.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/shared/config/env.ts)
- [envContract.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/shared/config/envContract.ts)
- [setup.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/test/setup.ts)
- [vite.config.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vite.config.ts)
- [RadarPage.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/radar/pages/RadarPage.tsx)
- [CommandCenterPage.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/command-center/pages/CommandCenterPage.tsx)

## Tasks / Subtasks

### Task 1: Align The Env Runtime Test With The Current Baseline (AC: 1, 2)

- [x] Reconfirm how the runtime env module is loaded under Vitest using:
  - [setup.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/test/setup.ts)
  - [vite.config.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/vite.config.ts)
  - `frontend/.env`
- [x] Update [env.test.ts](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/shared/config/env.test.ts) so it verifies the intended current contract instead of asserting a runtime-missing-env case that the test harness now prevents.
- [x] Keep explicit helper-level coverage that `normalizeDeployTarget(undefined)` throws.
- [x] Do not loosen runtime validation just to satisfy the test unless investigation proves the current runtime behavior is actually broken.

### Task 2: Align Mentor Shell Action Tests With The Current Pages (AC: 1, 3)

- [x] Update [mentor-shell-actions.test.tsx](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/test/mentor-shell-actions.test.tsx) so the positive render assertions match the current intended page content.
- [x] Keep the core purpose of the test intact:
  - no `Atualizar leitura` header action
  - no `Abrir centro` header action on Radar
  - no `Abrir matriz` header action on Command Center
- [x] Do not revert current UI copy unless the existing page text is itself a confirmed regression.

### Task 3: Prove The Frontend Test Gate Is Green Again (AC: 1, 4)

- [x] Run the smallest targeted test commands first while iterating:
  - `cd frontend && npm run test -- src/shared/config/env.test.ts`
  - `cd frontend && npm run test -- src/test/mentor-shell-actions.test.tsx`
- [x] After the targeted fixes pass, run:
  - `cd frontend && npm run test`
- [x] If any new failures appear outside these two specs, stop and report them rather than expanding scope silently.

## Non-Goals / Guardrails

- Do not edit `DEPLOY.md`, `docs/client-launch-runbook.md`, or `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` in this story.
- Do not change `frontend/vercel.json`, CSP, HSTS, or Vercel routing behavior.
- Do not introduce new environment rules or change the deploy contract unless a real defect is proven.
- Do not broaden this into general UI copy cleanup.

## Validation Steps

1. Run targeted tests first:
   - `cd frontend && npm run test -- src/shared/config/env.test.ts`
   - `cd frontend && npm run test -- src/test/mentor-shell-actions.test.tsx`
2. Then run the full frontend test suite:
   - `cd frontend && npm run test`
3. Confirm no deploy docs or deploy config files changed as part of this fix.

## Dev Agent Record

### Completion Notes

- Replaced one stale runtime-import assertion in `env.test.ts` with a test of the current local/test baseline that Vitest intentionally injects through `setup.ts`, `vite.config.ts`, and the committed local `.env`.
- Preserved helper-level guardrail coverage that `normalizeDeployTarget(undefined)` still throws, so the environment contract remains enforced at the normalization boundary.
- Updated `mentor-shell-actions.test.tsx` to assert current stable page landmarks on Radar and Command Center while keeping the real regression guard intact: the removed header actions are still absent.
- Verified the fix with both targeted specs and the full frontend Vitest suite; no additional frontend test failures remained after these two stale assertions were corrected.

## File List

- `frontend/src/shared/config/env.test.ts`
- `frontend/src/test/mentor-shell-actions.test.tsx`
- `_bmad-output/implementation-artifacts/4-6d-batch-f-frontend-test-gate-restoration.md`

## Change Log

- Created follow-up story to restore the red frontend test gate after `4-6c` kept the deploy contract strict.
- Restored the frontend test gate by aligning two stale tests with the current local/test harness and current mentor page content.
