# Provider Supabase Preflight

Date: 2026-05-29 12:10:08 -03:00
Task: T01 - Fazer preflight do estado atual

## Scope

- No production code changes.
- No test fixes in this task.
- Only baseline capture of current environment.

## Commands Executed

1. Backend tests

```powershell
python -m pytest
```

Result: failed
Reason:
- `C:\Python313\python.exe: No module named pytest`

2. Frontend tests

```powershell
cmd /c npm test
```

Result: failed
Reason:
- Vitest startup error due to filesystem access and config resolution:
  - `Cannot read directory "../../../../..": Access is denied.`
  - `Could not resolve "...\\frontend\\vite.config.ts"`

3. Frontend build

```powershell
cmd /c npm run build
```

Result: failed
Reason:
- TypeScript strict errors (`TS18047`) in:
  - `src/features/admin/pages/AdminPage.tsx`
- Main message pattern:
  - `'selectedClient' is possibly 'null'`
  - `'selectedProduct' is possibly 'null'`
  - `'selectedMentor' is possibly 'null'`

## Baseline Summary

- Backend test runner dependency missing in current Python environment (`pytest`).
- Frontend test command is blocked at startup by access/config resolution in current environment.
- Frontend build currently fails on strict null checks in `AdminPage.tsx`.

## Known Blockers (Observed in this preflight)

- Missing backend dependency: `pytest`.
- Frontend test execution environment issue (directory access / config resolution).
- Existing frontend TypeScript null-safety issues in admin page.
