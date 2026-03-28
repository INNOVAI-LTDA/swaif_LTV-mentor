#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ops.bmad_operator import (
    build_command_prompt,
    create_response_capture_path,
    execute_bmad_command,
    execute_command,
    format_event_summary,
    load_command_contract,
    load_event_log,
    resolve_prompt_profile,
)

MODEL_MAP = {
    "route": {"model": "GPT 5.4 Mini", "reasoning": "Low", "command": "bmad-help"},
    "map": {"model": "GPT 5.2", "reasoning": "Medium", "command": "bmad-document-project"},
    "story": {"model": "GPT 5.2", "reasoning": "Medium", "command": "bmad-create-story"},
    "dev": {"model": "GPT 5.1 Codex Max", "reasoning": "High", "command": "bmad-dev-story"},
    "review": {"model": "GPT 5.4", "reasoning": "High", "command": "bmad-code-review"},
    "fix": {"model": "GPT 5.2", "reasoning": "Medium", "command": "bmad-create-story"},
}
ORDER = ["route", "map", "story", "dev", "review"]


def load_state(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def apply_phase_result(state, batch, phase, result=None):
    batches = state.setdefault("batches", {})
    batch_state = batches.setdefault(batch, {})

    if result is None:
        if phase == "review":
            batch_state[phase] = "approved"
        elif phase == "fix":
            batch_state[phase] = "done"
        else:
            batch_state[phase] = "done"
        return

    batch_state[phase] = result


def phase_allowed(state, batch, phase):
    batches = state.setdefault("batches", {})
    batch_state = batches.setdefault(batch, {})

    if phase == "fix":
        return batch_state.get("review") == "changes_requested"

    idx = ORDER.index(phase)
    if idx == 0:
        return True
    prev = ORDER[idx - 1]
    if phase == "route":
        return True
    return batch_state.get(prev) in ("done", "approved")


def next_locked_reason(state, batch, phase):
    if phase == "fix":
        return "fix is only allowed after review = changes_requested"
    idx = ORDER.index(phase)
    if idx == 0:
        return ""
    prev = ORDER[idx - 1]
    return f"phase '{phase}' is locked until previous phase '{prev}' is done"


def prompt_path(workflow: str, phase: str):
    base = Path("ops/prompts") / workflow
    common = {
        "route": "common_route.md",
        "map": "common_map.md",
        "story": "common_story.md",
        "dev": "common_dev.md",
        "review": "common_review.md",
        "fix": "common_fix.md",
    }
    return base / common[phase]


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


def build_execution_prompt(workflow, batch, phase, command, prompt, context_files, *, contract, prompt_profile):
    command_prompt = build_command_prompt(
        command,
        context_files,
        contract=contract,
        prompt_profile=prompt_profile,
    )
    lines = [
        "You are executing a BMAD phase selected by the local operator.",
        "",
        f"Workflow: {workflow}",
        f"Batch: {batch}",
        f"Phase: {phase}",
        "",
        command_prompt,
        "",
        "Phase-specific instructions:",
        prompt.strip(),
        "",
        "Additional phase execution rules:",
        "- Stay within the current batch boundary.",
        "- Do not advance to another phase unless explicitly required by the phase instructions.",
        "- End by reporting the phase outcome clearly.",
    ]

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow", required=True)
    ap.add_argument("--batch", required=True)
    ap.add_argument("--phase", required=True, choices=["route", "map", "story", "dev", "review", "fix"])
    ap.add_argument("--state", default="ops/state/workflow_state.sample.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--codex-bin", default="codex")
    ap.add_argument("--context-file", action="append", default=[])
    ap.add_argument("--output-last-message")
    ap.add_argument("--prompt-profile", default="auto", choices=["auto", "plain", "contracted"])
    ap.add_argument("--event-log-root", default="_bmad-output/operator-events")
    ap.add_argument("--state-result")
    args = ap.parse_args()

    state_path = Path(args.state)
    if not state_path.exists():
        raise SystemExit(f"Missing state file: {state_path}")
    state = load_state(state_path)

    if not phase_allowed(state, args.batch, args.phase):
        raise SystemExit(next_locked_reason(state, args.batch, args.phase))

    prompt_file = prompt_path(args.workflow, args.phase)
    if not prompt_file.exists():
        raise SystemExit(f"Missing prompt template: {prompt_file}")

    model_info = MODEL_MAP[args.phase]
    prompt = prompt_file.read_text(encoding="utf-8")
    context_files = build_context_files(args.context_file)
    contract = load_command_contract(model_info["command"])
    prompt_profile = resolve_prompt_profile(args.prompt_profile, contract)
    if prompt_profile == "contracted" and contract is None:
        raise SystemExit(f"Prompt profile 'contracted' requires a command contract: {model_info['command']}")
    exec_prompt = build_execution_prompt(
        args.workflow,
        args.batch,
        args.phase,
        model_info["command"],
        prompt,
        context_files,
        contract=contract,
        prompt_profile=prompt_profile,
    )

    print("=== BMAD Phase Runner ===")
    print(f"workflow : {args.workflow}")
    print(f"batch    : {args.batch}")
    print(f"phase    : {args.phase}")
    print(f"command  : {model_info['command']}")
    print(f"model    : {model_info['model']}")
    print(f"reasoning: {model_info['reasoning']}")
    print(f"profile  : {prompt_profile}")
    print(f"contract : {contract.path.as_posix() if contract else 'none'}")
    print(f"prompt   : {prompt_file}")
    print("--- Prompt Preview ---")
    print(prompt.strip())
    print("----------------------")
    if context_files:
        print("--- Context Files ---")
        for context_file in context_files:
            print(context_file.as_posix())
        print("---------------------")

    if args.execute:
        print("execution: local codex exec")

    if args.dry_run:
        print("Dry run only. State unchanged.")
        if args.execute:
            print("--- Execution Prompt Preview ---")
            print(exec_prompt)
            print("--------------------------------")
        return

    if args.execute:
        response_capture_path = (
            Path(args.output_last_message)
            if args.output_last_message
            else create_response_capture_path(model_info["command"])
        )
        result = execute_bmad_command(
            model_info["command"],
            context_files=context_files,
            prompt_text=exec_prompt,
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
        if args.state_result is None:
            print("Codex execution completed. State unchanged; pass --state-result to record the outcome.")
            return

    apply_phase_result(state, args.batch, args.phase, args.state_result)
    state["current_batch"] = args.batch
    state["last_run_at_utc"] = datetime.now(timezone.utc).isoformat()
    save_state(state_path, state)
    print(f"State updated: {state_path}")


if __name__ == "__main__":
    main()
