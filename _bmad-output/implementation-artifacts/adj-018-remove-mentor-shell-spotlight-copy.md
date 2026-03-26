# Story ADJ-018: Remove MentorShell Sidebar Spotlight Copy (ACF)

Status: ready-for-dev

## Exact Scope

Implement the Approved Cleanup Frame (ACF) delta only:

- Remove the Mentor sidebar "Spotlight copy" block ("Leitura da carteira" + supporting copy) from the shared `MentorShell`.
- Keep Main content and Rail behavior exactly as-is (no Matrix/CommandCenter/Radar page layout changes; no `?panel=` rail changes).
- Keep routing and role gating behavior unchanged.

## Affected Blocks / Components

- `frontend/src/features/mentor/components/MentorShell.tsx`
  - Remove the `mentor-sidebar__spotlight` block.
- `frontend/src/features/mentor/mentor-shell.css`
  - Remove or simplify CSS rules that only apply to the removed spotlight block.

## Story

As a mentor,
I want the sidebar to contain only navigational and support elements,
so that the Matrix/Radar/Command Center views feel more operational and less noisy.

## Acceptance Criteria

1. The Mentor sidebar no longer renders the spotlight section labeled "Leitura da carteira" in any mentor view.
2. The rest of `MentorShell` remains unchanged:
   - Brand block, main nav, "Areas de Apoio" links, header/actions behavior, metrics row, and rail behavior (`?panel=...`) remain intact.
3. No role-based behavior changes:
   - `RequireMentorWorkspace` gating and existing routes stay the same.
4. Layout remains stable:
   - No unexpected overlap/regression in sidebar spacing; the main content width and rail behavior are unchanged.
5. Tests are updated/added at the nearest relevant layer to guard the removal.

## Tasks / Subtasks

- [ ] Remove the spotlight copy block from `MentorShell` (AC: 1,2)
- [ ] Remove spotlight-only CSS selectors / spacing rules if they become dead (AC: 4)
- [ ] Add a focused frontend test that asserts the spotlight copy is not rendered (AC: 5)
  - Prefer a small render test in `frontend/src/test/` that renders `MentorShell` and asserts "Leitura da carteira" is absent.

## Dev Notes

- Preserve shared shell/layout patterns (project-context.md):
  - Do not redesign sidebar structure; remove only the spotlight block.
  - Do not change routing (`frontend/src/app/routes.tsx`) or role gating.
- Keep diffs narrow:
  - No refactors in `MentorShell` beyond the minimal removal.
  - No changes to Matrix/Radar/CommandCenter pages for this story.
- Testing guidance (nearest relevant layer):
  - Use existing Testing Library + Vitest setup under `frontend/src/test`.
  - Avoid snapshot churn; assert on the removed label text and keep the test minimal.

### References

- `_bmad-output/project-context.md`
- `frontend/src/features/mentor/components/MentorShell.tsx`
- `frontend/src/features/mentor/mentor-shell.css`

## Out of Scope

- Any MatrixPage content hierarchy changes (filters, board, quick list, details).
- Any changes to the right rail ("Areas de Apoio") content or behavior.
- Any new actions blocks, headers, or UI redesign work.
- Any auth/session/routing changes.

## Regression Risks

- Cross-view impact: `MentorShell` is shared by Matrix/Radar/Command Center; verify all three still look correct after removal.
- Spacing risk: removing a large sidebar block may expose unintended empty space or border/rhythm issues; fix only if clearly broken and keep the patch minimal.

