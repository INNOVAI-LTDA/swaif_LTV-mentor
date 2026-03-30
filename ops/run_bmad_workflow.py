#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ops.bmad_operator import (
    build_command_prompt,
    create_response_capture_path,
    execute_bmad_command,
    format_event_summary,
    format_workflow_progress,
    load_command_contract,
    load_event_log,
    resolve_prompt_profile,
)


WORKFLOW_COMMANDS = {
    "agile": ["bmad-create-story", "bmad-dev-story", "bmad-code-review"],
    "batching": [
        "bmad-create-epics-and-stories",
        "bmad-sprint-planning",
        "bmad-create-story",
        "bmad-dev-story",
        "bmad-code-review",
    ],
    "greenfield": [
        "bmad-create-product-brief",
        "bmad-create-prd",
        "bmad-create-architecture",
        "bmad-create-epics-and-stories",
        "bmad-check-implementation-readiness",
        "bmad-sprint-planning",
    ],
    "brownfield": [
        "bmad-document-project",
        "bmad-generate-project-context",
        "bmad-create-architecture",
        "bmad-create-epics-and-stories",
        "bmad-check-implementation-readiness",
        "bmad-sprint-planning",
    ],
    "build-from-pieces": [
        "bmad-document-project",
        "bmad-generate-project-context",
        "bmad-create-prd",
        "bmad-create-architecture",
        "bmad-create-epics-and-stories",
        "bmad-check-implementation-readiness",
        "bmad-sprint-planning",
    ],
    "quick": ["bmad-quick-spec", "bmad-quick-dev"],
    "correct-course": ["bmad-correct-course"],
}

DEFAULT_SESSION_ROOT = Path("_bmad-output/operator-workflows")


def build_context_files(extra_paths: list[str]) -> list[Path]:
    context_files: list[Path] = []
    project_context = Path("_bmad-output/project-context.md")
    if project_context.exists():
        context_files.append(project_context)

    for raw_path in extra_paths:
        path = Path(raw_path)
        if not path.exists():
            raise SystemExit(f"Missing context file: {path}")
        if path not in context_files:
            context_files.append(path)

    return context_files


def build_context_files_from_event(event_payload: dict, extra_paths: list[str]) -> list[Path]:
    context_files = build_context_files(extra_paths)
    for artifact in event_payload.get("input_artifacts") or []:
        path_value = artifact.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            continue
        path = Path(path_value)
        if path.exists() and path not in context_files:
            context_files.append(path)
    return context_files


def collect_output_context(event_payload: dict, existing_context: list[Path]) -> list[Path]:
    output_context: list[Path] = []
    for artifact in event_payload.get("output_artifacts") or []:
        path_value = artifact.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            continue
        path = Path(path_value)
        if path.exists() and path not in output_context:
            output_context.append(path)

    if not output_context:
        return existing_context

    merged = list(output_context)
    for path in existing_context:
        if path not in merged:
            merged.append(path)
    return merged


def choose_next_index(commands: list[str], current_index: int, event_payload: dict) -> int | None:
    next_command = event_payload.get("next_command")
    if isinstance(next_command, str) and next_command in commands:
        return commands.index(next_command)

    next_index = current_index + 1
    if next_index >= len(commands):
        return None
    return next_index


def create_session_id(workflow: str, timestamp: datetime | None = None) -> str:
    stamp = (timestamp or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{stamp}-{workflow}"


def build_session_path(session_root: Path, session_id: str) -> Path:
    session_root.mkdir(parents=True, exist_ok=True)
    return session_root / f"{session_id}.json"


def save_workflow_session(session_root: Path, session: dict[str, Any]) -> Path:
    session_path = build_session_path(session_root, session["session_id"])
    session["last_updated_utc"] = datetime.now(timezone.utc).isoformat()
    session_path.write_text(json.dumps(session, indent=2), encoding="utf-8")
    return session_path


def load_workflow_session(session_root: Path, reference: str) -> tuple[Path, dict[str, Any]]:
    direct_path = Path(reference)
    if direct_path.exists():
        session_path = direct_path
    else:
        candidate = build_session_path(session_root, reference)
        if not candidate.exists():
            raise SystemExit(f"Workflow session not found: {reference}")
        session_path = candidate
    try:
        return session_path, json.loads(session_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Workflow session is not valid JSON: {session_path} ({exc})") from None


def session_history_entry(command_name: str, event_log_path: Path, event_payload: dict) -> dict[str, Any]:
    return {
        "command": command_name,
        "event_log_path": event_log_path.as_posix(),
        "status": event_payload.get("status"),
        "approval_required": event_payload.get("approval_required"),
        "next_command": event_payload.get("next_command"),
    }


def approval_decision_from_mode(mode: str, event_payload: dict, session_id: str) -> dict[str, Any] | None:
    if mode == "continue":
        return {"approved": True, "note": "Auto-approved by approval_mode=continue."}
    if mode == "questionnaire":
        if not sys.stdin.isatty():
            print("workflow_stop  : questionnaire mode requires an interactive terminal")
            return None
        return prompt_approval_questionnaire(event_payload, session_id)
    return None


def prompt_approval_questionnaire(event_payload: dict, session_id: str) -> dict[str, Any]:
    print("--- Approval Questionnaire ---")
    print(f"session_id     : {session_id}")
    print(f"summary        : {event_payload.get('summary', '')}")
    print(f"next_command   : {event_payload.get('next_command', '')}")
    response = input("Approve this step and continue? [y/N]: ").strip().lower()
    approved = response in {"y", "yes"}
    note = input("Approval note (optional): ").strip()
    print("------------------------------")
    return {"approved": approved, "note": note}


def apply_approval_decision(
    session: dict[str, Any],
    *,
    event_payload: dict,
    decision: dict[str, Any],
    next_index: int | None,
    next_context: list[Path],
) -> None:
    session["approval_note"] = decision.get("note", "")
    session["approval_updated_utc"] = datetime.now(timezone.utc).isoformat()
    if decision.get("approved"):
        session["status"] = "running"
        session["pending_approval_event"] = None
        session["pending_next_index"] = None
        session["current_index"] = next_index
        session["current_context"] = [path.as_posix() for path in next_context]
    else:
        session["status"] = "pending_approval"
        session["pending_approval_event"] = event_payload.get("event_log_path")
        session["pending_next_index"] = next_index
        session["current_context"] = [path.as_posix() for path in next_context]


def bootstrap_session_from_event(
    *,
    workflow_name: str,
    event_log_path: Path,
    event_payload: dict,
    extra_context_paths: list[str],
    prompt_profile: str,
    approval_mode: str,
) -> dict[str, Any]:
    commands = WORKFLOW_COMMANDS[workflow_name]
    command_name = event_payload.get("command")
    if not isinstance(command_name, str) or command_name not in commands:
        raise SystemExit(
            f"Event command does not belong to workflow '{workflow_name}': {event_log_path.as_posix()}"
        )

    current_index = commands.index(command_name)
    current_context = build_context_files_from_event(event_payload, extra_context_paths)
    next_context = collect_output_context(event_payload, current_context)
    next_index = choose_next_index(commands, current_index, event_payload)
    session_id = create_session_id(workflow_name)
    approval_required = bool(event_payload.get("approval_required"))

    return {
        "session_id": session_id,
        "workflow": workflow_name,
        "status": "pending_approval" if approval_required else "running",
        "approval_mode": approval_mode,
        "prompt_profile": prompt_profile,
        "current_index": current_index if approval_required else next_index,
        "visited_steps": current_index + 1,
        "current_context": [path.as_posix() for path in (next_context if approval_required else next_context)],
        "history": [session_history_entry(command_name, event_log_path, event_payload)],
        "pending_approval_event": event_log_path.as_posix() if approval_required else None,
        "pending_next_index": next_index if approval_required else None,
        "bootstrapped_from_event": event_log_path.as_posix(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow", choices=sorted(WORKFLOW_COMMANDS))
    ap.add_argument("--resume-session")
    ap.add_argument("--resume-event")
    ap.add_argument("--context-file", action="append", default=[])
    ap.add_argument("--instruction", default="")
    ap.add_argument("--codex-bin", default="codex")
    ap.add_argument("--prompt-profile", default="auto", choices=["auto", "plain", "contracted"])
    ap.add_argument("--event-log-root", default="_bmad-output/operator-events")
    ap.add_argument("--session-root", default=str(DEFAULT_SESSION_ROOT))
    ap.add_argument("--approval-mode", default="questionnaire", choices=["questionnaire", "stop", "continue"])
    ap.add_argument("--max-steps", type=int, default=12)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()

    if args.workflow is None and not args.resume_session:
        raise SystemExit(
            "Pass --workflow for a new run or event bootstrap, or --resume-session to continue an existing workflow."
        )
    if args.resume_session and args.resume_event:
        raise SystemExit("Pass only one of --resume-session or --resume-event.")

    session_root = Path(args.session_root)
    resumed = args.resume_session is not None
    bootstrapped = args.resume_event is not None

    if resumed:
        session_path, session = load_workflow_session(session_root, args.resume_session)
        workflow_name = session["workflow"]
        commands = WORKFLOW_COMMANDS[workflow_name]
        session_id = session["session_id"]
        current_index = session.get("current_index")
        visited_steps = session.get("visited_steps", 0)
        current_context = [Path(path) for path in session.get("current_context", [])]
    elif bootstrapped:
        workflow_name = args.workflow
        event_log_path = Path(args.resume_event)
        if not event_log_path.exists():
            raise SystemExit(f"Event log not found: {event_log_path}")
        event_payload = load_event_log(event_log_path)
        session = bootstrap_session_from_event(
            workflow_name=workflow_name,
            event_log_path=event_log_path,
            event_payload=event_payload,
            extra_context_paths=args.context_file,
            prompt_profile=args.prompt_profile,
            approval_mode=args.approval_mode,
        )
        commands = WORKFLOW_COMMANDS[workflow_name]
        session_id = session["session_id"]
        current_index = session.get("current_index")
        visited_steps = session.get("visited_steps", 0)
        current_context = [Path(path) for path in session.get("current_context", [])]
        session_path = build_session_path(session_root, session_id)
    else:
        workflow_name = args.workflow
        commands = WORKFLOW_COMMANDS[workflow_name]
        session_id = create_session_id(workflow_name)
        current_index = 0
        visited_steps = 0
        current_context = build_context_files(args.context_file)
        session = {
            "session_id": session_id,
            "workflow": workflow_name,
            "status": "running",
            "approval_mode": args.approval_mode,
            "prompt_profile": args.prompt_profile,
            "current_index": current_index,
            "visited_steps": visited_steps,
            "current_context": [path.as_posix() for path in current_context],
            "history": [],
            "pending_approval_event": None,
            "pending_next_index": None,
        }
        session_path = build_session_path(session_root, session_id)

    print("=== BMAD Workflow Runner ===")
    print(f"workflow      : {workflow_name}")
    print(f"prompt_profile: {args.prompt_profile}")
    print(f"approval_mode : {args.approval_mode}")
    print(f"session_id    : {session_id}")
    print(f"session_path  : {session_path.as_posix()}")
    if current_context:
        print("--- Initial Context ---")
        for path in current_context:
            print(path.as_posix())
        print("-----------------------")

    if args.dry_run:
        if bootstrapped:
            session_path = save_workflow_session(session_root, session)
            print(f"bootstrapped_from: {args.resume_event}")
        print("--- Workflow Preview ---")
        for command_name in commands:
            contract = load_command_contract(command_name)
            prompt_profile = resolve_prompt_profile(args.prompt_profile, contract)
            print(f"{command_name} [{prompt_profile}]")
        print("------------------------")
        return

    if not args.execute:
        print("Preview only. Pass --execute to run the workflow through codex.")
        return

    if not resumed:
        session_path = save_workflow_session(session_root, session)

    if resumed and session.get("status") == "completed":
        print("workflow_done  : session already completed")
        return

    if resumed and session.get("pending_approval_event"):
        pending_event_path = Path(session["pending_approval_event"])
        pending_event = load_event_log(pending_event_path)
        pending_event["event_log_path"] = pending_event_path.as_posix()
        print("--- Pending Approval ---")
        print(format_event_summary(pending_event))
        print("------------------------")

        pending_next_index = session.get("pending_next_index")
        next_context = collect_output_context(pending_event, current_context)

        if args.approval_mode in {"questionnaire", "continue"}:
            decision = approval_decision_from_mode(args.approval_mode, pending_event, session_id)
            if decision is None:
                return
            apply_approval_decision(
                session,
                event_payload=pending_event,
                decision=decision,
                next_index=pending_next_index,
                next_context=next_context,
            )
            save_workflow_session(session_root, session)
            if not decision["approved"]:
                print("workflow_stop  : approval was not granted")
                return
            current_index = pending_next_index
            current_context = next_context
        else:
            print("workflow_stop  : pending approval must be resumed with APPROVAL=questionnaire or APPROVAL=continue")
            return

    while current_index is not None and visited_steps < args.max_steps:
        print("--- Workflow Progress ---")
        print(format_workflow_progress(commands, current_index, visited_steps))
        print("-------------------------")
        visited_steps += 1
        command_name = commands[current_index]
        contract = load_command_contract(command_name)
        prompt_profile = resolve_prompt_profile(args.prompt_profile, contract)
        if prompt_profile == "contracted" and contract is None:
            raise SystemExit(f"Workflow step requires a contract that does not exist: {command_name}")

        session["current_index"] = current_index
        session["visited_steps"] = visited_steps - 1
        session["current_context"] = [path.as_posix() for path in current_context]
        save_workflow_session(session_root, session)

        prompt = build_command_prompt(
            command_name,
            current_context,
            args.instruction,
            contract=contract,
            prompt_profile=prompt_profile,
        )
        try:
            result = execute_bmad_command(
                command_name,
                prompt_text=prompt,
                context_files=current_context,
                prompt_profile=prompt_profile,
                contract=contract,
                codex_bin=args.codex_bin,
                event_log_root=Path(args.event_log_root),
                response_capture_path=create_response_capture_path(command_name),
            )
        except Exception as exc:
            session["status"] = "failed"
            session["failure_reason"] = str(exc)
            session["current_index"] = current_index
            session["visited_steps"] = visited_steps - 1
            save_workflow_session(session_root, session)
            print("--- Workflow Error ---")
            print(f"failed_step    : {command_name}")
            print(f"reason         : {exc}")
            print("----------------------")
            raise SystemExit(1) from None

        event_payload = load_event_log(result.event_log_path)
        event_payload["event_log_path"] = result.event_log_path.as_posix()
        session.setdefault("history", []).append(session_history_entry(command_name, result.event_log_path, event_payload))
        print("--- Event Summary ---")
        print(format_event_summary(event_payload))
        print("---------------------")
        print("--- Workflow Progress ---")
        print(format_workflow_progress(commands, current_index, visited_steps))
        print("-------------------------")

        status = str(event_payload.get("status", "")).strip().lower()
        if status in {"failed", "blocked", "needs_input"}:
            session["status"] = status or "blocked"
            session["current_index"] = current_index
            session["visited_steps"] = visited_steps
            session["current_context"] = [path.as_posix() for path in current_context]
            save_workflow_session(session_root, session)
            print("workflow_stop  : blocked by command status")
            return

        next_context = collect_output_context(event_payload, current_context)
        next_index = choose_next_index(commands, current_index, event_payload)
        if next_index == current_index:
            session["status"] = "blocked"
            session["failure_reason"] = "next_command would repeat the same step"
            session["current_index"] = current_index
            session["visited_steps"] = visited_steps
            save_workflow_session(session_root, session)
            print("workflow_stop  : next_command would repeat the same step")
            return

        if event_payload.get("approval_required"):
            session["status"] = "pending_approval"
            session["pending_approval_event"] = result.event_log_path.as_posix()
            session["pending_next_index"] = next_index
            session["current_index"] = current_index
            session["visited_steps"] = visited_steps
            session["current_context"] = [path.as_posix() for path in next_context]
            save_workflow_session(session_root, session)

            if args.approval_mode == "continue":
                current_context = next_context
                current_index = next_index
                session["status"] = "running"
                session["pending_approval_event"] = None
                session["pending_next_index"] = None
                save_workflow_session(session_root, session)
                continue

            if args.approval_mode == "questionnaire":
                decision = approval_decision_from_mode(args.approval_mode, event_payload, session_id)
                if decision is None:
                    return
                apply_approval_decision(
                    session,
                    event_payload=event_payload,
                    decision=decision,
                    next_index=next_index,
                    next_context=next_context,
                )
                save_workflow_session(session_root, session)
                if not decision["approved"]:
                    print("workflow_stop  : approval was not granted")
                    return
                current_context = next_context
                current_index = next_index
                continue

            print("workflow_stop  : approval gate reached")
            return

        current_context = next_context
        current_index = next_index
        session["status"] = "running"
        session["pending_approval_event"] = None
        session["pending_next_index"] = None
        session["current_index"] = current_index
        session["visited_steps"] = visited_steps
        session["current_context"] = [path.as_posix() for path in current_context]
        save_workflow_session(session_root, session)

    if visited_steps >= args.max_steps:
        session["status"] = "blocked"
        session["failure_reason"] = f"Reached max workflow steps ({args.max_steps}) without termination."
        save_workflow_session(session_root, session)
        raise SystemExit(f"Reached max workflow steps ({args.max_steps}) without termination.")

    session["status"] = "completed"
    session["current_index"] = None
    session["visited_steps"] = visited_steps
    save_workflow_session(session_root, session)
    print("workflow_done  : completed")


if __name__ == "__main__":
    main()
