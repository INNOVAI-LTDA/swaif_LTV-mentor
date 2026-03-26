# Vercel Deployment Baseline (Batch A)

This repo versions the Vercel frontend deploy posture. Batch A establishes the minimal root-deploy baseline only.

## Required Vercel Project Settings
- Root Directory: `frontend`
- Framework Preset: `Vite`
- Build Command: `npm run build`
- Output Directory: `dist`
- Project Config: `frontend/vercel.json` (kept minimal on purpose for Batch A)

## Environment
- `VITE_APP_BASE_PATH=/` (root-path deployment posture). Subpath deploys are **not** assumed; only configure a subpath in later batches with an explicit justification.
- `VITE_API_BASE_URL` set to the target backend URL for the environment (no localhost in hosted environments).
- Do not place secrets in `VITE_*` variables; they are shipped to the browser. Use server-side env vars for anything sensitive.

## Scope Guardrails
- No SPA rewrites/redirects/headers are included here (handled in Batch B and later).
- Keep deploy behavior versioned in Git; avoid ad-hoc Vercel UI drift.

## Validation Before Deploy
1) `cd frontend && npm run build`
2) (Optional) `cd frontend && npm run test`