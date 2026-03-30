# Operator Kit V3 Operator Runbook

## Purpose

Provide a practical runbook for using the V3-style operator model during normal work.

## Standard Start

1. identify the workflow type
2. identify the initial context artifact
3. confirm whether the workflow is high-risk
4. prefer `PROFILE=contracted`
5. prefer `APPROVAL=questionnaire`

## Recommended Defaults

```powershell
PROFILE=contracted
APPROVAL=questionnaire
EXECUTE=1
```

## Daily Usage Pattern

### Documentation work

Use:

```powershell
make bmad-run WORKFLOW=brownfield CONTEXT="docs/discovery/<scope>.md" EXECUTE=1 PROFILE=contracted
```

### Implementation work

Use:

```powershell
make bmad-run WORKFLOW=agile CONTEXT="_bmad-output/implementation-artifacts/<story-file>.md" EXECUTE=1 PROFILE=contracted
```

### Small change

Use:

```powershell
make bmad-run WORKFLOW=quick CONTEXT="docs/discovery/<small-change>.md" EXECUTE=1 PROFILE=contracted
```

## What To Watch In The Terminal

The operator should pay attention to:

- `status`
- `summary`
- `approval_gate`
- `next_command`
- produced artifact paths
- event log path

The operator should not need to inspect raw model reasoning during the normal path.

## Resume Rule

If interrupted:

1. inspect the latest event log
2. inspect the latest produced artifact
3. confirm whether the workflow stopped at approval or failure
4. resume from the saved workflow session

Resume with:

```powershell
make bmad-resume RESUME="<session-id-or-json-path>" EXECUTE=1 PROFILE=contracted
```

## Failure Rule

If a command fails:

1. read the event summary
2. inspect the response capture only if the summary is insufficient
3. correct the input artifact or contract issue
4. rerun the step

## Safety Rule

For data-sensitive or deploy-sensitive work:

- never use unattended continuation
- keep `APPROVAL=questionnaire` or `APPROVAL=stop`
- require explicit operator confirmation before destructive actions
