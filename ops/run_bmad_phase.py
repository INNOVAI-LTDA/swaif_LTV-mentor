#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow", required=True)
    ap.add_argument("--batch", required=True)
    ap.add_argument("--phase", required=True, choices=["route", "map", "story", "dev", "review", "fix"])
    ap.add_argument("--state", default="ops/state/workflow_state.sample.json")
    ap.add_argument("--dry-run", action="store_true")
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

    print("=== BMAD Phase Runner ===")
    print(f"workflow : {args.workflow}")
    print(f"batch    : {args.batch}")
    print(f"phase    : {args.phase}")
    print(f"command  : {model_info['command']}")
    print(f"model    : {model_info['model']}")
    print(f"reasoning: {model_info['reasoning']}")
    print(f"prompt   : {prompt_file}")
    print("--- Prompt Preview ---")
    print(prompt.strip())
    print("----------------------")

    if args.dry_run:
        print("Dry run only. State unchanged.")
        return

    batches = state.setdefault("batches", {})
    batch_state = batches.setdefault(args.batch, {})
    if args.phase == "review":
        batch_state[args.phase] = "approved"
    elif args.phase == "fix":
        batch_state[args.phase] = "done"
        batch_state["review"] = "approved"
    else:
        batch_state[args.phase] = "done"

    state["current_batch"] = args.batch
    state["last_run_at_utc"] = datetime.now(timezone.utc).isoformat()
    save_state(state_path, state)
    print(f"State updated: {state_path}")


if __name__ == "__main__":
    main()
