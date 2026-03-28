#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ops.bmad_operator import (
    build_command_prompt,
    create_response_capture_path,
    execute_bmad_command,
    format_event_summary,
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow", required=True, choices=sorted(WORKFLOW_COMMANDS))
    ap.add_argument("--context-file", action="append", default=[])
    ap.add_argument("--instruction", default="")
    ap.add_argument("--codex-bin", default="codex")
    ap.add_argument("--prompt-profile", default="auto", choices=["auto", "plain", "contracted"])
    ap.add_argument("--event-log-root", default="_bmad-output/operator-events")
    ap.add_argument("--approval-mode", default="stop", choices=["stop", "continue"])
    ap.add_argument("--max-steps", type=int, default=12)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()

    commands = WORKFLOW_COMMANDS[args.workflow]
    context_files = build_context_files(args.context_file)

    print("=== BMAD Workflow Runner ===")
    print(f"workflow      : {args.workflow}")
    print(f"prompt_profile: {args.prompt_profile}")
    print(f"approval_mode : {args.approval_mode}")
    if context_files:
        print("--- Initial Context ---")
        for path in context_files:
            print(path.as_posix())
        print("-----------------------")

    if args.dry_run:
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

    current_index = 0
    visited_steps = 0
    current_context = context_files

    while current_index is not None and visited_steps < args.max_steps:
        visited_steps += 1
        command_name = commands[current_index]
        contract = load_command_contract(command_name)
        prompt_profile = resolve_prompt_profile(args.prompt_profile, contract)
        if prompt_profile == "contracted" and contract is None:
            raise SystemExit(f"Workflow step requires a contract that does not exist: {command_name}")

        prompt = build_command_prompt(
            command_name,
            current_context,
            args.instruction,
            contract=contract,
            prompt_profile=prompt_profile,
        )
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

        event_payload = load_event_log(result.event_log_path)
        event_payload["event_log_path"] = result.event_log_path.as_posix()
        print("--- Event Summary ---")
        print(format_event_summary(event_payload))
        print("---------------------")

        status = str(event_payload.get("status", "")).strip().lower()
        if status in {"failed", "blocked", "needs_input"}:
            print("workflow_stop  : blocked by command status")
            return

        if event_payload.get("approval_required") and args.approval_mode == "stop":
            print("workflow_stop  : approval gate reached")
            return

        current_context = collect_output_context(event_payload, current_context)
        next_index = choose_next_index(commands, current_index, event_payload)
        if next_index == current_index:
            print("workflow_stop  : next_command would repeat the same step")
            return
        current_index = next_index

    if visited_steps >= args.max_steps:
        raise SystemExit(f"Reached max workflow steps ({args.max_steps}) without termination.")

    print("workflow_done  : completed")


if __name__ == "__main__":
    main()
