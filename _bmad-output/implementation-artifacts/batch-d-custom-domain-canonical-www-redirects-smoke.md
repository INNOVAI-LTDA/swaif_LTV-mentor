# Story: Batch D - Custom Domain + Canonical WWW + Redirect Policy + Smoke Checklist

Status: review
Owner: dmene
Date: 2026-03-26

## Problem Statement

We are approaching first stable deployment on Vercel. The repo currently has no committed host-level redirect policy and no operator-facing, single source of truth for “what URL is canonical” and “what checks prove the deployment is good”.

Domain configuration (custom domain + TLS) is primarily a Vercel/operator action, but the canonical hostname rules, apex-to-www redirect behavior, and trailing slash policy must be explicit, documented, and testable so releases do not drift across environments.

This batch standardizes the domain posture and adds a deploy smoke checklist without introducing CSP/HSTS work (reserved for Batch F).

## Goal (Batch D Only)

1. Connect the real client-facing custom domain (operator action; document it).
2. Make `www` the canonical hostname.
3. Redirect apex -> `www` (permanent redirect).
4. Define a trailing slash policy and document expected behavior.
5. Add a deploy smoke-test checklist to `DEPLOY.md` containing the required checks.

## Constraints / Guardrails (Binding)

- Keep diffs narrow; no opportunistic refactors.
- Avoid mixing in CSP/HSTS (Batch F).
- Preserve app behavior (routing, shells, auth, adapters) outside of host canonicalization.
- Prefer versioned Vercel config (`frontend/vercel.json`) for host rules where possible, but do not attempt to encode “domain connection” as code (that is Vercel UI / DNS).

## Current State (Evidence)

- No `DEPLOY.md` exists yet (Batch A introduces it).
- No `frontend/vercel.json` exists yet (Batch A introduces it).
- Docs already track that domain/TLS and rewrite model are pending operator confirmation:
  - `docs/production-release-tracker.md` includes “Confirm client domain, subpath strategy, TLS, and reverse-proxy rewrite model” as `in_progress`.
  - `docs/client-launch-runbook.md` lists domain/TLS confirmation as a precondition.

## Scope

### In Scope (Exact Changes)

1. Update `DEPLOY.md` (created in Batch A) to document:
   - the required custom domain (placeholder values + where to set it in Vercel)
   - canonical hostname policy: `https://www.yourdomain.com` is canonical
   - apex -> www redirect behavior (status code and preservation of path/query)
   - trailing slash policy for the canonical host
2. Implement redirect policy in Vercel config **without mixing in CSP/HSTS**:
   - Update `frontend/vercel.json` to add redirects for apex -> www if the project will also serve apex.
   - If redirecting apex requires Vercel domain settings rather than config (common), document that explicitly and keep config minimal.
3. Define a trailing slash policy (document first, enforce only if safe/needed):
   - Choose the smallest consistent policy with the current app:
     - Frontend base path normalization supports `/` and `/<subpath>/`.
     - Router basename uses a non-trailing-slash variant for non-root.
   - If enforcing via Vercel config, keep it limited to a simple redirect rule (no rewrites/headers here beyond what earlier batches add).
4. Add a deploy smoke-test checklist to `DEPLOY.md` containing:
   - Home page loads
   - Console has no 404 asset errors
   - API base URL points to intended backend
   - Nested route refresh works
   - Login/auth flow works
   - Custom domain works
   - Apex to www redirect works
   - Security headers exist (baseline headers from Batch E)
   - Preview deploy works from PR

### Out of Scope (Explicit)

- CSP and HSTS (Batch F).
- Backend CORS changes (Batch C).
- Cache strategy (Batch G).
- UI/layout changes.

## Acceptance Criteria (Must Pass)

1. Canonical URL policy is explicit:
   - `DEPLOY.md` clearly states canonical host is `https://www.yourdomain.com` and what to expect on apex.
2. Redirect behavior is documented and testable:
   - `DEPLOY.md` includes the exact commands/URLs to verify apex -> www redirect and trailing slash policy.
3. Smoke-test checklist exists in `DEPLOY.md` and is operator-executable.
4. Domain behavior is operationally clear:
   - `DEPLOY.md` states what is configured in Vercel UI/DNS vs what is versioned in `frontend/vercel.json`.

## Implementation Notes (Smallest Safe Patch)

- Custom domain connection is a Vercel UI + DNS step; document it with placeholders and explicit operator actions.
- If Vercel automatically handles apex <-> www redirects based on which domains are added, prefer that over complex config rules; use `frontend/vercel.json` only for what must be versioned and deterministic.
- Keep redirect rules minimal and do not introduce security headers here (they’re Batch E) beyond “verify they exist” in smoke checklist.

## Files / Modules Likely Affected

- Update: `DEPLOY.md`
- Update (if needed): `frontend/vercel.json`
- Optional (docs-as-input alignment only, if referenced): `docs/production-release-tracker.md`

## Tests / Validation

No unit tests expected (docs/config only). Validation is operational:

1. Canonical host:
   - Open `https://www.yourdomain.com/` and confirm app loads.
2. Apex -> www redirect:
   - `curl -I https://yourdomain.com/` returns 308/301 to `https://www.yourdomain.com/` (preserving path/query).
3. Trailing slash policy:
   - `curl -I https://www.yourdomain.com/login` and `curl -I https://www.yourdomain.com/login/` behave per documented policy.
4. App functional smoke:
   - Validate login and protected navigation.
   - Refresh nested route under `/app/*` (requires SPA rewrite from Batch B).
5. Preview deploy:
   - Confirm PR preview deploy loads and passes the same smoke subset; if preview origins are used against a shared backend, confirm backend CORS allowlist includes preview origin(s) (Batch C).

## Release Risks If Not Implemented

- Operators may publish inconsistent hostnames (apex sometimes, www sometimes), causing broken cookies/storage expectations, mixed-origin CORS issues, and confusing client-facing URLs.
- Lack of a single smoke checklist increases risk of “green build, broken deploy” (especially deep refresh and asset base-path issues).

## Dev Agent Record

### Debug Log
- 2026-03-26: documentation-only domain posture update (no automated tests required for this batch).

### Completion Notes
- Documented canonical host (`https://www.yourdomain.com`), apex-to-www redirect expectation, trailing-slash behavior, and deploy smoke checklist in `DEPLOY.md`.
- Clarified operator posture in `docs/production-release-tracker.md` to include canonical host and apex redirect requirements.
- Kept `frontend/vercel.json` unchanged; apex redirect is enforced via Vercel Domains UI per the documented policy.

## File List
- `DEPLOY.md`
- `docs/production-release-tracker.md`
- `_bmad-output/implementation-artifacts/batch-d-custom-domain-canonical-www-redirects-smoke.md`

## Change Log
- 2026-03-26: Batch D custom domain + canonical www policy documented with smoke checklist.
