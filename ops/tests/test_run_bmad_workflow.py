from __future__ import annotations

from pathlib import Path

from ops.run_bmad_workflow import (
    apply_approval_decision,
    approval_decision_from_mode,
    bootstrap_session_from_event,
    load_workflow_session,
    save_workflow_session,
)


def test_save_and_load_workflow_session_round_trips(tmp_path: Path):
    session = {
        "session_id": "20260330T120000000000Z-brownfield",
        "workflow": "brownfield",
        "status": "running",
        "current_index": 2,
        "visited_steps": 2,
        "current_context": ["docs/discovery/data-ingestion-admin-brief.md"],
        "history": [],
        "pending_approval_event": None,
        "pending_next_index": None,
    }

    written_path = save_workflow_session(tmp_path, session)
    loaded_path, loaded_session = load_workflow_session(tmp_path, session["session_id"])

    assert written_path == loaded_path
    assert loaded_session["session_id"] == session["session_id"]
    assert loaded_session["workflow"] == "brownfield"
    assert loaded_session["current_index"] == 2
    assert "last_updated_utc" in loaded_session


def test_approval_decision_from_continue_auto_approves():
    decision = approval_decision_from_mode(
        "continue",
        {"summary": "Architecture reviewed.", "next_command": "bmad-create-epics-and-stories"},
        "wf-001",
    )

    assert decision == {
        "approved": True,
        "note": "Auto-approved by approval_mode=continue.",
    }


def test_apply_approval_decision_moves_session_forward_when_approved():
    session = {
        "status": "pending_approval",
        "pending_approval_event": "_bmad-output/operator-events/sample.json",
        "pending_next_index": 3,
        "current_index": 2,
        "current_context": ["docs/discovery/data-ingestion-admin-brief.md"],
    }

    apply_approval_decision(
        session,
        event_payload={"event_log_path": "_bmad-output/operator-events/sample.json"},
        decision={"approved": True, "note": "Looks good."},
        next_index=3,
        next_context=[Path("_bmad-output/planning-artifacts/batch-g-data-ingestion-admin-architecture.md")],
    )

    assert session["status"] == "running"
    assert session["pending_approval_event"] is None
    assert session["pending_next_index"] is None
    assert session["current_index"] == 3
    assert session["current_context"] == [
        "_bmad-output/planning-artifacts/batch-g-data-ingestion-admin-architecture.md"
    ]
    assert session["approval_note"] == "Looks good."
    assert "approval_updated_utc" in session


def test_apply_approval_decision_keeps_session_pending_when_rejected():
    session = {
        "status": "pending_approval",
        "pending_approval_event": "_bmad-output/operator-events/sample.json",
        "pending_next_index": 3,
        "current_index": 2,
        "current_context": ["docs/discovery/data-ingestion-admin-brief.md"],
    }

    apply_approval_decision(
        session,
        event_payload={"event_log_path": "_bmad-output/operator-events/sample.json"},
        decision={"approved": False, "note": "Need to read the architecture first."},
        next_index=3,
        next_context=[Path("_bmad-output/planning-artifacts/batch-g-data-ingestion-admin-architecture.md")],
    )

    assert session["status"] == "pending_approval"
    assert session["pending_approval_event"] == "_bmad-output/operator-events/sample.json"
    assert session["pending_next_index"] == 3
    assert session["current_context"] == [
        "_bmad-output/planning-artifacts/batch-g-data-ingestion-admin-architecture.md"
    ]
    assert session["approval_note"] == "Need to read the architecture first."


def test_bootstrap_session_from_event_creates_pending_approval_session(tmp_path: Path):
    project_context = tmp_path / "_bmad-output" / "project-context.md"
    project_context.parent.mkdir(parents=True)
    project_context.write_text("context", encoding="utf-8")

    architecture = tmp_path / "_bmad-output" / "planning-artifacts" / "batch-g-architecture.md"
    architecture.parent.mkdir(parents=True)
    architecture.write_text("# Architecture", encoding="utf-8")

    brief = tmp_path / "docs" / "discovery" / "data-ingestion-admin-brief.md"
    brief.parent.mkdir(parents=True)
    brief.write_text("# Brief", encoding="utf-8")

    session = bootstrap_session_from_event(
        workflow_name="brownfield",
        event_log_path=tmp_path / "_bmad-output" / "operator-events" / "architecture.json",
        event_payload={
            "command": "bmad-create-architecture",
            "approval_required": True,
            "next_command": "bmad-create-epics-and-stories",
            "input_artifacts": [
                {"path": project_context.as_posix()},
                {"path": brief.as_posix()},
            ],
            "output_artifacts": [
                {"path": architecture.as_posix()},
            ],
        },
        extra_context_paths=[],
        prompt_profile="contracted",
        approval_mode="questionnaire",
    )

    assert session["workflow"] == "brownfield"
    assert session["status"] == "pending_approval"
    assert session["pending_approval_event"].endswith("architecture.json")
    assert session["pending_next_index"] == 3
    assert session["current_index"] == 2
    assert architecture.as_posix() in session["current_context"]
