# Story 4.2b: batch-a-deploy-contract-clarity-fixes

Status: done

## Story

As a release operator,
I want the Batch A Vercel deploy contract documented consistently across the repo,
so that root-path deployment, environment expectations, and the pending SPA rewrite requirement are unambiguous before hosted validation continues.

## Acceptance Criteria

1. `DEPLOY.md` states explicitly that Batch A is not host-ready until Batch B adds the Vercel SPA rewrite for deep-link refresh behavior.
2. `DEPLOY.md` includes the exact Vercel rewrite snippet that Batch B is expected to add next for the Vite SPA.
3. `DEPLOY.md` states explicitly that the required build variables must be configured in both Vercel Preview and Production until Batch B introduces distinct environment separation.
4. Operator-facing docs/examples no longer imply that `/accmed/` or `/cliente/` is the default Vercel deployment base path for Batch A.
5. `frontend/.env.client.accmed.example` keeps the current local baseline intact but is marked clearly as local-only so operators do not reuse it as the hosted Vercel contract.

## Tasks / Subtasks

- [x] Task 1 (AC: 1, 2, 3)
  - [x] Update `DEPLOY.md` to say Batch A is repo-prepared but not host-ready until Batch B adds the SPA rewrite.
  - [x] Add the exact Vercel rewrite snippet from the current Vercel Vite SPA guidance for the next batch:
    - `rewrites: [{ source: "/(.*)", destination: "/index.html" }]`
  - [x] Add an explicit operator note that `VITE_DEPLOY_TARGET`, `VITE_APP_BASE_PATH`, `VITE_API_BASE_URL`, and `VITE_CLIENT_CODE` must be set in both Vercel Preview and Production until Batch B separates them.
- [x] Task 2 (AC: 4)
  - [x] Update `frontend/README.md` so the deploy guidance reflects root-path Vercel deployment as the active Batch A contract, while keeping subpath support documented as an optional capability rather than the assumed default.
  - [x] Update `frontend/.env.example` so the published-client example uses `VITE_APP_BASE_PATH=/` instead of a subpath example.
  - [x] Update `docs/client-launch-runbook.md` so `/accmed/` and `/cliente/` are clearly framed as local/staging examples, not the current Vercel root contract.
  - [x] Update `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` so the routing/hosting notes do not conflict with the new Batch A root-path contract.
- [x] Task 3 (AC: 5)
  - [x] Add a clear local-only warning near `frontend/.env.client.accmed.example` explaining that it is a local validation baseline and must not be copied directly to hosted Vercel environments.
  - [x] Keep the existing `/accmed/` value in that file unchanged to avoid disturbing the current local evidence baseline.

## Dev Notes

### Scope guardrails (do not expand)

- This is a documentation/template alignment story only.
- Do not add the actual SPA rewrite to `frontend/vercel.json` here; that belongs to Batch B.
- Do not change runtime code, router behavior, backend CORS, headers, CSP, or HSTS here.
- Do not change the current local validation baseline beyond clarifying that it is local-only.

### Why this story exists

Batch A introduced a root-path Vercel contract in `DEPLOY.md`, but the existing operator guidance across the repo still teaches subpath deployment (`/accmed/`, `/cliente/`) as the working example. That creates an operator-facing contradiction. Separately, Vercel's current Vite SPA guidance says deep linking does not work out of the box and requires a rewrite to `index.html`, so the current deploy-preparation batch must say clearly that host readiness is deferred until Batch B.

### Relevant Files

- `DEPLOY.md`
- `frontend/README.md`
- `frontend/.env.example`
- `frontend/.env.client.accmed.example`
- `docs/client-launch-runbook.md`
- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- `frontend/vercel.json`
- `docs/mvp-mentoria/vercel-batch-a-current-state.md`

### Testing standards summary

- This story changes docs/templates only.
- Validation should be limited to reviewing the operator contract for consistency and, if desired, re-running the existing frontend build commands already documented in `DEPLOY.md`.
- Do not introduce unrelated code or test changes.

### References

- [Source: DEPLOY.md]
- [Source: frontend/README.md]
- [Source: frontend/.env.example]
- [Source: frontend/.env.client.accmed.example]
- [Source: docs/client-launch-runbook.md]
- [Source: docs/mvp-mentoria/frontend-deployment-readiness-checklist.md]
- [Source: https://vercel.com/docs/frameworks/frontend/vite]

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- `rg -n "/cliente/|/accmed/|VITE_APP_BASE_PATH=/|Preview|Production|rewrites|index.html|local-only" DEPLOY.md frontend/README.md frontend/.env.example frontend/.env.client.accmed.example docs/client-launch-runbook.md docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- `git diff -- DEPLOY.md frontend/README.md frontend/.env.example frontend/.env.client.accmed.example docs/client-launch-runbook.md docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`

### Completion Notes List

- `DEPLOY.md` now states Batch A is not host-ready until Batch B adds the Vercel SPA rewrite and includes the exact rewrite snippet to apply next.
- `DEPLOY.md` now states the required Vercel build vars must be present in both `Preview` and `Production` until Batch B separates them.
- `frontend/README.md` and `frontend/.env.example` now present `/` as the active Vercel root-path contract for this batch.
- `docs/client-launch-runbook.md` and `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` now preserve `/accmed/` as local-only baseline evidence while making the hosted Vercel contract explicit.
- `frontend/.env.client.accmed.example` keeps `/accmed/` unchanged but now warns operators not to reuse it directly for hosted Vercel deployment.

### File List

- `DEPLOY.md`
- `frontend/README.md`
- `frontend/.env.example`
- `frontend/.env.client.accmed.example`
- `docs/client-launch-runbook.md`
- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
