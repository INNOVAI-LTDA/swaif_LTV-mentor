---
title: 'Frontend Deployment Hardening for Client Delivery'
slug: 'frontend-deployment-hardening-client-delivery'
created: '2026-03-18'
status: 'implemented'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['React 18.3.1', 'React Router DOM 6.30.1', 'TypeScript 5.8.3 strict', 'Vite 5.4.19', 'Vitest 2.1.9', 'FastAPI 0.135.1']
files_to_modify: ['frontend/src/app/providers/AuthProvider.tsx', 'frontend/src/pages/LoginPage.tsx', 'frontend/src/app/routes.tsx', 'frontend/src/shared/config/env.ts', 'frontend/.env.example', 'frontend/src/test/routes.smoke.test.tsx', 'frontend/src/test/login-page.test.tsx', 'frontend/src/test/http-client.test.ts', 'frontend/README.md', 'frontend/src/domain/hooks/useAdminClients.ts', 'frontend/src/domain/hooks/useAdminProducts.ts', 'frontend/src/domain/hooks/useAdminMentors.ts', 'frontend/src/domain/hooks/useAdminPillars.ts', 'frontend/src/domain/hooks/useAdminMetrics.ts', 'frontend/src/domain/hooks/useAdminStudents.ts', 'backend/app/main.py', 'backend/.env.example', 'backend/tests/test_cors_config.py']
code_patterns: ['auth state centralized in AuthProvider', 'router definitions centralized in app/routes.tsx', 'shared env access via shared/config/env.ts', 'admin data loading via useAsyncResource-based hooks', 'unauthorized handling through shared auth events', 'standardized backend auth and error envelope']
test_patterns: ['frontend route smoke tests in frontend/src/test', 'backend auth API tests in backend/tests/api', 'standardized error payload assertions in backend/tests/api/test_error_payload_api.py']
---

# Tech-Spec: Frontend Deployment Hardening for Client Delivery

**Created:** 2026-03-18

## Overview

### Problem Statement

The current frontend still contains demo-oriented authentication and session behavior, root-only routing assumptions, and a silent localhost API fallback. Those behaviors block safe client deployment because protected areas can mount without production-safe guards, deployments under a subpath are unsupported, and missing environment configuration can silently point to a local backend.

### Solution

Harden the existing frontend in brownfield-safe slices that preserve the current React, routing, service, and adapter patterns. The first slices isolate demo login for explicit non-production use, add route and role guards plus configurable router basename support, and enforce explicit API environment configuration for client builds.

### Scope

**In Scope:**
- Auth and session hardening for client-safe frontend behavior
- Archiving `loginPreview` behind explicit non-production or demo-only gating
- Protected route behavior for authenticated and admin-only surfaces
- Configurable router `basename` and subpath-safe navigation
- API environment hardening around `VITE_API_BASE_URL`
- Tests and evidence updates for the first hardening slices
- Brownfield-safe implementation sequencing guided by the deployment readiness checklist

**Out of Scope:**
- Backend authentication redesign
- Full branding/content replacement implementation
- Full deploy documentation rewrite
- Later checklist blocks except when a dependency must be recorded for sequencing

## Context for Development

### Codebase Patterns

- Frontend uses React + TypeScript strict mode with routing centralized in `src/app/routes.tsx`.
- Authentication state is centralized in `src/app/providers/AuthProvider.tsx`.
- API config is centralized in `src/shared/config/env.ts`.
- Frontend infrastructure concerns belong in `src/shared` and `src/app`, not feature pages.
- Existing project context requires preserving adapter/service layering and avoiding scattered environment access.
- Deployment checklist is the source of truth for acceptance direction and slice priority.
- Preview mode is implemented as a first-class branch inside `AuthProvider` and `LoginPage`, with dedicated localStorage state and role presets.
- Route access is currently open at router level; admin data hooks can execute without an auth or role gate because enablement depends on IDs and panel state rather than validated session state.
- Unauthorized API handling already exists through `httpClient` plus `authEvents`, so route and access hardening should build on that instead of inventing a parallel session-expiry flow.
- Backend auth is already sufficient for real-session validation through `/auth/login` and `/me`, and backend CORS currently defaults to localhost development origins when unset.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `docs/mvp-mentoria/frontend-deployment-readiness-checklist.md` | Source of truth for deployment hardening goals, evidence, and recommended priority |
| `_bmad-output/project-context.md` | Current implementation rules and brownfield constraints for future agents |
| `frontend/src/app/providers/AuthProvider.tsx` | Current preview auth/session behavior and login state handling |
| `frontend/src/app/routes.tsx` | Current browser router setup with unguarded routes and no `basename` |
| `frontend/src/pages/LoginPage.tsx` | Current login UX with hardcoded demo credentials, branding assets, and preview-only student path |
| `frontend/src/shared/config/env.ts` | Current API base URL and timeout environment handling, including localhost fallback |
| `frontend/src/shared/api/httpClient.ts` | Existing HTTP client and unauthorized event flow |
| `frontend/src/shared/auth/tokenStorage.ts` | Current access token persistence behavior |
| `frontend/src/shared/auth/authEvents.ts` | Existing unauthorized event channel that can support route/session cleanup |
| `frontend/src/domain/services/authService.ts` | Current login and `/me` orchestration on the frontend |
| `frontend/src/domain/hooks/useAdminClients.ts` | Example admin hook that currently loads regardless of validated auth or role |
| `frontend/src/domain/hooks/useAdminStudents.ts` | Example admin hook with enablement based on mentor context only |
| `frontend/src/features/admin/pages/AdminPage.tsx` | Admin screen anchor that currently assumes auth state and mounts data resources |
| `frontend/src/test/routes.smoke.test.tsx` | Current route coverage that will need hardening-aware updates |
| `frontend/.env.example` | Current example env file still pointing to localhost by default |
| `frontend/README.md` | Current environment and setup documentation baseline |
| `backend/app/api/routes/auth.py` | Existing backend login and `/me` contract for real-session validation |
| `backend/app/main.py` | Backend CORS configuration and current localhost defaults |
| `backend/tests/api/test_auth_api.py` | Existing backend auth flow verification |
| `backend/tests/api/test_error_payload_api.py` | Backend error-envelope expectations already consumed by frontend infrastructure |

### Technical Decisions

- Keep `loginPreview` available only for explicit demo or non-production usage; do not remove it entirely.
- Assume client deployment must support configurable subpath hosting through router `basename`.
- Prefer build-time failure outside local or dev when required API base URL configuration is missing.
- Preserve existing React shells, service boundaries, shared config entrypoints, and current test organization.
- Sequence work by dependency: auth and access control first, routing/base path second, API env hardening third, then downstream checklist slices.
- Treat backend CORS and auth contracts as external dependencies to validate during implementation, but keep this quick spec scoped to frontend changes unless a hard blocker appears.
- Prefer route-level and hook-level protection working together: protected navigation alone is insufficient if admin hooks can still execute before role validation.
- Archive demo behavior through explicit env gating rather than deleting the capability needed for internal demos.

## Implementation Plan

### Tasks

- [x] Task 1: Introduce explicit deployment-mode environment helpers
  - File: `frontend/src/shared/config/env.ts`
  - Action: Replace the silent `http://127.0.0.1:8000` fallback with explicit environment parsing that distinguishes local or dev from client-safe builds, adds support for a router base path variable, and throws a build-time error when required client env values are missing outside local or dev.
  - Notes: Keep all environment access centralized here. Do not let feature code read `import.meta.env` directly.

- [x] Task 2: Archive preview authentication behind explicit non-production gating
  - File: `frontend/src/app/providers/AuthProvider.tsx`
  - Action: Refactor preview-session helpers so `loginPreview`, preview localStorage persistence, and preview session restoration are only enabled when a shared env gate explicitly permits demo mode.
  - Notes: Preserve existing auth state shape where practical so downstream pages and hooks do not need broad rewrites.

- [x] Task 3: Remove client-visible hardcoded demo credentials from the login experience
  - File: `frontend/src/pages/LoginPage.tsx`
  - Action: Rework role presets and copy so demo-only presets are hidden or disabled in client-safe mode, while the archived demo path remains available when the explicit demo env gate is enabled.
  - Notes: The student preview path should not remain a default client path. Preserve the existing page structure and styling patterns unless a small supporting UI state is required.

- [x] Task 4: Add protected-route and role-gate infrastructure
  - File: `frontend/src/app/routes.tsx`
  - Action: Introduce route guard wrappers for authenticated routes and admin-only routes, preventing protected route rendering when session or role checks fail.
  - Notes: Keep route definitions centralized in this file. Guards should integrate with existing `AuthProvider` state rather than duplicating auth logic.

- [x] Task 5: Support configurable router basename for subpath deployment
  - File: `frontend/src/app/routes.tsx`
  - File: `frontend/src/main.tsx`
  - Action: Configure the browser router to consume a shared base path from env and ensure route registration works when the app is deployed below `/`.
  - Notes: Keep the solution compatible with current route tests by exposing route objects for memory-router coverage.

- [x] Task 6: Prevent privileged data hooks from executing before access is validated
  - File: `frontend/src/features/admin/pages/AdminPage.tsx`
  - File: `frontend/src/domain/hooks/useAdminClients.ts`
  - File: `frontend/src/domain/hooks/useAdminProducts.ts`
  - File: `frontend/src/domain/hooks/useAdminMentors.ts`
  - File: `frontend/src/domain/hooks/useAdminPillars.ts`
  - File: `frontend/src/domain/hooks/useAdminMetrics.ts`
  - File: `frontend/src/domain/hooks/useAdminStudents.ts`
  - Action: Thread validated auth and role prerequisites into admin view loading so admin resources do not fetch until the user is authenticated and confirmed as `admin`.
  - Notes: Favor extending the existing `enabled` pattern used by `useAsyncResource` rather than inventing a separate hook framework.

- [x] Task 7: Align unauthorized handling and session cleanup with guarded navigation
  - File: `frontend/src/app/providers/AuthProvider.tsx`
  - File: `frontend/src/shared/api/httpClient.ts`
  - File: `frontend/src/shared/auth/authEvents.ts`
  - Action: Ensure unauthorized API responses clear session state consistently and drive users back toward the correct login or unauthorized fallback path without repeated protected-page mount attempts.
  - Notes: Reuse the existing unauthorized event flow. Avoid adding a second session-expiry mechanism.

- [x] Task 8: Expand test coverage for the first deployment-hardening slices
  - File: `frontend/src/test/routes.smoke.test.tsx`
  - File: `frontend/src/test/*` (new focused auth or env tests if needed)
  - Action: Update route smoke tests and add focused tests for guarded access, admin role denial, preview-mode gating, and env-config behavior.
  - Notes: Keep tests in the current Vitest plus Testing Library style and verify both client-safe mode and explicit demo mode where behavior differs.

- [x] Task 9: Update deployment-facing frontend documentation and env example
  - File: `frontend/.env.example`
  - File: `frontend/README.md`
  - Action: Document required env vars, local or dev vs client-safe behavior, base path configuration, and the explicit demo-mode gate for internal demonstrations.
  - Notes: Documentation should match the implementation exactly and remove the assumption that localhost fallback is acceptable for deployed clients.

### Acceptance Criteria

- [x] AC 1: Given a client-safe build with demo mode disabled, when the login page loads, then no client-visible preview login flow or hardcoded demo credential guidance is shown.
- [x] AC 2: Given demo mode is explicitly enabled in a non-production environment, when the login page loads, then the archived preview path is available only under that explicit gate.
- [x] AC 3: Given a user without a valid session, when they navigate directly to `/app`, `/app/admin`, `/app/centro-comando`, `/app/radar`, `/app/aluno`, or `/app/matriz-renovacao`, then the protected screen does not mount and the user is redirected to the appropriate public access path.
- [x] AC 4: Given an authenticated non-admin user, when they navigate to `/app/admin`, then administrative UI does not render and admin-only data hooks do not execute.
- [x] AC 5: Given an authenticated admin user, when they navigate to `/app/admin`, then the admin surface renders through the guarded route and existing admin flows remain reachable.
- [x] AC 6: Given the app is built for a configured subpath deployment, when users navigate via direct URL refresh to supported routes, then routing resolves correctly under the configured basename.
- [x] AC 7: Given a client-safe build outside local or dev, when `VITE_API_BASE_URL` is missing, then the build fails explicitly instead of silently targeting localhost.
- [x] AC 8: Given a configured client-safe build, when runtime API requests are issued, then request URLs resolve from explicit env configuration and not from an implicit localhost fallback.
- [x] AC 9: Given the backend returns `401` for a protected request, when the frontend receives the response, then session state is cleared predictably and guarded routes no longer continue mounting protected content.
- [x] AC 10: Given the first hardening slices are complete, when `npm run build` and `npm run test` are executed, then the updated route, auth, and env-related coverage passes.
- [x] AC 11: Given the documentation update is complete, when a teammate prepares a deploy configuration, then the required env vars, basename behavior, and demo-mode gate are documented in `frontend/README.md` and `.env.example`.

## Additional Context

### Dependencies

- Frontend deployment readiness checklist
- Existing auth and routing infrastructure
- Shared API configuration and HTTP client behavior
- Backend `/auth/login` and `/me` contract stability
- Backend CORS configuration validation for the final deployed frontend origin, now enforced through `APP_ENV` + `CORS_ALLOW_ORIGINS`
- Vite environment variable injection during build and preview workflows

### Testing Strategy

- Update route smoke coverage so protected routes no longer render privileged screens for anonymous sessions.
- Add or update auth/provider-focused frontend tests for preview gating, logout cleanup, and unauthorized redirect behavior.
- Add coverage for env configuration rules where feasible, especially missing required API base URL outside local/dev.
- Preserve backend auth API tests as contract anchors for `/auth/login`, `/me`, and standardized error handling rather than duplicating backend behavior assumptions in frontend tests.
- Validate direct-route navigation under a configured basename using memory-router or router factory coverage where practical.
- Run manual verification for anonymous, admin, mentor, and student flows after guard changes because role-driven route behavior crosses multiple UI surfaces.

### Notes

- This quick spec is intentionally scoped to brownfield-safe hardening, not a net-new frontend rebuild.
- The first delivery slices must create a safe path for later branding, demo cleanup, and deploy documentation work.
- Highest risk area: breaking internal demo capability while removing unsafe client defaults. Keep the explicit demo-mode gate narrow and documented.
- Second risk area: route guards that block rendering but still allow eager data hooks to fire. Guard both route entry and hook enablement.
- Future slices after this spec should cover branding externalization, broader demo-text cleanup, release-quality evidence capture, and deployment runbook completion.

## Implementation Outcome

- Frontend route guards, demo gating, env hardening, basename support, and admin hook gating were implemented.
- Frontend verification now includes route guard, login-mode, env, and unauthorized HTTP client coverage.
- Backend CORS configuration now fails fast in production-like environments when explicit origins are missing.
- Remaining rollout work is operational: provide real client values for `VITE_API_BASE_URL`, `VITE_APP_BASE_PATH` when needed, `APP_ENV`, and `CORS_ALLOW_ORIGINS` in the deployment environment.
