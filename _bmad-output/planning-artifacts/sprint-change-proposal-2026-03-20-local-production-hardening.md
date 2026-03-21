# Sprint Change Proposal: Local-Only Production Hardening

Date: 2026-03-20

## Trigger

Story `4.1-staging-environment-parameterization` is complete for the current local baseline, but remote staging cannot begin because no real remote server, origin, TLS, or deploy target exists yet.

Continuing directly to Story `4.2` would create fake staging progress. At the same time, there is still meaningful local-only work that improves production readiness before migration.

## Recommendation

Recommended path: `Direct Adjustment`

Scope: `Moderate`

Decision:

- keep `4.2-staging-deploy-and-smoke-validation` paused until remote infrastructure exists
- insert a local-only hardening lane before any hosted validation resumes
- use that lane to finish the parts of production readiness that do not require a real server

## Why This Change Is Safe

- It does not reopen already-completed auth, env, backup, or evidence stories.
- It respects the current truth: hosted validation cannot happen locally.
- It keeps momentum on real release risks that are still local-code or local-ops concerns.
- It prevents the team from overclaiming staging readiness.

## Proposed Local-Only Follow-Up Slices

### Slice A: Mentor-Demo Dependency Isolation

Goal:

- remove or isolate the remaining dependency on `mentor-demo` backend routes from the production path

Scope:

- decide which mentor flows remain acceptable for local-only/demo use
- gate or remove remote-facing mentor-demo exposure
- update tracker and checklist so the behavior is no longer an ambiguous blocker

Done means:

- the production path no longer depends on an implicitly demo-oriented mentor route family
- any remaining demo-only route is explicitly local/internal and documented as such

### Slice B: Final Local Product Identity Cleanup

Goal:

- make the local app feel like a product candidate, not a repackaged demo

Scope:

- finish any remaining copy cleanup on login, mentor, aluno, and admin surfaces
- tighten current local branding around `Acelerador Médico (AccMed)` and `Gamma`
- remove residual “demo” tone where it is still user-facing

Done means:

- the local browser-facing app reads consistently as the target product
- remaining demo terminology is either gone or clearly internal-only

### Slice C: Deployment Packaging and Startup Artifacts

Goal:

- prepare the repo for clean migration to a remote host

Scope:

- add operator-facing startup wrappers or scripts for frontend and backend
- define env-file conventions for local vs remote
- add packaging notes for artifact folder layout, backup location, and rollback prerequisites
- optionally add host-bootstrap examples if the target OS/process manager is known

Done means:

- a teammate can package and start the app from the repo without tacit knowledge
- the migration to a server is operationally cleaner when the host exists

### Slice D: Local Browser Smoke Validation

Goal:

- close the biggest remaining local proof gap before remote migration

Scope:

- run a real browser-level manual smoke pass locally under `/accmed/`
- validate login shell, branding, protected navigation, access denial, and one representative mentor/admin path
- record screenshots or evidence references in the tracker/checklist

Done means:

- the local release evidence is no longer limited to build/test/API/shell-level proof
- the next hosted story starts from stronger local confidence

## Recommended Order

1. Slice A: Mentor-Demo Dependency Isolation
2. Slice B: Final Local Product Identity Cleanup
3. Slice C: Deployment Packaging and Startup Artifacts
4. Slice D: Local Browser Smoke Validation
5. Resume `4.2` only when remote infrastructure exists

## Impact on Current Sprint

- `4.1` remains `done`
- `4.2` stays `backlog` and should be treated as infra-blocked
- the sprint should temporarily branch into the local-only hardening slices above

## Recommended Next Command

`bmad-bmm-quick-dev-new-preview`

Prompt:

`Implement the first local-only production-hardening slice before remote staging resumes. Start with isolating or removing the remaining mentor-demo dependency from the production path, keeping any internal-only demo behavior explicitly gated to local/non-production use, and update the release tracker/checklist accordingly. Preserve the existing architecture, env-contract patterns, and current local validation evidence.`
