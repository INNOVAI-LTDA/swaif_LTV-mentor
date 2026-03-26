# Story: Batch G - Cache Strategy (Measured) + Local Vercel CLI Parity (Docs)

Status: review
Owner: dmene
Date: 2026-03-26

## Problem Statement

We want a stable, reproducible deployment workflow on Vercel without prematurely “optimizing” caching based on guesses. Vite already emits hashed assets under `/assets/*`, which generally supports long-lived caching naturally. The risky part is `index.html` caching: if it is cached too aggressively, users can get stuck on old asset references after a deploy.

Separately, local parity with Vercel’s runtime (Preview/Production env vars and routing behavior) is currently undocumented. Without a documented Vercel CLI workflow (`vercel link`, `vercel env pull`), operators and developers can accidentally test with mismatched env configuration.

Batch G documents a measurement-first caching posture and standardizes a local Vercel CLI workflow without introducing speculative caching micro-optimizations.

## Goal (Batch G Only)

1. Review cache strategy only when measured:
   - Document how to measure current cache headers for `index.html` and hashed assets in Preview/Production.
2. Keep `index.html` caching conservative unless there is measured reason to optimize.
3. Let Vite hashed assets handle most asset caching naturally.
4. Standardize local parity with Vercel CLI by documenting:
   - `npm i -g vercel`
   - `vercel link`
   - `vercel env pull`

## Constraints / Guardrails (Binding)

- Keep diffs narrow: documentation-only by default.
- Do not introduce premature cache header changes or micro-optimizations.
- Avoid unrelated deployment changes (no redirects/headers/CSP/HSTS/routing changes in this batch).

## Current State (Evidence)

- No repo-level caching policy is defined (no `vercel.json` headers yet).
- No Vercel CLI workflow is referenced in `docs/` or `frontend/README.md`.
- `frontend/dist/index.html` references hashed assets under `/assets/`, consistent with Vite’s cache-busting model.

## Scope

### In Scope (Exact Changes)

1. Add a small “Cache posture (measured)” section to `DEPLOY.md`:
   - Define what to measure (response headers for `index.html` and a hashed asset).
   - Define what “conservative index.html caching” means operationally (avoid long max-age).
   - State that we will not change cache headers unless measurement shows a need.
2. Add a “Local parity with Vercel CLI” section to `DEPLOY.md` (or `frontend/README.md` if that is the operator entrypoint):
   - install Vercel CLI
   - link project
   - pull env vars into a local file for consistent builds/tests
   - minimal “how to run locally” guidance (do not change code)

### Out of Scope (Explicit)

- Any actual cache header configuration in `frontend/vercel.json` unless:
  - a measurement section is executed and recorded, and
  - a concrete, justified need is documented in the same change.
- Any changes to routing/rewrites, redirects, security headers, CSP, or HSTS.

## Acceptance Criteria (Must Pass)

1. Cache policy is only documented if intentionally optimized:
   - `DEPLOY.md` states that caching changes require measurement evidence.
   - No cache headers are added/changed in config unless accompanied by measurement + justification (this batch defaults to docs-only).
2. Local Vercel CLI workflow is documented and reproducible:
   - `DEPLOY.md` includes the exact commands:
     - `npm i -g vercel`
     - `vercel link`
     - `vercel env pull`
   - The doc states where the env file lands and how to use it without committing secrets.
3. No premature caching micro-optimizations are introduced:
   - No new cache-related config changes absent measurement evidence.

## Implementation Notes (Smallest Safe Patch)

- Prefer consolidating deploy-operator workflow into root `DEPLOY.md` to avoid duplicating checklists across docs.
- Treat `vercel env pull` output as a local artifact that must not be committed; mention `.gitignore` only if currently missing coverage (change only if necessary).
- If the repo uses multiple environments (Preview/Production), document how to pull each (or how Vercel CLI selects).

## Files / Modules Likely Affected

- Update: `DEPLOY.md`
- Optional update: `frontend/README.md` (only if DEPLOY.md is not the chosen home for operator workflow)
- Optional update: `.gitignore` (only if the pulled env filename is not already ignored and we decide to standardize a specific filename)

## Tests / Validation

Docs-only expected; validate by executing the commands locally:

1. Install and link:
   - `npm i -g vercel`
   - `vercel link`
2. Pull env vars:
   - `vercel env pull` (confirm it creates the expected local env file and contains only the intended values)
3. Build with pulled env:
   - `cd frontend && npm run build`
4. Cache measurement (once deployed):
   - `curl -I https://www.yourdomain.com/` (index.html)
   - `curl -I https://www.yourdomain.com/assets/<hash>.js` (hashed asset)

## Release Risks If Not Implemented

- Teams may “optimize” caching blindly and accidentally cache `index.html` too long, causing stale deployments.
- Lack of Vercel CLI parity increases env mismatch risk between local validation and Preview/Production behavior.

## Dev Agent Record

### Debug Log
- 2026-03-26: documented cache measurement posture and Vercel CLI parity workflow.

### Completion Notes
- Added guidance in `DEPLOY.md` on measuring cache headers (index.html vs hashed assets) before making changes; no cache config altered.
- Documented Vercel CLI parity steps (`npm i -g vercel`, `vercel link`, `vercel env pull .env.local`, local build/test with pulled envs).

## File List
- `DEPLOY.md`
- `_bmad-output/implementation-artifacts/batch-g-cache-measurement-and-vercel-cli-parity.md`

## Change Log
- 2026-03-26: Batch G cache measurement posture and Vercel CLI parity workflow documented.
