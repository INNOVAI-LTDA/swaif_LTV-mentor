# Sprint Change Proposal

Date: 2026-03-19
Project: swaif_LTV-mentoria
Prepared for: dmene
Workflow: bmad-correct-course
Mode Assumption: Batch
Artifact Scope Note: No repo-local PRD or Epics were found in the configured planning artifacts path, so this proposal is grounded in the available tech spec, project context, deployment checklist, and the latest review findings.

## 1. Issue Summary

The first correction pass improved deployment hardening, but the follow-up edge-case and adversarial reviews still found release blockers and weak operational assumptions.

The most important unresolved decision is the behavior when a stale token exists but `/me` cannot be validated because the backend is unavailable. The current code accidentally allows some protected UI to mount based on token presence alone, even when `user` is still null. That is not an intentional product behavior and creates inconsistent access control.

### Decision

For this release, the frontend should **block all protected UI until `/me` has been validated successfully**.

Rationale:

- It is the safest brownfield option.
- It matches the deployment-hardening goal of predictable protected-route behavior.
- It avoids implicitly inventing a degraded read-only mode that has no PRD, UX, or architecture support.
- It reduces ambiguity in auth, routing, and admin-hook behavior.

## 2. Impact Analysis

### Epic Impact

No epic artifact was found. Practically, this remains part of the existing deployment-hardening stream and should be treated as a second correction pass within the same scope.

### Story Impact

No story artifact was found. The safest implementation interpretation is:

- keep the deployment-hardening scope intact,
- add one focused follow-up correction story,
- execute it before release prep or broader cleanup.

### Artifact Conflicts

Artifacts directly affected:

- `_bmad-output/implementation-artifacts/tech-spec-frontend-deployment-hardening-client-delivery.md`
- `_bmad-output/project-context.md`
- `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`
- `frontend/README.md`
- `backend/.env.example`

Artifacts indirectly affected:

- frontend auth tests,
- frontend route tests,
- frontend env validation tests,
- backend CORS config tests.

### Technical Impact

- `AuthProvider` and route guards need to require validated identity, not token presence alone.
- frontend env/build logic needs a stronger client-safe boundary than Vite mode naming by itself.
- login bootstrap needs to tolerate transient `/me` failure without falsely burning the session or falsely succeeding.
- backend startup must fail fast when production deploy inputs are incomplete or malformed.
- deployment docs must describe the exact safe build path, not just the variables.

## 3. Recommended Approach

Recommended path: Direct Adjustment

This is still a brownfield-safe correction, not a rollback and not a broader replan.

### Why this path

- The architecture and hardening direction are still correct.
- The remaining defects are concentrated in auth gating, configuration validation, and deploy contracts.
- The safest fix is to narrow behavior at existing boundaries rather than reopening the feature scope.

### Effort estimate

- Small to moderate
- One focused implementation pass
- One follow-up review pass

### Risk assessment

- Moderate implementation risk
- High release risk if left unresolved

### Timeline impact

- Small delay if handled immediately
- High probability of release churn if deferred to deployment time

## 4. Detailed Change Proposals

### Change Group A: Treat Unvalidated Sessions as Unauthenticated

Purpose:

- Prevent protected surfaces from mounting while the backend identity is still unknown.

Files:

- `frontend/src/app/providers/AuthProvider.tsx`
- `frontend/src/app/routes.tsx`
- frontend auth and route tests

Proposal:

OLD:

- `isAuthenticated` becomes true when `authReady` is true and a token exists, even if `user` is null after `/me` failure.

NEW:

- Protected UI should require a validated user object for real sessions.
- If `/me` cannot be validated, route guards should block protected surfaces.
- Preserve preview-session behavior explicitly, because preview users do have a synthetic user object.

Suggested edit direction:

```ts
const hasValidatedSession = Boolean(accessToken && user);
isAuthenticated = authReady && (isPreviewSession || hasValidatedSession);
```

Rationale:

- This turns the stale-token policy into an explicit rule and closes the current protected-route leak.

### Change Group B: Split Login Bootstrap Failure from Session Revocation

Purpose:

- Avoid clearing a newly issued token on transient `/me` failure during login while still avoiding a false authenticated success.

Files:

- `frontend/src/domain/services/authService.ts`
- `frontend/src/app/providers/AuthProvider.tsx`
- frontend login/auth tests

Proposal:

OLD:

- Any `/me` failure after `/auth/login` clears the token and collapses into a normal login failure.

NEW:

- Distinguish invalid-token failures from transient bootstrap failures.
- On transient `/me` failure during login, surface a retryable error and do not claim a valid authenticated session.
- Decide in one place whether the token should be retained for an immediate retry or cleared deliberately; do not let the current accidental behavior stand.

Suggested edit direction:

```ts
if (error instanceof AppError && error.isNetworkError) {
  throw new AppError({ ...error, code: "AUTH_BOOTSTRAP_RETRYABLE" });
}
```

Rationale:

- Login bootstrap and logout semantics should not be conflated.

### Change Group C: Replace Mode-Based Security Assumptions with Explicit Client-Safe Rules

Purpose:

- Make it harder to produce an unsafe client build by choosing the wrong Vite mode.

Files:

- `frontend/src/shared/config/env.ts`
- `frontend/vite.config.ts`
- `frontend/.env.example`
- `frontend/README.md`
- frontend env tests

Proposal:

OLD:

- Demo-mode gating and localhost fallback rely mainly on Vite `mode` naming.

NEW:

- Introduce an explicit deployment-safety signal such as `VITE_DEPLOY_TARGET=local|client`.
- Reserve localhost fallback and demo mode for `local`.
- Fail build for client targets when required variables are absent or malformed.

Suggested edit direction:

```ts
const deployTarget = (import.meta.env.VITE_DEPLOY_TARGET || "local").trim().toLowerCase();
const isLocalLike = deployTarget === "local";
```

Rationale:

- Build mode is a tooling concern, not a reliable security boundary.

### Change Group D: Validate Deploy Inputs, Not Just Their Presence

Purpose:

- Fail fast on malformed but non-empty deploy configuration.

Files:

- `frontend/src/shared/config/env.ts`
- `backend/app/main.py`
- frontend env tests
- backend CORS tests

Proposal:

OLD:

- `VITE_API_BASE_URL` is only trimmed.
- `CORS_ALLOW_ORIGINS` strips trailing slashes but accepts path-bearing values.

NEW:

- Frontend should validate that `VITE_API_BASE_URL` is an absolute URL.
- Backend should reject CORS origin values that include paths, query strings, or fragments.

Suggested edit direction:

```ts
new URL(candidate);
if (!/^https?:$/.test(parsed.protocol)) throw new Error(...);
```

```py
parsed = urlparse(origin)
if parsed.path not in ("", "/") or parsed.params or parsed.query or parsed.fragment:
    raise RuntimeError("CORS origin must be a bare origin")
```

Rationale:

- Presence-only validation still allows common operator mistakes to ship.

### Change Group E: Fail Fast on Missing Backend Deploy Intent

Purpose:

- Stop production deploys from silently booting with localhost-only CORS because `APP_ENV` was forgotten.

Files:

- `backend/app/main.py`
- `backend/.env.example`
- `frontend/README.md`
- backend tests

Proposal:

OLD:

- Missing `APP_ENV` defaults to `local`.

NEW:

- Require `APP_ENV` explicitly outside local development workflows, or introduce a separate `BACKEND_DEPLOY_TARGET` signal.
- Production deployment instructions must treat missing backend deploy intent as a configuration error.

Suggested edit direction:

```py
app_env = os.getenv("APP_ENV")
if app_env is None:
    raise RuntimeError("APP_ENV is required")
```

Rationale:

- A missing deploy-intent variable is itself a deploy error.

### Change Group F: Remove Weak Fallbacks in Role Routing

Purpose:

- Prevent silent misrouting when role contracts drift.

Files:

- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/app/routes.tsx`
- frontend login and route tests

Proposal:

OLD:

- Unknown backend roles fall back to the selected UI role.
- Non-admin users always fall back from `/app/admin` to `/app`.

NEW:

- Unknown backend roles should fail closed and surface an explicit error.
- Route fallbacks should be role-aware or send the user to a neutral safe page such as `/login` or a dedicated unauthorized screen.

Suggested edit direction:

```ts
if (!isKnownRole(user.role)) {
  setError("Perfil nao reconhecido.");
  return;
}
```

Rationale:

- Silent fallback hides contract errors and produces inconsistent protected-route behavior.

### Change Group G: Clean Up Stale Preview State

Purpose:

- Prevent old preview sessions from resurfacing when demo mode is later re-enabled locally.

Files:

- `frontend/src/app/providers/AuthProvider.tsx`
- frontend auth tests

Proposal:

OLD:

- Preview storage is ignored when demo mode is off but remains persisted.

NEW:

- When demo mode is off, proactively purge preview-session storage during auth initialization.

Suggested edit direction:

```ts
if (!env.demoModeEnabled) {
  clearPreviewSession();
  return null;
}
```

Rationale:

- Archived demo state should not outlive the demo context.

### Change Group H: Tighten Deployment Documentation

Purpose:

- Make the safe build and deploy path explicit for operators.

Files:

- `frontend/README.md`
- `frontend/.env.example`
- `backend/.env.example`
- optionally `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md`

Proposal:

OLD:

- Docs describe variables, but not the exact safe build contract.

NEW:

- Add explicit examples for:
  - local build/dev flow,
  - client-safe build flow,
  - backend deploy pairing,
  - invalid configuration examples that must fail.

Suggested edit direction:

```md
Client-safe build example:
VITE_DEPLOY_TARGET=client
VITE_API_BASE_URL=https://api.example.com
npm run build
```

Rationale:

- Operators need an executable deploy recipe, not only variable names.

## 5. Smallest Brownfield-Safe Follow-Up Slices

### Slice 1: Auth Gating Safety

Scope:

- require validated user for protected real sessions
- block protected UI when `/me` is unvalidated
- add auth/route regression tests

Why first:

- This closes the highest-severity access-control issue.

### Slice 2: Login Bootstrap and Role Fallback Fixes

Scope:

- separate retryable login bootstrap failure from invalid auth
- fail closed on unknown roles
- make admin fallback behavior explicit

Why second:

- Small, isolated changes with direct user-facing impact.

### Slice 3: Explicit Deploy Target and Input Validation

Scope:

- replace mode-based security assumptions
- validate absolute API URLs
- strengthen frontend env tests

Why third:

- This removes the main deploy-footgun without broad UI changes.

### Slice 4: Backend Deploy Intent and CORS Validation

Scope:

- fail fast on missing backend deploy intent
- reject malformed CORS origin values
- update backend examples and tests

Why fourth:

- Operationally critical, but isolated to startup/config behavior.

### Slice 5: Preview-State Cleanup and Deploy Docs

Scope:

- purge stale preview state when demo mode is off
- document exact local vs client-safe build/deploy steps

Why last:

- Low code risk, depends on the final env contract from slices 3 and 4.

## 6. Implementation Handoff

Scope classification: Moderate

Interpretation:

- Minor-to-moderate code change size
- Moderate delivery impact because deploy semantics and auth behavior become stricter

Recommended handoff:

- Development implements slices 1 to 5
- Review reruns edge-case and adversarial checks after the pass

Success criteria:

- Protected routes never mount from token presence alone
- Transient `/me` failures do not masquerade as either success or logout
- Client-safe builds cannot be made unsafe by selecting the wrong Vite mode
- Backend startup fails fast on missing or malformed production deploy inputs
- Unknown roles and weak redirect fallbacks fail closed
- Docs define one explicit safe deploy path

## 7. Proposed Next BMAD Commands

Primary next command:

`bmad-bmm-quick-dev-new-preview`

Recommended prompt:

`Implement the second course-correction slices for deployment hardening: require validated user state before protected real-session routes mount, separate retryable /me bootstrap failures from invalid auth, replace mode-based security assumptions with an explicit local-vs-client deploy target, validate absolute API base URLs and bare CORS origins, fail fast when backend deploy intent is missing, fail closed on unknown roles and weak non-admin fallbacks, purge stale preview-session storage when demo mode is off, and update deployment docs/examples to show the exact safe local and client-safe build paths. Preserve existing architecture patterns and expand tests at the nearest relevant layer.`

Follow-up review:

`bmad-review-edge-case-hunter`

Prompt:

`Review the second deployment-hardening correction pass for any remaining auth, env, routing, preview-state, or CORS edge cases.`
