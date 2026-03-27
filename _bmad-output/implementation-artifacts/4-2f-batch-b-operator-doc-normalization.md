# Story 4.2f: batch-b-operator-doc-normalization

Status: ready-for-dev

## Story

As a release operator,
I want the remaining operator docs to speak consistently in current-state Batch B terms and include the `/dashboard` validation route,
so that the deploy/runbook contract matches the repository's actual Batch B implementation and the `4-2d` story does not present itself as review-ready while its hosted-validation-doc task remains open.

## Scope (Smallest Valid Fix Set Only)

1. Normalize remaining "Batch A" wording to current-state Batch B terms in:
   - `DEPLOY.md`
   - `docs/client-launch-runbook.md`
   - `frontend/README.md`
2. Add `/dashboard` to the hosted refresh/validation route list in `docs/client-launch-runbook.md`.
3. After doc alignment, make the `4-2d` story record consistent:
   - either close the open hosted-validation-doc task
   - or stop presenting the story as review-ready (keep it as not ready for review / in-progress)

No runtime code/config changes are allowed in this story.

## Acceptance Criteria

1. `DEPLOY.md` no longer presents itself as "Batch A" while describing Batch B behavior; wording is consistent with current-state Batch B.
2. `docs/client-launch-runbook.md` no longer frames hosted deployment as "Vercel Batch A contract" where it is actually describing current-state Batch B.
3. `frontend/README.md` no longer contains leftover "Batch A" deploy-contract wording for the current Vercel guidance (only historical references allowed when explicitly labeled).
4. `docs/client-launch-runbook.md` includes `/dashboard` in the explicit browser hard-refresh list for SPA rewrite validation.
5. `_bmad-output/implementation-artifacts/4-2d-batch-b-spa-rewrite-and-env-separation.md` is internally consistent:
   - it must not be in a "review-ready" posture while keeping the hosted-validation-doc task open
   - the story status and checkboxes match the stated state (hosted validation still pending vs documented steps)

## Tasks / Subtasks

### Task 1: Normalize Batch Wording In Operator Docs (AC: 1, 2, 3)

- [ ] Update `DEPLOY.md` header and any remaining Batch A references that describe the active hosted Vercel contract, so the doc reads as current-state Batch B.
  - Keep historical notes if needed, but label them as historical.
- [ ] Update `docs/client-launch-runbook.md` references to "Vercel Batch A contract" to reflect current-state Batch B (rewrite versioned, Preview/Production env examples exist).
- [ ] Update `frontend/README.md` leftover Batch A wording related to Vercel deploy guidance:
  - Specifically adjust any lines that still say "Para o deploy Vercel do Batch A..." when they are describing the current contract.
  - Keep the AccMed local template note as local-only (do not re-scope it).

### Task 2: Add `/dashboard` To Hosted Refresh List (AC: 4)

- [ ] In `docs/client-launch-runbook.md`, add `/dashboard` to the "Validate SPA rewrite" direct refresh URLs list.
- [ ] Ensure this remains consistent with `DEPLOY.md` hosted validation steps and the `4-2d` acceptance criteria.

### Task 3: Make The `4-2d` Story Record Consistent (AC: 5)

- [ ] Decide and apply one of:
  - Option A (recommended): keep Status `review` but close the hosted-validation-doc task if hosted validation steps are now documented elsewhere (e.g. `DEPLOY.md` and runbook).
  - Option B: keep hosted-validation-doc task open and change story Status away from `review` (e.g. `in-progress`) so it is not presented as review-ready.
- [ ] Ensure the story completion notes stay honest that real hosted validation on Vercel Preview/Production is still pending.

## Guardrails

- Do not change runtime code (`frontend/src/**`), `frontend/vercel.json`, backend code, or test behavior.
- Do not add security headers/CSP/HSTS or CORS changes.
- Keep diffs narrow and operator-contract focused.

## Likely Files

- `DEPLOY.md`
- `docs/client-launch-runbook.md`
- `frontend/README.md`
- `_bmad-output/implementation-artifacts/4-2d-batch-b-spa-rewrite-and-env-separation.md`

## Validation Steps (Docs Only)

- `rg -n "Batch A|Batch B|dashboard|Host Readiness|Vercel Batch" DEPLOY.md docs/client-launch-runbook.md frontend/README.md _bmad-output/implementation-artifacts/4-2d-batch-b-spa-rewrite-and-env-separation.md`
- `git diff -- DEPLOY.md docs/client-launch-runbook.md frontend/README.md _bmad-output/implementation-artifacts/4-2d-batch-b-spa-rewrite-and-env-separation.md`

## Dev Agent Record

### Agent Model Used

gpt-5.2

### Debug Log References

TBD (populate during implementation)

### Completion Notes List

TBD (populate during implementation)

### File List

TBD (populate during implementation)
