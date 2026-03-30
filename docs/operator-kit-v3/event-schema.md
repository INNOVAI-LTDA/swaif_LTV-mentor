# Operator Kit V3 Event Schema

## Purpose

Define the canonical event structure used by the operator kit to record command execution.

## Event Role

An event log should answer:

- what ran
- why it ran
- what it consumed
- what it produced
- what happened
- what should happen next
- whether human approval is required

## Canonical Shape

```json
{
  "execution_id": "wf-20260330-001",
  "step_id": "step-003",
  "timestamp_utc": "2026-03-30T18:42:11Z",
  "workflow": "brownfield",
  "command": "bmad-create-story",
  "prompt_profile": "contracted",
  "execution_mode": "execute",
  "status": "completed",
  "summary": "Created the next bounded story for Batch F.",
  "approval_required": true,
  "input_artifacts": [
    {
      "path": "docs/discovery/data-ingestion-admin-brief.md",
      "role": "planning_anchor"
    }
  ],
  "output_artifacts": [
    {
      "artifact_type": "story",
      "path": "_bmad-output/implementation-artifacts/4-7a-batch-g-admin-ingestion-entry.md",
      "title": "4.7a Batch G Admin Ingestion Entry"
    }
  ],
  "decisions": [
    "Split backend apply into a later batch."
  ],
  "risks": [
    "Admin-only boundary must remain enforced."
  ],
  "next_command": "bmad-dev-story",
  "response_capture_path": "_bmad-output/operator-events/messages/20260330T184211123456Z-bmad-create-story.md"
}
```

## Required Fields

- `timestamp_utc`
- `command`
- `prompt_profile`
- `execution_mode`
- `status`
- `summary`
- `approval_required`
- `input_artifacts`
- `output_artifacts`

## Recommended Fields

- `execution_id`
- `step_id`
- `workflow`
- `decisions`
- `risks`
- `next_command`
- `response_capture_path`

## Status Values

Recommended status vocabulary:

- `completed`
- `approved`
- `changes_requested`
- `blocked`
- `failed`
- `needs_input`

These values should be interpreted consistently across workflows.

## Artifact Entry Shape

Each artifact reference should contain:

- `path`
- `role` for inputs
- `artifact_type` for outputs

Optional:

- `title`
- `version`
- `notes`

## Event Rules

- one command execution produces one event
- events should not embed large artifact bodies
- events should reference artifact paths instead
- events should be append-only
- events should support resuming a workflow later

## Display Rule

Operator-facing output should prefer event-summary fields over raw model reasoning.

This means terminal output should emphasize:

- status
- summary
- approval gate
- produced artifacts
- next command
- event path
