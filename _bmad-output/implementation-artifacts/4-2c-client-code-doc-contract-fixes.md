# Story 4.2c: client-code-doc-contract-fixes

Status: review

## Story

As a release operator,
I want every published `VITE_DEPLOY_TARGET=client` example to include the required `VITE_CLIENT_CODE` and the AccMed template flow labeled correctly as local-only bootstrap evidence,
so that the Batch A deploy contract is executable in practice and operators do not confuse the local `/accmed/` baseline with the hosted Vercel root-path contract.

## Acceptance Criteria

1. Every operator-facing `VITE_DEPLOY_TARGET=client` command/example in `frontend/.env.example` includes `VITE_CLIENT_CODE=<client_code>`.
2. Every operator-facing `VITE_DEPLOY_TARGET=client` command/example in `docs/client-launch-runbook.md` includes `VITE_CLIENT_CODE=<client_code>`.
3. `frontend/README.md` states explicitly that the `AccMed` template flow is for local validation/bootstrap only and is not the hosted Vercel contract.
4. No runtime code changes are made.
5. `frontend/vercel.json` is not changed in this batch.

## Tasks / Subtasks

- [x] Task 1 (AC: 1)
  - [x] Update the published client example in `frontend/.env.example` to include `VITE_CLIENT_CODE=<client_code>`.
  - [x] Keep the example aligned with the current hosted Batch A root-path contract by leaving `VITE_APP_BASE_PATH=/`.
- [x] Task 2 (AC: 2)
  - [x] Update the current local `client`-target frontend build command in `docs/client-launch-runbook.md` to include `VITE_CLIENT_CODE=accmed`.
  - [x] Update the hosted frontend build example in `docs/client-launch-runbook.md` to include `VITE_CLIENT_CODE=<client_code>`.
  - [x] Preserve the existing distinction between the local `/accmed/` validation baseline and the hosted Vercel `/` contract.
- [x] Task 3 (AC: 3, 4, 5)
  - [x] Add one explicit note near the `Template cliente AccMed` section in `frontend/README.md` stating that this flow is for local validation/bootstrap only.
  - [x] State clearly that hosted Vercel deployment must follow the Batch A contract documented in `DEPLOY.md`.
  - [x] Do not change runtime code, router behavior, env parsing, or `frontend/vercel.json`.

## Dev Notes

### Scope guardrails (do not expand)

- This is a docs/template correction story only.
- Do not modify `frontend/vercel.json`.
- Do not add SPA rewrites here; that remains Batch B.
- Do not change runtime code, environment validation logic, or router behavior.
- Do not alter the `/accmed/` local template baseline beyond clarifying how operators should interpret it.

### Why this story exists

Batch A and the follow-up clarity patch established `/` as the hosted Vercel base-path contract, but some operator-facing examples still omit `VITE_CLIENT_CODE` even though `VITE_DEPLOY_TARGET=client` requires it. Separately, the `AccMed` template flow in `frontend/README.md` still reads like a normal hosted build path even though the template file is now explicitly local-only. This story closes those remaining contract gaps without expanding scope into runtime or hosting behavior.

### Relevant Files

- `frontend/.env.example`
- `docs/client-launch-runbook.md`
- `frontend/README.md`
- `frontend/.env.client.accmed.example`
- `DEPLOY.md`
- `frontend/src/shared/config/envContract.ts`

### Testing standards summary

- This story changes docs/templates only.
- Validation should be limited to contract consistency checks in the edited files.
- Suitable validation includes targeted text search for `VITE_DEPLOY_TARGET=client`, `VITE_CLIENT_CODE`, `Template cliente AccMed`, and `Vercel`.
- Do not add or modify automated tests for this story.

### References

- [Source: frontend/.env.example]
- [Source: docs/client-launch-runbook.md]
- [Source: frontend/README.md]
- [Source: frontend/.env.client.accmed.example]
- [Source: DEPLOY.md]
- [Source: frontend/src/shared/config/envContract.ts]

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- `rg -n "VITE_DEPLOY_TARGET=client|VITE_CLIENT_CODE|Template cliente AccMed|DEPLOY.md" frontend/.env.example docs/client-launch-runbook.md frontend/README.md`
- `git diff -- frontend/.env.example docs/client-launch-runbook.md frontend/README.md _bmad-output/implementation-artifacts/4-2c-client-code-doc-contract-fixes.md`

### Completion Notes List

- Added `VITE_CLIENT_CODE=<client_code>` to the published client example in `frontend/.env.example`.
- Added `VITE_CLIENT_CODE=accmed` to the current local `client` build example and `VITE_CLIENT_CODE=<client_code>` to the hosted build example in `docs/client-launch-runbook.md`.
- Added an explicit note in `frontend/README.md` that the `AccMed` template flow is for local validation/bootstrap only and not the hosted Vercel contract.
- Left runtime code and `frontend/vercel.json` unchanged.

### File List

- `frontend/.env.example`
- `docs/client-launch-runbook.md`
- `frontend/README.md`
- `_bmad-output/implementation-artifacts/4-2c-client-code-doc-contract-fixes.md`

## Change Log

- 2026-03-26: Implemented the docs-only client-code contract fixes and marked the story ready for review.
