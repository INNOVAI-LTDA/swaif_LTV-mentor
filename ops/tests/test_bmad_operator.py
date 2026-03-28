from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from ops.bmad_operator import (
    build_command_prompt,
    collect_artifact_statuses,
    collect_planning_artifacts,
    create_response_capture_path,
    execute_command,
    extract_structured_response,
    format_event_summary,
    infer_next_command,
    load_command_contract,
    materialize_output_artifacts,
    summarize_artifact_statuses,
    validate_command_response,
    write_event_log,
)


def write_story(path: Path, title: str, status: str):
    path.write_text(
        "\n".join(
            [
                f"# Story {title}",
                "",
                f"Status: {status}",
                "",
                "## Story",
                "",
                "Example story body.",
            ]
        ),
        encoding="utf-8",
    )


def make_contract(tmp_path: Path, command_name: str = "bmad-create-story") -> Path:
    contracts_root = tmp_path / "contracts"
    contracts_root.mkdir()
    contract_path = contracts_root / f"{command_name}.json"
    contract_path.write_text(
        json.dumps(
            {
                "command": command_name,
                "prompt_profile": "contracted",
                "required_inputs": [{"role": "planning_anchor", "description": "Story source doc."}],
                "output_artifact_types": ["story"],
                "materialized_artifact_types": ["story"],
                "required_response_fields": [
                    "status",
                    "summary",
                    "decisions",
                    "risks",
                    "input_artifacts",
                    "output_artifacts",
                    "approval_required",
                ],
                "default_next_command": "bmad-dev-story",
                "artifact_path_guidance": [
                    {
                        "artifact_type": "story",
                        "path_hint": "_bmad-output/implementation-artifacts/<story-file>.md",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return contract_path


def test_summarize_artifact_statuses_uses_implementation_artifacts_as_truth(tmp_path: Path):
    older_ready = tmp_path / "4-4b-batch-d-domain-contract-correction.md"
    newest_review = tmp_path / "4-5a-batch-e-baseline-frontend-security-headers.md"
    done_story = tmp_path / "4-1-staging-environment-parameterization.md"

    write_story(done_story, "4.1: staging-environment-parameterization", "done")
    write_story(older_ready, "4.4b: batch-d-domain-contract-correction", "ready-for-dev")
    write_story(newest_review, "4.5a: batch-e-baseline-frontend-security-headers", "review")

    os.utime(done_story, (1000, 1000))
    os.utime(older_ready, (2000, 2000))
    os.utime(newest_review, (3000, 3000))

    summary = summarize_artifact_statuses(tmp_path)
    artifacts = collect_artifact_statuses(tmp_path)

    assert [artifact.path.name for artifact in artifacts] == [
        newest_review.name,
        older_ready.name,
        done_story.name,
    ]
    assert summary["current"] is not None
    assert summary["current"].path.name == newest_review.name
    assert summary["current"].status == "review"
    assert summary["counts"] == {"review": 1, "ready-for-dev": 1, "done": 1}


def test_execute_command_runs_local_shell_caller_hello_world():
    completed = execute_command(
        [sys.executable, "-c", "print('hello world')"],
        capture_output=True,
    )

    assert completed.returncode == 0
    assert completed.stdout.strip() == "hello world"


def test_collect_planning_artifacts_finds_batch_current_state_docs(tmp_path: Path):
    planning_root = tmp_path / "docs" / "mvp-mentoria"
    planning_root.mkdir(parents=True)
    current_state_doc = planning_root / "batch-f-csp-and-hsts-current-state.md"
    current_state_doc.write_text(
        "\n".join(
            [
                "# Batch F (CSP And HSTS) - Current State (Brownfield)",
                "",
                "Current state findings.",
            ]
        ),
        encoding="utf-8",
    )

    artifacts = collect_planning_artifacts([planning_root])

    assert len(artifacts) == 1
    assert artifacts[0].path.name == "batch-f-csp-and-hsts-current-state.md"
    assert artifacts[0].artifact_type == "current-state"
    assert artifacts[0].title == "Batch F (CSP And HSTS) - Current State (Brownfield)"


def test_load_contract_and_build_contracted_prompt(tmp_path: Path):
    make_contract(tmp_path)
    contract = load_command_contract("bmad-create-story", tmp_path / "contracts")
    context_file = tmp_path / "batch-f-current-state.md"
    context_file.write_text("context", encoding="utf-8")

    prompt = build_command_prompt(
        "bmad-create-story",
        [context_file],
        "Keep scope to Batch F.",
        contract=contract,
        prompt_profile="auto",
    )

    assert contract is not None
    assert contract.command == "bmad-create-story"
    assert "Return a single JSON object inside a ```json fenced block." in prompt
    assert "Allowed output artifact types: story." in prompt
    assert "Keep scope to Batch F." in prompt


def test_extract_validate_materialize_and_log_structured_response(tmp_path: Path):
    make_contract(tmp_path)
    contract = load_command_contract("bmad-create-story", tmp_path / "contracts")
    assert contract is not None

    context_file = tmp_path / "docs" / "mvp-mentoria" / "batch-f-csp-and-hsts-current-state.md"
    context_file.parent.mkdir(parents=True)
    context_file.write_text("# Batch F", encoding="utf-8")

    raw_response = """
Here is the final response.

```json
{
  "status": "completed",
  "summary": "Created the Batch F CSP story.",
  "decisions": ["Constrain scope to CSP only."],
  "risks": ["HSTS remains deferred until host proof exists."],
  "input_artifacts": [
    {
      "path": "docs/mvp-mentoria/batch-f-csp-and-hsts-current-state.md",
      "role": "planning_anchor"
    }
  ],
  "output_artifacts": [
    {
      "artifact_type": "story",
      "path": "_bmad-output/implementation-artifacts/4-6a-batch-f-csp-baseline.md",
      "title": "4.6a Batch F CSP Baseline",
      "content": "# Story 4.6a Batch F CSP Baseline\\n\\nStatus: ready-for-dev\\n"
    }
  ],
  "approval_required": true,
  "next_command": "bmad-dev-story"
}
```
"""

    structured = extract_structured_response(raw_response)
    normalized = validate_command_response(structured, contract, [context_file])
    written_paths = materialize_output_artifacts(normalized, contract, repo_root=tmp_path)
    event_log = write_event_log(
        "bmad-create-story",
        prompt_profile="contracted",
        execution_mode="execute",
        context_files=[context_file],
        contract=contract,
        response=normalized,
        response_capture_path=create_response_capture_path("bmad-create-story", root=tmp_path / "messages"),
        event_root=tmp_path / "events",
    )

    assert normalized["next_command"] == "bmad-dev-story"
    assert written_paths == [tmp_path / "_bmad-output" / "implementation-artifacts" / "4-6a-batch-f-csp-baseline.md"]
    assert written_paths[0].read_text(encoding="utf-8").startswith("# Story 4.6a Batch F CSP Baseline")

    logged = json.loads(event_log.read_text(encoding="utf-8"))
    assert logged["command"] == "bmad-create-story"
    assert logged["next_command"] == "bmad-dev-story"
    assert logged["output_artifacts"][0]["path"] == "_bmad-output/implementation-artifacts/4-6a-batch-f-csp-baseline.md"


def test_infer_next_command_falls_back_to_contract_default(tmp_path: Path):
    make_contract(tmp_path)
    contract = load_command_contract("bmad-create-story", tmp_path / "contracts")
    assert contract is not None

    next_command = infer_next_command({"status": "completed"}, contract)

    assert next_command == "bmad-dev-story"


def test_format_event_summary_prefers_structured_event_log_fields():
    summary = format_event_summary(
        {
            "command": "bmad-code-review",
            "status": "changes_requested",
            "summary": "Scope is correct but one regression remains.",
            "approval_required": True,
            "next_command": "bmad-dev-story",
            "output_artifacts": [
                {
                    "artifact_type": "review-report",
                    "path": "_bmad-output/operator-artifacts/4-6a-review-report.md",
                }
            ],
            "event_log_path": "_bmad-output/operator-events/20260327T190000Z-bmad-code-review.json",
        }
    )

    assert "command        : bmad-code-review" in summary
    assert "status         : changes_requested" in summary
    assert "approval_gate  : yes" in summary
    assert "next_command   : bmad-dev-story" in summary
    assert "- review-report: _bmad-output/operator-artifacts/4-6a-review-report.md" in summary
