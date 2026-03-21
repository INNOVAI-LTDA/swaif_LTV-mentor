# Production Readiness Sprint Plan

Date: 2026-03-19
Source: `_bmad-output/implementation-artifacts/tech-spec-production-readiness-rollout-client-launch.md`

## Planning Basis

This sprint plan is derived directly from the production-readiness tech spec because the repo does not yet contain a dedicated epics document for this track.

The goal is to stop looping on broad `quick-dev` requests and move into a stable execution cycle:

1. pick one story
2. implement it
3. review it
4. collect evidence
5. move to the next story

## Current Snapshot

- Branding and client-identity externalization: mostly implemented
- Release checklist, tracker, and runbook: implemented as operator artifacts
- Local production guardrails: implemented; JSON pilot operating model approval still pending
- JSON backup and restore utility: implemented, reviewed clean, and backed by local rehearsal evidence
- Remote staging validation: local parameter baseline now fixed, hosted validation not started
- One local production validation pass is now recorded and attached to the release gate artifacts

## Sprint Epics

### Epic 1: Client-Facing Cleanup and Release Controls

Purpose: finish client-visible hardening and keep release artifacts usable.

| Story | Status | Scope | Blockers | Completion Criteria |
| ----- | ------ | ----- | -------- | ------------------- |
| `1-1-branding-and-shell-identity-hardening` | `done` | Env-driven client name, product name, page identity, shared shell branding | none | Login, shell, and top-level metadata reflect configured client identity |
| `1-2-demo-residue-scan-and-client-surface-cleanup` | `done` | Remove remaining client-visible demo residue and decide what stays local-only | none | Residue scan is clean for client-facing surfaces or each exception is explicitly gated and documented |
| `1-3-release-gate-tracker-and-runbook-activation` | `done` | Checklist, tracker, and runbook converted into execution artifacts | none | Release docs are operator-usable and aligned on status/evidence flow |

### Epic 2: Local Production Safety for JSON Pilot

Purpose: make the current single-server pilot defensible before remote staging.

| Story | Status | Scope | Blockers | Completion Criteria |
| ----- | ------ | ----- | -------- | ------------------- |
| `2-1-runtime-guardrails-and-startup-posture` | `done` | Explicit runtime posture, mentor-demo route toggle, startup observability, multi-root storage handling | none | Startup fails or logs clearly on invalid posture, and remote environments have an explicit mentor-demo policy |
| `2-2-backup-restore-safety-and-rehearsal` | `done` | Close backup/restore edge cases, then run one local rehearsal | none | Backup names are collision-safe, manifest is complete, restore is fail-safe enough for pilot usage, and one local backup+verify+restore rehearsal is recorded |
| `2-3-json-pilot-operating-model-decision` | `done` | Decide whether JSON pilot posture is acceptable for initial client usage | owner approval still pending for remote staging posture, but the recommended operating model is recorded | Release tracker records approved JSON pilot constraints or escalation to persistence migration |

### Epic 3: Local Validation and Evidence Capture

Purpose: prove the current build works locally in client-safe posture before any remote deploy.

| Story | Status | Scope | Blockers | Completion Criteria |
| ----- | ------ | ----- | -------- | ------------------- |
| `3-1-local-production-validation-pass` | `done` | Run local backend with explicit envs and validate frontend against it | none | Local build, login flows, auth expiry, access denial, and local shell serving proof are recorded against the local pilot backend with explicit evidence files |
| `3-2-release-evidence-and-checklist-population` | `done` | Fill checklist and tracker with local evidence and unresolved blockers | none | Release artifacts contain objective evidence, not placeholders, for all local-only gates |

### Epic 4: Remote Staging Readiness

Purpose: transition from local validation to the first real hosted environment.

| Story | Status | Scope | Blockers | Completion Criteria |
| ----- | ------ | ----- | -------- | ------------------- |
| `4-1-staging-environment-parameterization` | `done` | Confirm domain, base path, TLS, frontend origin, backend URL, APP_ENV, and CORS values | none for the current local baseline; remote host details still missing for hosted validation | Current baseline values are copied into the tracker/runbook and the remaining remote-only inputs are explicit |
| `4-2-staging-deploy-and-smoke-validation` | `backlog` | Publish frontend, start backend, validate rewrite/base path/CORS/integrated flows | remote server, domain, TLS, and deploy target still unavailable | Staging smoke passes or every failure is captured as a blocker |
| `4-3-go-no-go-client-pilot-decision` | `backlog` | Decide whether the current release can move from staging to client pilot | staging evidence and JSON pilot posture decision required | Tracker contains an explicit go/no-go decision with approver and open risks |

## Recommended Execution Order

1. `2-1-runtime-guardrails-and-startup-posture`
2. `2-3-json-pilot-operating-model-decision`
3. `1-2-demo-residue-scan-and-client-surface-cleanup`
4. `3-1-local-production-validation-pass`
5. `3-2-release-evidence-and-checklist-population`
6. `4-1-staging-environment-parameterization`
7. `4-2-staging-deploy-and-smoke-validation`
8. `4-3-go-no-go-client-pilot-decision`

## Immediate Next Story

### `4-2-staging-deploy-and-smoke-validation`

Reason:
- the local baseline is fixed and documented, but the first hosted validation has not been executed
- the next step is to publish and test on a real host when those operator inputs are available
- every remaining blocker is now a hosted-validation problem instead of a local-configuration problem

Current waiting state:

- Do not start this story until a real remote server, domain/origin, and deploy path exist.
- If local-only productionization work should continue before remote infra exists, open a sprint change and add a new local-only story slice instead of pretending staging validation happened.

Implementation target:
- publish the frontend on the target host
- start the backend with the chosen remote values
- validate rewrite, base path, CORS, auth, and smoke behavior in the real environment

Done means:
- hosted smoke evidence exists for the real environment
- failures are captured as blockers instead of assumptions
- Story `4-3` can decide go/no-go on real staged behavior

## Stop Conditions

- Do not start remote staging work before Epic 3 is complete.
- Do not claim `client-ready` while `2-3-json-pilot-operating-model-decision` is still unresolved.
- If a story reopens after review, return to that same story instead of starting a new epic.
