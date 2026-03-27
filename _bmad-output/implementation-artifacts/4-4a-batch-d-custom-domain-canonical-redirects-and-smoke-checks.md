# Story 4.4a: batch-d-custom-domain-canonical-redirects-and-smoke-checks (Batch D)

Status: ready-for-dev

## Story

As a release operator,
I want the hosted Vercel deployment to use the real client-facing custom domain with a single canonical hostname (`www`), standardized redirect behavior (including trailing slashes), and an explicit post-deploy smoke checklist,
so that go-live is operationally reproducible and we can validate routing and asset behavior on the real host without guessing.

## Background (Current State Snapshot)

- Frontend deploy root is `frontend/` (documented in `DEPLOY.md`).
- `frontend/vercel.json` exists and currently includes only the SPA rewrite for deep-link refresh:
  - `rewrites: [{ "source": "/(.*)", "destination": "/index.html" }]`
- There are no committed canonical-host redirects or trailing-slash rules yet.
- `DEPLOY.md` already contains hosted refresh validation routes (Batch B) but does not cover custom domain + canonicalization checks.

Source: `docs/mvp-mentoria/batch-d-custom-domain-redirects-current-state.md`.

## Requirements (Batch D)

1. Connect the real client-facing custom domain (Vercel dashboard + DNS).
2. Make `www` the canonical hostname.
3. Redirect apex to `www`.
4. Define trailing slash policy.
5. Add deploy smoke-test checklist to `DEPLOY.md` containing:
   - Home page loads
   - Console has no 404 asset errors
   - API base URL points to intended backend
   - Nested route refresh works
   - Login/auth flow works
   - Custom domain works
   - Apex to www redirect works
   - Security headers exist
   - Preview deploy works from PR

## Acceptance Criteria

1. Canonical URL policy is explicit and versioned.
2. Redirect behavior is documented and testable.
3. `DEPLOY.md` contains a concrete post-deploy smoke checklist that includes custom domain and redirect checks.
4. Domain behavior is operationally clear (what is configured in Git vs Vercel dashboard/DNS).

## Decisions (Lock Before Implementing)

- Canonical host: `https://www.<domain>` is canonical.
- Apex redirect: `https://<domain>` permanently redirects to `https://www.<domain>`, preserving full path and query string.
- Trailing slash policy (choose one and keep consistent):
  - Recommended for SPA: no enforced trailing slash redirects on application routes (to avoid surprising path changes).
  - If enforcing trailing slash normalization, prefer a single consistent behavior (redirect one form to the other) and verify it does not interfere with the SPA rewrite.

## Tasks / Subtasks

### Task 1: Version Canonical Host Redirects (AC: 1, 2)

- [ ] Update `frontend/vercel.json` to add Vercel `redirects` that enforce `www` canonicalization:
  - Redirect apex to www using a permanent redirect code (`308` preferred).
  - Preserve path and query string.
- [ ] Keep the SPA rewrite intact and ensure redirect rules run before the SPA rewrite.
- [ ] Do not add CSP/HSTS here.

Notes:
- Vercel supports `redirects` in `vercel.json` and a `has: [{ type: "host", value: "..." }]` matcher. Use that rather than hardcoding every path.

### Task 2: Define Trailing Slash Policy (AC: 2)

- [ ] Decide whether to set `trailingSlash` in `frontend/vercel.json`.
- [ ] If set, document why (and validate it does not cause loops or break SPA refresh).

### Task 3: Update Operator Docs (AC: 3, 4)

- [ ] Update `DEPLOY.md`:
  - Add a Batch D section clarifying:
    - Custom domain attachment is configured in Vercel dashboard + DNS.
    - Canonical host and redirects are versioned in `frontend/vercel.json`.
  - Add a post-deploy smoke checklist (see list below) and make it explicit it must be run on:
    - Vercel Preview URL (PR)
    - Vercel Production custom domain
- [ ] Optionally, if `docs/client-launch-runbook.md` is the operator source of truth, add a short “Custom Domain + Canonical Host” verification section that mirrors `DEPLOY.md`.

## Post-Deploy Smoke Checklist (Must Be Added To `DEPLOY.md`)

1. Home page loads on Production custom domain.
2. Browser console shows no 404 asset errors (filter for `Failed to load resource`).
3. API base URL is the intended backend:
   - Confirm network requests go to `VITE_API_BASE_URL` and not `localhost/127.0.0.1`.
4. Nested route refresh works (no host `404`):
   - Refresh: `/`, `/login`, `/dashboard`, `/app/admin`, `/app/matriz-renovacao`, `/app/aluno`.
5. Login/auth flow works:
   - Login -> redirected to the correct app surface; protected routes behave as expected.
6. Custom domain works:
   - Cert is valid; no mixed-content warnings; correct host in address bar.
7. Apex to www redirect works:
   - Visiting `https://<apex>` lands on `https://www.<apex>` and preserves path/query.
8. Security headers exist (baseline presence check only; do not add/validate CSP/HSTS here):
   - Confirm headers like `x-content-type-options`, `referrer-policy`, etc. are present if already configured.
9. Preview deploy works from PR:
   - Repeat key refresh checks on the Preview URL and confirm API env is Preview-scoped.

## Non-Goals / Guardrails

- Do not introduce CSP or HSTS (Batch F) in this story.
- Do not add or change backend CORS here (Batch C already covers it).
- Keep diffs narrow: `frontend/vercel.json` + `DEPLOY.md` (+ optionally one operator doc).

## Validation Steps

Repo-level:

1. Sanity-check `frontend/vercel.json` is valid JSON.
2. If any docs changed: run a quick grep to ensure the canonical host policy is stated once and consistently.

Hosted:

1. Deploy Preview (PR) and Production.
2. Execute the `DEPLOY.md` smoke checklist on both.
3. Explicitly validate the apex->www redirect and absence of redirect loops.

