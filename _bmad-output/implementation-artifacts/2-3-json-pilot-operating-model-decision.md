# Story 2.3: json-pilot-operating-model-decision

Status: done

## Story

As a release owner,
I want the JSON-backed pilot operating model to be explicitly documented and bounded,
so that initial client usage is governed by known constraints instead of implicit assumptions.

## Acceptance Criteria

1. The release tracker records a concrete recommended decision for JSON-backed initial client usage rather than a generic pending placeholder.
2. The pilot operating model defines explicit constraints for hosting, backups, restore posture, concurrency, rollback, and release scope.
3. Operator docs describe when the JSON pilot model is acceptable and when it must be escalated to persistence migration.
4. The story leaves a clear approval checkpoint for the final business owner without hiding the remaining risk.

## Tasks / Subtasks

- [x] Task 1 (AC: 1, 2)
  - [x] Formalize the recommended JSON pilot posture in [production-release-tracker.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/production-release-tracker.md).
  - [x] Replace the generic decision placeholder with concrete constraints and a recommended approval posture.
- [x] Task 2 (AC: 2, 3)
  - [x] Expand [client-launch-runbook.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md) with an explicit JSON pilot operating model section.
  - [x] Document the escalation conditions that require a database migration before broader production usage.
- [x] Task 3 (AC: 4)
  - [x] Keep the business approval visible as a named checkpoint rather than silently auto-approving it.
  - [x] Update sprint/story artifacts so the next local validation story can consume a clear decision outcome.

## Dev Notes

### Why This Story Exists

Epic 2 cannot honestly be considered stable while the persistence posture remains a vague pending decision. The code and operator tooling now support a single-server JSON pilot with backup and restore rehearsal, but the release artifacts still do not state whether that posture is acceptable for initial client usage or under what constraints.

### Decision Framing

This story does not replace the JSON storage model. It formalizes the current recommendation:

- acceptable only for an initial single-server pilot
- only with explicit backup and restore rehearsal evidence
- only with controlled maintenance windows for restore
- not acceptable for multi-instance, high-concurrency, or scale-out usage

### Relevant Files

- [production-release-tracker.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/production-release-tracker.md)
- [client-launch-runbook.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/docs/client-launch-runbook.md)
- [production-readiness-sprint-plan.md](C:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/_bmad-output/implementation-artifacts/production-readiness-sprint-plan.md)

### Implementation Guardrails

- Do not present the JSON pilot as scalable production architecture.
- Do not fabricate staging evidence or business approval.
- Do make the recommended decision concrete enough that the next validation story has stable operating assumptions.

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- Sprint handoff after Story 2.1 completion on 2026-03-20

### Completion Notes List

- Formalized the recommended JSON pilot decision as a constrained operating model rather than leaving it as a generic pending blocker.
- Updated the release tracker so Gate 9 now points to a specific recommendation, explicit constraints, and the remaining owner-approval checkpoint.
- Expanded the client launch runbook with a dedicated JSON pilot operating model section that defines both acceptable usage and escalation triggers.
- Advanced the sprint plan so Epic 2 now treats the JSON pilot decision as an approval gate on a concrete recommendation, not an undefined next step.

### File List

- `docs/production-release-tracker.md`
- `docs/client-launch-runbook.md`
- `_bmad-output/implementation-artifacts/production-readiness-sprint-plan.md`
