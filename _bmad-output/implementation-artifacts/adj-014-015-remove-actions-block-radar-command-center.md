# Story ADJ.014-015: Remove actions block on Radar and Command Center pages

Status: ready-for-dev

## Story

As a mentor user,
I want the Radar and Command Center pages to remove the header actions block,
so that the pages have more vertical space and a cleaner client-facing layout.

## Scope

- In scope:
  - ADJ-014: `frontend/src/features/radar/pages/RadarPage.tsx`
  - ADJ-015: `frontend/src/features/command-center/pages/CommandCenterPage.tsx`
- Out of scope (do not touch):
  - Auth, routing, env, API calls/contracts, shared layout redesign, CSS refactors, other pages (including `StudentPage`)

## Acceptance Criteria

1. Radar page no longer renders the header actions block.
   - The UI no longer shows the "Atualizar leitura" button.
   - The UI no longer shows the "Abrir centro" link.
   - The header (eyebrow/title/description) still renders normally.
2. Command Center page no longer renders the header actions block.
   - The UI no longer shows the "Atualizar leitura" button.
   - The UI no longer shows the "Abrir matriz" link.
   - The header (eyebrow/title/description) still renders normally.
3. No behavior changes outside removing the actions block.
   - No changes to routes (`frontend/src/app/routes.tsx`), auth flows, env access, API/service/adapters, or cross-page layout.
4. TypeScript remains strict-clean and build/test remain green for the touched scope.

## Tasks / Subtasks

- [ ] ADJ-014: Remove RadarPage actions block (AC: #1)
  - [ ] Remove the `actions={...}` prop passed into `MentorShell`.
  - [ ] Remove now-unused imports and code (e.g., `Link` if it becomes unused).
- [ ] ADJ-015: Remove CommandCenterPage actions block (AC: #2)
  - [ ] Remove the `actions={...}` prop passed into `MentorShell`.
  - [ ] Remove now-unused imports and code (e.g., `Link`, `refreshAll()` if it becomes unused).
- [ ] Add minimal guardrail tests (AC: #1, #2, #4)
  - [ ] Add a focused test that renders each page with mocked hooks and asserts the header actions content is absent.
  - [ ] Keep mocking local to the test file; do not change routing/auth/env implementation.

## Dev Notes

### Implementation Notes (smallest safe patch)

- The "actions block" is the `actions?: ReactNode` slot on `MentorShell`.
  - `MentorShell` only renders the actions container when `actions` is truthy:
    - `frontend/src/features/mentor/components/MentorShell.tsx` (`{actions && <div className="mentor-header__actions">...`).
- The already-applied Matrix adjustment (ADJ-013) demonstrates the intended pattern:
  - `frontend/src/features/matrix/pages/MatrixPage.tsx` omits the `actions` prop entirely.
- For both pages in this story, the smallest change is to remove `actions={...}` from the `MentorShell` callsite.
  - Do not replace with new UI, new buttons, or new layout containers in the page body.

### Testing Requirements (nearest relevant layer)

Add one new test file under `frontend/src/test` (Vitest + Testing Library) that:

- Mocks `../shared/config/env` to provide required branding fields used by `MentorShell`.
- Wraps the page render in a router (e.g., `MemoryRouter`) because `MentorShell` uses `NavLink`, `useLocation`, and `useSearchParams`.
- Mocks page hooks so the pages can render deterministically without network:
  - RadarPage:
    - `../domain/hooks/useCommandCenter` -> `useCommandCenterStudents()`
    - `../domain/hooks/useRadar` -> `useStudentRadar()`
  - CommandCenterPage:
    - `../domain/hooks/useCommandCenter` -> `useCommandCenterStudents()`, `useCommandCenterStudentDetail()`, `useCommandCenterTimeline()`
- Assertions:
  - `screen.queryByRole("button", { name: "Atualizar leitura" })` is `null` for both pages.
  - `screen.queryByRole("link", { name: "Abrir centro" })` is `null` on Radar.
  - `screen.queryByRole("link", { name: "Abrir matriz" })` is `null` on Command Center.

Keep the test limited to verifying the removal of the actions UI, not full data rendering.

### Manual Verification

- Navigate to `/app/radar` and `/app/centro-comando` and confirm:
  - Header copy is present.
  - No header action buttons/links appear.
  - No visual regressions outside the removed action row.

### References

- `docs/ui-adjustments-backlog.md` (ADJ-014, ADJ-015)
- `_bmad-output/project-context.md` (strict TS, test location, guardrails)
- `frontend/src/features/mentor/components/MentorShell.tsx` (actions slot conditional rendering)
- `frontend/src/features/matrix/pages/MatrixPage.tsx` (ADJ-013 precedent: omit `actions`)
- `docs/mvp-mentoria/frontend-integration-architecture.md` (layering rules; avoid mixing in API/auth changes)

## Dev Agent Record

### Agent Model Used

GPT-5.2 (Codex CLI)

### Debug Log References

- None

### Completion Notes List

- Story created for a narrow, page-level UI cleanup batch (ADJ-014/015).

### File List

- `frontend/src/features/radar/pages/RadarPage.tsx`
- `frontend/src/features/command-center/pages/CommandCenterPage.tsx`
- `frontend/src/test/<new test file>.test.tsx`

