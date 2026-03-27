# Batch D (Custom Domain, Canonical Host, Redirects, Smoke Checks) - Current State

Scope: document only what is true in the repo today that impacts Batch D (custom domain, canonical host policy, redirects, trailing slash behavior, and smoke-test checklist posture).

## Custom Domain Connection (Current)

There is no versioned artifact in this repo that proves a custom domain is already connected in Vercel (domain attachment and DNS are Vercel/DNS-side configuration).

What is versioned today:

- `frontend/vercel.json` exists and is the only committed Vercel config file.
- No root `vercel.json` exists at repo root (Vercel Root Directory is expected to be `frontend` per `DEPLOY.md`).

Implication: whether a custom domain is connected must currently be verified in the Vercel dashboard and in DNS, not in Git.

## Canonical Host Policy (Current)

No canonical-host policy is versioned in `frontend/vercel.json` today (no redirects that enforce `www` or apex as canonical).

Implication: if a custom domain is added, `www` canonicalization is not currently guaranteed by repo-config. Any canonicalization would be ad hoc (Vercel dashboard rules) until Batch D versions it.

## Redirect Rules (Current)

`frontend/vercel.json` currently contains only the SPA rewrite:

- `rewrites: [{ "source": "/(.*)", "destination": "/index.html" }]`

There are no committed host-level redirects (no `redirects` in `frontend/vercel.json`, no `_redirects` file, no other proxy config in repo).

## Trailing Slash Behavior (Current)

There is no trailing-slash policy committed (no `trailingSlash` field in `frontend/vercel.json`).

Implication: trailing slash behavior is currently whatever the hosting platform defaults to, and it is not standardized/locked by this repo yet.

## `DEPLOY.md` Status (Current)

`DEPLOY.md` exists and documents the Vercel settings for Batch B:

- Root Directory: `frontend`
- Framework Preset: Vite
- Build Command: `npm run build`
- Output Directory: `dist`

`DEPLOY.md` also contains a hosted smoke list focused on SPA refresh/deep-links, but it does not yet include any custom-domain canonicalization or redirect verification.

## Files Likely Affected By Batch D

- `frontend/vercel.json`
  - add canonical-host redirects (www or apex)
  - standardize redirect behavior (and ensure it does not conflict with SPA rewrite)
  - optionally standardize trailing slash policy if desired
- `DEPLOY.md`
  - add Batch D hosted smoke checklist: canonical host, redirects, trailing slash expectations
- `docs/client-launch-runbook.md`
  - ensure operator procedure includes the new hosted-domain and redirect checks (if this runbook is used as operator source of truth)
- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
  - if this remains a release gate, add explicit pass/fail items for domain + redirects + smoke refresh routes

## Validation Steps Needed For Batch D (Not Yet Versioned)

DNS / Vercel:

1. Confirm the custom domain is added to the Vercel project (Production) and has a valid TLS certificate.
2. Confirm Preview behavior expectations (Preview URLs usually remain `*.vercel.app`; custom preview domains are optional).

Hosted redirect + canonicalization (after Batch D versions rules):

1. Verify canonical host:
   - `https://yourdomain.com/` redirects to `https://www.yourdomain.com/` (or the reverse), consistently.
2. Verify status codes:
   - redirects are stable (no loops) and use a permanent code (`301` or `308`) where appropriate.
3. Verify path preservation:
   - canonicalization preserves the full path/query (example: `/login?next=%2Fapp%2Fadmin` remains intact).
4. Verify trailing slash posture (if standardized):
   - `/login` and `/login/` behave as intended (either one redirects to the other, or both work without ambiguity).

Hosted SPA smoke (must remain valid after redirects):

1. Hard-refresh these routes on the final canonical host:
   - `/`
   - `/login`
   - `/dashboard`
   - `/app/admin`
   - `/app/matriz-renovacao`
   - `/app/aluno`
2. Confirm each refresh returns the SPA shell (no host `404`) and the app loads.

