# Story 4.2e: batch-b-doc-contract-alignment-after-review

Status: ready-for-dev

## Story

As a release operator,
I want the Batch B operator docs, release-gate docs, and story record aligned with the actual committed Batch B implementation,
so that the repo no longer mixes "Batch B is still pending" messaging with a repo state where the SPA rewrite and Preview/Production env examples already exist.

## Why This Follow-Up Exists

Code review on `4-2d-batch-b-spa-rewrite-and-env-separation.md` found that the implementation changed the repo state correctly in code/config, but left the operator-facing documentation in a contradictory state:

- `frontend/vercel.json` now contains the SPA rewrite.
- `frontend/.env.preview.example` and `frontend/.env.production.example` now exist.
- `DEPLOY.md` still says deep-link refresh is deferred to Batch B and still lists Batch B items as out of scope.
- `frontend/README.md` still says env separation is pending Batch B.
- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` still behaves as the release gate but has not been aligned to the new Batch B operator contract.
- The `4-2d` story record is in `review`, but it still has hosted validation open and should not read as if full hosted readiness is already complete.

This story is intentionally limited to doc/template/story alignment only.

## Acceptance Criteria

1. `DEPLOY.md` reflects the current Batch B state and no longer says the app is "not host-ready until Batch B" or that SPA rewrites / Preview-Production separation are still out of scope for Batch B.
2. `DEPLOY.md` documents the hosted validation steps now expected after deploy, including hard-refresh coverage for:
   - `/`
   - `/login`
   - `/dashboard`
   - `/app/admin`
   - `/app/matriz-renovacao`
   - `/app/aluno`
3. `frontend/README.md` no longer describes Preview/Production separation as still pending Batch B.
4. If `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` remains the release gate, it is updated so its routing/hosting and deploy-doc wording matches the new Batch B operator contract instead of describing the rewrite/env split as still pending implementation.
5. `frontend/.env.production.example` uses plain ASCII or correctly encoded Portuguese text for the new operator-facing strings.
6. The `4-2d` story record remains honest about completion state:
   - keep it in `review`
   - do not imply hosted validation is already complete
   - if needed, add a completion note or follow-up note clarifying that hosted validation remains an operator/deploy step

## Tasks / Subtasks

### Task 1: Align `DEPLOY.md` To Actual Batch B State (AC: 1, 2)

- [ ] Remove the wording that says the app is still "not host-ready until Batch B".
- [ ] Remove the "Batch B" out-of-scope bullets for:
  - SPA rewrites / deep-link refresh activation
  - Preview vs Production env split
- [ ] Replace that stale wording with the current operator contract:
  - SPA rewrite is now versioned in `frontend/vercel.json`
  - Preview and Production example env files now exist
  - hosted validation is still required after deploy
- [ ] Add explicit hosted validation steps for:
  - `/`
  - `/login`
  - `/dashboard`
  - `/app/admin`
  - `/app/matriz-renovacao`
  - `/app/aluno`

### Task 2: Align Frontend Operator Docs (AC: 3)

- [ ] Update `frontend/README.md` so it no longer says env separation is still pending Batch B.
- [ ] Keep the README wording consistent with the current explicit operator contract:
  - Preview uses `frontend/.env.preview.example` as the example reference
  - Production uses `frontend/.env.production.example` as the example reference
  - `VITE_API_BASE_URL` remains explicit for hosted builds
- [ ] Do not expand scope into runtime/env contract behavior changes here.

### Task 3: Align Release Gate Doc If Still Authoritative (AC: 4)

- [ ] Review `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` as the current release-gate doc.
- [ ] If it is still the active gate, update the routing/hosting and deploy-doc wording so it matches the new Batch B repo state:
  - rewrite exists in repo
  - hosted validation is still pending until run on real Vercel environments
  - env separation examples now exist
- [ ] Preserve the distinction between "implemented in repo" and "validated on host" instead of collapsing them together.

### Task 4: Fix Production Env Template Text (AC: 5)

- [ ] Update `frontend/.env.production.example` so its operator-facing strings are plain ASCII or correctly encoded Portuguese.
- [ ] Keep the file non-secret and placeholder-based.

### Task 5: Keep The Story Record Honest (AC: 6)

- [ ] Update `_bmad-output/implementation-artifacts/4-2d-batch-b-spa-rewrite-and-env-separation.md` only in allowed story-record sections.
- [ ] Keep the story status at `review`.
- [ ] Ensure the record does not imply full hosted validation already happened while the hosted validation checklist remains open.
- [ ] If useful, add a short completion note clarifying that repo-side Batch B prep is implemented but hosted validation remains pending.

## Scope Guardrails

- This is a docs/template/story-record correction story only.
- Do not change `frontend/vercel.json`, routing behavior, env validation logic, or backend code here.
- Do not add new runtime behavior or broaden Batch B.
- Do not perform unrelated cleanup in docs outside the files above.

## Likely Files

- `DEPLOY.md`
- `frontend/README.md`
- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- `frontend/.env.production.example`
- `_bmad-output/implementation-artifacts/4-2d-batch-b-spa-rewrite-and-env-separation.md`

## Validation Expectations

- Targeted text/contract review only.
- Suitable checks:
  - `rg -n "Batch B|not host-ready|Preview|Production|dashboard|rewrite|env.production.example|env.preview.example" DEPLOY.md frontend/README.md docs/mvp-mentoria/frontend-deployment-readiness-checklist.md frontend/.env.production.example`
  - `git diff -- DEPLOY.md frontend/README.md docs/mvp-mentoria/frontend-deployment-readiness-checklist.md frontend/.env.production.example _bmad-output/implementation-artifacts/4-2d-batch-b-spa-rewrite-and-env-separation.md`
- No runtime tests are required unless doc changes expose an implementation inconsistency.

## References

- `_bmad-output/implementation-artifacts/4-2d-batch-b-spa-rewrite-and-env-separation.md`
- `frontend/vercel.json`
- `DEPLOY.md`
- `frontend/README.md`
- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- `frontend/.env.production.example`

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

TBD (populate during implementation)

### Completion Notes List

TBD (populate during implementation)

### File List

TBD (populate during implementation)
