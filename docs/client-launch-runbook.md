# Client Launch Runbook

Date: 2026-03-19

## Scope

This runbook covers the current release posture of the app as a single-server pilot deployment. It is written for an operator who did not implement the feature locally.

## Current Local Baseline

Use this parameter set for the current local dry-run baseline:

| Input | Current local value |
| ----- | ------------------- |
| Frontend origin | `http://127.0.0.1:4173` |
| Frontend base path | `/accmed/` |
| Backend API URL | `http://127.0.0.1:8000` |
| Backend APP_ENV | `local` |
| Backend CORS_ALLOW_ORIGINS | `http://127.0.0.1:4173` |
| Client display name | `Acelerador Médico (AccMed)` |
| Product name | `Gamma` |

This is the current local baseline only. Replace the origin, backend URL, and any final branded assets when moving to the first real hosted environment.

## Required Inputs

Fill these values before deploying:

| Input | Example | Required |
| ----- | ------- | -------- |
| Frontend origin | `https://cliente.example.com` | yes |
| Frontend base path | `/cliente/` | yes |
| Backend API URL | `https://api.cliente.example.com` | yes |
| Backend APP_ENV | `production` | yes |
| Backend CORS_ALLOW_ORIGINS | `https://cliente.example.com` | yes |
| Client display name | `Nome do Cliente` | yes |
| Product name | `Nome do Produto` | yes |
| Branding asset paths | `/branding/logo.png` | yes |
| Deploy operator | `preencher` | yes |

## Preconditions

- Frontend release branch is green on `npm run test`
- Frontend build is green for the selected deploy target
- Backend deploy config is validated
- Client branding assets and env values are ready
- Target host, domain, TLS, and SPA rewrite strategy are confirmed
- `docs/production-release-tracker.md` is filled for this release candidate

## Current Pilot Assumptions

- Backend persistence is still JSON-file based on local disk
- Deployment is single-server only
- Backup and restore must be validated before client go-live
- The published frontend path now keeps mentor-demo isolated by default; any mentor-demo usage is local/internal only

## JSON Pilot Operating Model

The current backend persistence model is acceptable only as a constrained initial pilot. Treat it as an operating model with explicit limits, not as scalable production architecture.

This JSON pilot is acceptable only when all of the following remain true:

- exactly one active backend instance writes the JSON stores
- persisted data stays on local disk attached to that single server
- backup and restore rehearsal evidence is current and recorded in `docs/production-release-tracker.md`
- restore is performed only inside a controlled maintenance window
- expected client usage is low-to-moderate and operationally supervised
- rollback means restoring JSON snapshots, not failing over to a second live node

This JSON pilot is not acceptable if any of the following become true:

- you need more than one backend instance
- you need shared writes across multiple hosts or containers
- you need zero-downtime restore expectations
- you expect sustained high write concurrency or materially larger data volume
- the client requires stronger durability, audit, or recovery guarantees than snapshot-based recovery can provide

If any of those conditions apply, stop and escalate to a database-backed persistence migration before remote staging or broader client rollout.

## Local Pre-Staging Validation

Run this sequence before touching a remote host:

1. Start the backend locally with explicit pilot posture.
2. Capture one storage snapshot.
3. Verify the snapshot manifest.
4. Validate the frontend against the local backend with `VITE_DEPLOY_TARGET=client` style envs.
5. Confirm startup logs show `app_env`, `cors_origins`, `mentor_demo_routes`, `mentor_demo_policy`, `storage_root`, and `backup_dir`.

The maintenance utility now uses a shared storage I/O lock stored in a writable OS temp location and keyed to the resolved JSON store set, so repository-backed JSON writes from other Python processes wait while `backup` or `restore` is running even if backup-dir config differs between processes or stores live in different directories. This reduces mixed-state risk, but restore is still a best-effort multi-file operation under the current JSON pilot model. Run restore inside a controlled maintenance window and treat any rollback failure as a manual-intervention event.

### Local backend startup

```bash
APP_ENV=local ^
CORS_ALLOW_ORIGINS=http://127.0.0.1:4173 ^
ENABLE_MENTOR_DEMO_ROUTES=true ^
ALLOW_REMOTE_MENTOR_DEMO_ROUTES=false ^
STORAGE_BACKUP_DIR=backups ^
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Current local frontend build command

```bash
VITE_DEPLOY_TARGET=client ^
VITE_API_BASE_URL=http://127.0.0.1:8000 ^
VITE_APP_BASE_PATH=/accmed/ ^
VITE_CLIENT_NAME=Acelerador Médico (AccMed) ^
VITE_APP_NAME=Gamma ^
VITE_APP_TAGLINE=Validacao local controlada ^
VITE_SHELL_SUBTITLE=Piloto local ^
VITE_BRANDING_ICON_PATH=branding/app-icon.png ^
VITE_BRANDING_LOGO_PATH=branding/app-logo.png ^
VITE_BRANDING_LOGIN_HERO_PATH=branding/login-hero.png ^
VITE_ENABLE_DEMO_MODE=false ^
VITE_ENABLE_INTERNAL_MENTOR_DEMO=false ^
npm run build
```

### Local backup and restore commands

Create snapshot:

```bash
py -m app.operations.storage_maintenance backup
```

Verify snapshot:

```bash
py -m app.operations.storage_maintenance verify backend/backups/snapshot-YYYYMMDDTHHMMSSZ
```

Restore snapshot:

```bash
py -m app.operations.storage_maintenance restore backend/backups/snapshot-YYYYMMDDTHHMMSSZ
```

Do not move to staging until one local backup plus restore rehearsal has completed successfully.
If restore reports that rollback could not fully recover the pre-restore snapshot, stop immediately and inspect the rollback snapshot path before restarting the app.

## Frontend Build

Use the target client values, not local placeholders:

```bash
VITE_DEPLOY_TARGET=client ^
VITE_API_BASE_URL=https://api.cliente.example.com ^
VITE_APP_BASE_PATH=/cliente/ ^
VITE_CLIENT_NAME=Nome do Cliente ^
VITE_APP_NAME=Nome do Produto ^
VITE_APP_TAGLINE=Mensagem curta ^
VITE_SHELL_SUBTITLE=Operacao inicial ^
VITE_BRANDING_ICON_PATH=/branding/favicon.png ^
VITE_BRANDING_LOGO_PATH=/branding/logo.png ^
VITE_BRANDING_LOGIN_HERO_PATH=/branding/login-hero.png ^
VITE_ENABLE_DEMO_MODE=false ^
npm run build
```

## Backend Startup

Start the backend with explicit deploy intent and the published frontend origin:

```bash
APP_ENV=production ^
CORS_ALLOW_ORIGINS=https://cliente.example.com ^
ENABLE_MENTOR_DEMO_ROUTES=false ^
ALLOW_REMOTE_MENTOR_DEMO_ROUTES=false ^
STORAGE_BACKUP_DIR=backups ^
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If a remote environment ever needs mentor-demo routes for an approved internal validation window, the runtime contract is explicit:

```bash
APP_ENV=production ^
CORS_ALLOW_ORIGINS=https://cliente.example.com ^
ENABLE_MENTOR_DEMO_ROUTES=true ^
ALLOW_REMOTE_MENTOR_DEMO_ROUTES=true ^
STORAGE_BACKUP_DIR=backups ^
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Do not use that posture for normal client-facing staging or go-live. The backend now fails fast if `ENABLE_MENTOR_DEMO_ROUTES=true` is set in a production-like environment without the matching approval flag.

## Staging Validation Procedure

### 1. Publish frontend artifact

- Copy the generated frontend build to the target host path.
- Confirm the host serves the app under the configured base path.
- Record the artifact location and timestamp in the release tracker.

### 2. Validate SPA rewrite

- Open the published app on the final origin and base path.
- Directly refresh these URLs in the browser:
  - `/cliente/login`
  - `/cliente/app/admin`
  - `/cliente/app/matriz-renovacao`
  - `/cliente/app/aluno`
- Expected result: each refresh returns the SPA shell instead of a host `404`.
- Evidence: screenshot or deploy log showing successful refreshes.

### 3. Validate base path and static assets

- Open browser devtools on the published app.
- Confirm branding assets load from the published base path instead of `/`.
- Confirm navigation does not drop the configured base path.
- Confirm `document.title` and shell identity show the configured client branding.
- Evidence: screenshot plus network panel capture.

### 4. Validate backend origin and CORS

- Confirm the backend starts with explicit `APP_ENV` and `CORS_ALLOW_ORIGINS`.
- Confirm startup logs record the deploy posture and that `mentor_demo_routes=false` plus `mentor_demo_policy=explicit-disable` or `production-default-disabled`.
- From the published frontend origin, authenticate and observe browser network traffic.
- Confirm no request targets `127.0.0.1` or `localhost`.
- Confirm the browser origin exactly matches the configured `CORS_ALLOW_ORIGINS`.
- Evidence: backend startup log plus browser network capture.

### 5. Validate integrated smoke against the target backend URL

Use the published frontend against the real staging backend URL. Record pass or fail for each step:

1. Open `/cliente/login`.
   Expected: client branding loads and no demo credentials are exposed.
2. Authenticate as admin and open `/cliente/app/admin`.
   Expected: admin shell loads, protected requests succeed, logout returns to login.
3. Confirm the published frontend does not expose the internal mentor workspace unless an explicit local-only validation window was approved.
   Expected: login does not offer the mentor surface and direct access to `/cliente/app/matriz-renovacao` or related mentor routes resolves to controlled denial in the published posture.
4. If aluno is in scope, authenticate and open `/cliente/app/aluno`.
   Expected: student shell loads and student flow is usable.
5. Trigger unauthorized behavior with an expired or invalid token.
   Expected: session is cleared or access is denied according to the current guard policy.
6. Validate one representative `403` path for a non-admin user.
   Expected: access denied UX appears without privileged screen mount.
7. Reload a deep protected route after successful authentication.
   Expected: SPA rewrite plus guarded routing continue to work.

### 6. Record evidence and blockers

- Update `docs/production-release-tracker.md` with the evidence location for each completed step.
- If any step fails, mark the corresponding gate as `blocked` and record the blocker before continuing.

## Smoke Evidence Template

| Step | Result | Evidence | Notes |
| ---- | ------ | -------- | ----- |
| Login branding check | `pending` | `preencher` | `preencher` |
| Admin flow | `pending` | `preencher` | `preencher` |
| Mentor flow | `pending` | `preencher` | `preencher` |
| Aluno flow or waiver | `pending` | `preencher` | `preencher` |
| Unauthorized handling | `pending` | `preencher` | `preencher` |
| `403` handling | `pending` | `preencher` | `preencher` |
| Deep refresh validation | `pending` | `preencher` | `preencher` |
| No localhost traffic | `pending` | `preencher` | `preencher` |

## Backup Reminder

- Export or snapshot the JSON store files before first client usage
- Record where the backup lives and who can restore it
- Run one restore rehearsal before go-live
- Do not publish to client usage if the restore rehearsal has not been executed
- Attach the snapshot directory and verification output to the release tracker
- Treat backup and restore as a maintenance-window activity even in local pilot mode

## Rollback Trigger

Rollback immediately if any of the following occurs:

- login or protected-route flow is broken on the published host
- branding assets fail to load under the target base path
- CORS blocks the published frontend
- persisted JSON data becomes unreadable or inconsistent
- mentor or admin flow fails in the client environment

## Operator Signoff

| Item | Owner | Status | Notes |
| ---- | ----- | ------ | ----- |
| Frontend artifact published | `preencher` | `pending` | `preencher` |
| Backend started with production config | `preencher` | `pending` | `preencher` |
| Staging smoke approved | `preencher` | `pending` | `preencher` |
| Backup and restore confirmed | `preencher` | `pending` | `preencher` |
| Go-live recommendation recorded in tracker | `preencher` | `pending` | `preencher` |
