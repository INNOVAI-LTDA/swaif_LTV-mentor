# Sprint Change Proposal

Date: 2026-03-19
Project: swaif_LTV-mentoria
Prepared for: dmene
Workflow: bmad-correct-course
Mode Assumption: Batch
Artifact Scope Note: No repo-local PRD or Epics were found in the configured planning artifacts path, so this proposal is grounded in the available tech spec, project context, deployment checklist, and frontend integration architecture.

## 1. Issue Summary

The frontend deployment-hardening slice was implemented successfully, but post-implementation reviews surfaced several release blockers and weak assumptions that can still break a real client deployment.

The highest-risk findings are:

- Demo mode can still be re-enabled in a production build by environment flag alone.
- Session validation currently treats transient `/me` failures like invalid authentication and clears the user session.
- Post-login navigation trusts the selected UI role instead of the backend-authenticated role.
- Backend CORS production detection is too narrow and can silently fall back to localhost-only origins.
- Frontend and backend deployment documentation are still split enough that operators can configure only one side and ship a broken release.

These issues were discovered after the first hardening slice passed tests and builds. They do not justify re-planning the feature, but they do require a focused correction pass before a real client release.

## 2. Impact Analysis

### Epic Impact

No epic file was found, so no epic text can be updated directly. Practically, this change affects the active deployment-hardening stream only and should be treated as a correction within the same implementation slice, not a new epic.

### Story Impact

No story files were found, so no story text can be updated directly. The safest interpretation is:

- Keep the original hardening scope.
- Add one correction story for auth and deployment safety.
- Execute it before any broader branding or rollout work.

### Artifact Conflicts

Artifacts directly affected by this correction:

- `_bmad-output/implementation-artifacts/tech-spec-frontend-deployment-hardening-client-delivery.md`
- `_bmad-output/project-context.md`
- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- `docs/mvp-mentoria/frontend-integration-architecture.md`

Artifacts indirectly affected:

- Frontend environment and deploy documentation
- Backend deploy environment documentation
- Frontend auth and router tests
- Backend configuration tests

### Technical Impact

- Frontend auth logic in `AuthProvider` needs narrower failure handling.
- Frontend env logic in `env.ts` needs production-safe demo gating.
- Login flow in `LoginPage` needs server-role-aware routing.
- Backend startup configuration in `backend/app/main.py` needs stronger production-like environment detection and CORS normalization.
- Deployment documentation needs cross-reference between frontend and backend required environment settings.

## 3. Recommended Approach

Recommended path: Direct Adjustment

This should be handled as a small brownfield-safe correction, not a rollback and not an MVP scope reset.

Rationale:

- The first hardening slice already established the correct structure.
- The defects are concentrated in configuration and auth edge handling.
- The safest fix is to patch behavior at the existing boundaries rather than reopening the architecture.

Effort estimate:

- Small to moderate
- One focused correction pass
- Mostly frontend, with one backend config update and one documentation alignment pass

Risk assessment:

- Low implementation risk if sliced correctly
- High release risk if left unfixed

Timeline impact:

- Minimal schedule change if executed immediately
- Significant release risk if deferred until deployment

## 4. Detailed Change Proposals

### Change Group A: Lock Demo Mode Out of Client Releases

Purpose:

- Prevent preview login from being enabled in real client deployments by a mis-set environment flag.

Files:

- `frontend/src/shared/config/env.ts`
- `frontend/src/app/providers/AuthProvider.tsx`
- `frontend/README.md`
- `frontend/.env.example`

Proposal:

OLD:

- `demoModeEnabled` is derived directly from `VITE_ENABLE_DEMO_MODE`.

NEW:

- `demoModeEnabled` should only become `true` when both conditions hold:
- the flag is enabled
- the build is explicitly local-like or otherwise marked non-client-safe

Suggested edit direction:

```ts
const demoModeEnabled = isLocalLikeMode() && parseBoolean(import.meta.env.VITE_ENABLE_DEMO_MODE);
```

Rationale:

- This preserves demo capability for internal use while making accidental production exposure much harder.

### Change Group B: Stop Logging Users Out on Transient Session Validation Failures

Purpose:

- Differentiate invalid authentication from network and backend instability.

Files:

- `frontend/src/app/providers/AuthProvider.tsx`
- `frontend/src/shared/api/httpClient.ts`
- `frontend/src/test/http-client.test.ts`
- `frontend/src/test/routes.smoke.test.tsx`

Proposal:

OLD:

- Any `/me` failure during refresh clears user state.

NEW:

- Only `401`-class invalid-session paths should clear auth state.
- Network errors and timeouts should keep the token and surface a retryable error state.

Suggested edit direction:

```ts
catch (err) {
  if (err instanceof AppError && err.isNetworkError) {
    setError(toUserErrorMessage(err, "Falha ao validar sessao."));
    return;
  }
  setAccessToken(null);
  setUser(null);
  setError(toUserErrorMessage(err, "Falha ao validar sessao."));
}
```

Rationale:

- Otherwise a temporary outage looks like a permanent logout.

### Change Group C: Route After Login Using the Authenticated Backend Role

Purpose:

- Prevent misleading post-login redirects when the selected UI profile differs from the role returned by the backend.

Files:

- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/domain/services/authService.ts`
- frontend auth/login tests

Proposal:

OLD:

- Successful login navigates to `ROLE_PRESETS[selectedRole].destination`.

NEW:

- Successful real login should navigate from the authenticated session role returned by the backend, not from the selected card alone.

Suggested edit direction:

```ts
const session = await login(email.trim(), password);
const destination = roleToDestination(session.user?.role ?? selectedRole);
navigate(destination);
```

Rationale:

- This removes a role-assumption bug without changing the existing UI model.

### Change Group D: Make Backend CORS Fail-Fast for More Real Deploy Environments

Purpose:

- Prevent silent localhost fallback in common non-local deployment environments.

Files:

- `backend/app/main.py`
- `backend/.env.example`
- `backend/tests/test_cors_config.py`

Proposal:

OLD:

- Production-like detection only recognizes `production`, `staging`, and `client`.

NEW:

- Treat any environment not explicitly local/development/test as production-like, or expand the allowlist to cover common deployment names and normalize origins.

Suggested edit direction:

```py
def is_production_like_environment() -> bool:
    return os.getenv("APP_ENV", "local").strip().lower() not in {"local", "development", "dev", "test"}

cors_origins = [origin.strip().rstrip("/") for origin in cors_env.split(",") if origin.strip()]
```

Rationale:

- This is safer operationally than trying to enumerate every deployment alias correctly forever.

### Change Group E: Align Frontend and Backend Deployment Documentation

Purpose:

- Reduce the chance of a half-configured release.

Files:

- `frontend/README.md`
- `frontend/.env.example`
- `backend/.env.example`
- optionally `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`

Proposal:

OLD:

- Frontend deploy docs describe frontend envs only.

NEW:

- Frontend deploy docs should explicitly call out the paired backend requirements:
- `APP_ENV`
- `CORS_ALLOW_ORIGINS`
- matching published frontend origin

Suggested edit direction:

```md
Backend pairings required for deployment:
- APP_ENV=production|staging|...
- CORS_ALLOW_ORIGINS=https://published-frontend-origin
```

Rationale:

- The browser will fail even if the frontend itself is configured correctly.

## 5. Smallest Brownfield-Safe Follow-Up Slices

### Slice 1: Demo and Auth Safety

Scope:

- Lock demo mode to local-like environments
- stop logout on transient `/me` failures

Why first:

- These are the highest user-facing release blockers

### Slice 2: Correct Post-Login Role Routing

Scope:

- Navigate from authenticated backend role
- preserve preview routing as-is for explicit demo mode

Why second:

- Small isolated change with low ripple risk

### Slice 3: Backend CORS Detection Hardening

Scope:

- widen production-like detection
- normalize configured origins
- update backend env example and tests

Why third:

- Operationally critical, but isolated to backend startup config

### Slice 4: Deployment Doc Alignment

Scope:

- Cross-reference frontend and backend deployment variables
- mark both as required for published environments

Why last:

- Depends on the final corrected behavior from slices 1 to 3

## 6. Implementation Handoff

Scope classification: Minor to Moderate

Interpretation:

- Minor from a code-change standpoint
- Moderate operationally because it affects release safety and deployment behavior

Recommended handoff:

- Development team implements slices 1 to 4
- Reviewer reruns edge-case and adversarial review after the correction pass

Success criteria:

- Demo login cannot be re-enabled in client-safe releases by env flag alone
- Valid sessions survive transient `/me` failures
- Real login redirects according to authenticated backend role
- Backend startup fails fast for any non-local deployment without explicit CORS origins
- Deployment docs clearly pair frontend and backend environment requirements

## 7. Proposed Next BMAD Commands

Primary next command:

`bmad-bmm-quick-dev-new-preview`

Recommended prompt:

`Implement the course-correction slices for deployment hardening: lock demo mode to local-like builds only, avoid clearing auth on transient /me failures, route post-login by authenticated backend role, strengthen backend APP_ENV/CORS production detection and origin normalization, and align frontend/backend deployment docs. Preserve existing tests and architecture patterns.`

Follow-up review:

`bmad-review-edge-case-hunter`

Prompt:

`Review the deployment hardening correction pass for unhandled auth, routing, env, and CORS edge cases.`

