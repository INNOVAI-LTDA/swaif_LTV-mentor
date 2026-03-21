# Story 1.2: demo-residue-scan-and-client-surface-cleanup

Status: done

## Story

As a release operator,
I want remaining client-facing demo residue removed or isolated behind explicit internal-only behavior,
so that the app no longer looks or behaves like a repackaged demo during local production validation.

## Acceptance Criteria

1. The login UI no longer exposes hardcoded usernames, passwords, or demo email strings in client-facing flows.
2. The internal aluno preview path remains available only when demo mode is enabled, but it does not depend on visible hardcoded credentials.
3. The student experience no longer maps access by fixed demo email addresses.
4. Frontend defaults and fixtures no longer carry the old demo brand or local credential strings where they would pollute the residue scan.
5. Targeted frontend tests pass, and a residue scan over the relevant frontend sources reflects the cleanup.

## Tasks / Subtasks

- [x] Task 1 (AC: 1, 2)
  - [x] Remove hardcoded login preset credentials from [LoginPage.tsx](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/pages/LoginPage.tsx).
  - [x] Keep the internal aluno preview path operational without exposing preset credentials in the UI.
- [x] Task 2 (AC: 2, 3)
  - [x] Update [AuthProvider.tsx](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/app/providers/AuthProvider.tsx) so preview login uses an internal synthetic identity instead of UI-provided demo email strings.
  - [x] Remove fixed demo-email mapping from [StudentPage.tsx](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/student/pages/StudentPage.tsx).
- [x] Task 3 (AC: 4)
  - [x] Neutralize default branding asset names in [env.ts](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/shared/config/env.ts) and [.env.example](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/.env.example).
  - [x] Clean frontend test fixtures that still carry old demo brand or local credential strings where they are not behaviorally required.
- [x] Task 4 (AC: 5)
  - [x] Update the nearest relevant frontend tests.
  - [x] Run the targeted frontend test command and one textual residue scan for the affected frontend sources/tests.

## Dev Notes

### Why This Story Exists

The previous hardening work removed unsafe client defaults, but the repo still contains visible demo residue in the login page, a fixed demo-email mapping in the student page, and old branded/local values in frontend fixtures. Those strings and behaviors now block a clean local production-readiness pass.

### Relevant Files

- [LoginPage.tsx](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/pages/LoginPage.tsx)
- [AuthProvider.tsx](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/app/providers/AuthProvider.tsx)
- [StudentPage.tsx](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/features/student/pages/StudentPage.tsx)
- [AppLayout.tsx](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/app/layout/AppLayout.tsx)
- [env.ts](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/shared/config/env.ts)
- [.env.example](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/.env.example)
- [login-page.test.tsx](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/test/login-page.test.tsx)
- [env.test.ts](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/frontend/src/shared/config/env.test.ts)

### Implementation Guardrails

- Keep demo mode available for internal/local use only.
- Do not re-open the broader auth hardening scope.
- Prefer neutral internal placeholders over demo-branded fixture strings when the exact literal value is not behaviorally important.

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- Sprint handoff after Story 2.3 completion on 2026-03-20
- `npm run test`
- `rg -n -i "admin@swaif\\.local|mentor@swaif\\.local|admin123|mentor123|Acelerador Medico|swaif\\.demo|aceleradormedico\\.demo" frontend/src frontend/.env.example`

### Completion Notes List

- Removed hardcoded login preset credentials from the client-facing login flow and converted the internal aluno preview path into a role-only internal action.
- Switched preview session creation to an internal synthetic identity in `AuthProvider` so the UI no longer carries `.demo` email strings.
- Removed the fixed student lookup by demo email and kept the local pilot student flow on the existing default student record until real server-side linkage exists.
- Neutralized default branding fallback asset names and copied generic branding fallback files into `frontend/public/branding`.
- Cleaned old demo/local credential strings from the nearest frontend tests and admin modal fixture branding.
- Verified the frontend suite passes with 52 tests total and the targeted residue scan over `frontend/src` plus `.env.example` returns no matches for the old brand and credential markers.

### File List

- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/app/providers/AuthProvider.tsx`
- `frontend/src/features/student/pages/StudentPage.tsx`
- `frontend/src/app/layout/AppLayout.tsx`
- `frontend/src/shared/config/env.ts`
- `frontend/.env.example`
- `frontend/public/branding/app-icon.png`
- `frontend/public/branding/app-logo.png`
- `frontend/public/branding/login-hero.png`
- `frontend/src/test/login-page.test.tsx`
- `frontend/src/shared/config/env.test.ts`
- `frontend/src/test/admin-client-modal.test.tsx`
- `frontend/src/test/auth-recovery-flow.test.tsx`
- `frontend/src/test/auth-service.test.ts`
- `frontend/src/test/routes.smoke.test.tsx`
