#!/usr/bin/env python3
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


def build_context_files(extra_paths):
    context_files = []
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--command", required=True)
    ap.add_argument("--context-file", action="append", default=[])
    ap.add_argument("--instruction", default="")
    ap.add_argument("--codex-bin", default="codex")
    ap.add_argument("--output-last-message")
    ap.add_argument("--prompt-profile", default="auto", choices=["auto", "plain", "contracted"])
    ap.add_argument("--event-log-root", default="_bmad-output/operator-events")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()

    context_files = build_context_files(args.context_file)
    contract = load_command_contract(args.command)
    prompt_profile = resolve_prompt_profile(args.prompt_profile, contract)

    if prompt_profile == "contracted" and contract is None:
        raise SystemExit(f"Prompt profile 'contracted' requires a command contract: {args.command}")

    prompt = build_command_prompt(
        args.command,
        context_files,
        args.instruction,
        contract=contract,
        prompt_profile=prompt_profile,
    )

    print("=== BMAD Command Runner ===")
    print(f"command        : {args.command}")
    print(f"prompt_profile : {prompt_profile}")
    print(f"contract       : {contract.path.as_posix() if contract else 'none'}")
    if context_files:
        print("--- Context Files ---")
        for context_file in context_files:
            print(context_file.as_posix())
        print("---------------------")

    if args.execute:
        print("execution      : local codex exec")

    if args.dry_run:
        print("--- Execution Prompt Preview ---")
        print(prompt)
        print("--------------------------------")
        return

    if not args.execute:
        print("Preview only. Pass --execute to run locally through codex.")
        return

    response_capture_path = (
        Path(args.output_last_message)
        if args.output_last_message
        else create_response_capture_path(args.command)
    )
    result = execute_bmad_command(
        args.command,
        prompt_text=prompt,
        context_files=context_files,
        prompt_profile=prompt_profile,
        contract=contract,
        codex_bin=args.codex_bin,
        event_log_root=Path(args.event_log_root),
        response_capture_path=response_capture_path,
    )

    event_payload = load_event_log(result.event_log_path)
    event_payload["event_log_path"] = result.event_log_path.as_posix()
    print("--- Event Summary ---")
    print(format_event_summary(event_payload))
    print("---------------------")


if __name__ == "__main__":
    main()
