from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any, Sequence


STORY_TITLE_RE = re.compile(r"^# Story\s+(.+?)\s*$", re.MULTILINE)
STATUS_RE = re.compile(r"^Status:\s*(.+?)\s*$", re.MULTILINE)
CURRENT_STATE_FILE_RE = re.compile(r"batch-[a-z0-9-]*current-state.*\.md$", re.IGNORECASE)
CURRENT_STATE_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)

DEFAULT_CONTRACTS_ROOT = Path("ops/contracts")
DEFAULT_EVENT_LOG_ROOT = Path("_bmad-output/operator-events")
DEFAULT_RESPONSE_CAPTURE_ROOT = DEFAULT_EVENT_LOG_ROOT / "messages"

DEFAULT_RESPONSE_FIELDS = (
    "status",
    "summary",
    "decisions",
    "risks",
    "input_artifacts",
    "output_artifacts",
    "approval_required",
)


@dataclass(frozen=True)
class ArtifactStatus:
    path: Path
    story_title: str
    status: str
    last_modified: float

    @property
    def last_modified_utc(self) -> str:
        return datetime.fromtimestamp(self.last_modified, tz=timezone.utc).isoformat()


@dataclass(frozen=True)
class PlanningArtifact:
    path: Path
    title: str
    artifact_type: str
    last_modified: float

    @property
    def last_modified_utc(self) -> str:
        return datetime.fromtimestamp(self.last_modified, tz=timezone.utc).isoformat()


@dataclass(frozen=True)
class CommandContract:
    path: Path
    command: str
    prompt_profile: str
    required_inputs: tuple[dict[str, Any], ...]
    output_artifact_types: tuple[str, ...]
    materialized_artifact_types: tuple[str, ...]
    required_response_fields: tuple[str, ...]
    default_next_command: str | None
    artifact_path_guidance: tuple[dict[str, Any], ...]
    raw: dict[str, Any]


@dataclass(frozen=True)
class CommandExecutionResult:
    command: str
    prompt_profile: str
    contract: CommandContract | None
    response_capture_path: Path
    event_log_path: Path
    response: dict[str, Any] | None
    materialized_paths: tuple[Path, ...]


def parse_artifact_status(path: Path) -> ArtifactStatus | None:
    text = path.read_text(encoding="utf-8")
    status_match = STATUS_RE.search(text)
    if status_match is None:
        return None

    title_match = STORY_TITLE_RE.search(text)
    story_title = title_match.group(1).strip() if title_match else path.stem

    return ArtifactStatus(
        path=path,
        story_title=story_title,
        status=status_match.group(1).strip(),
        last_modified=path.stat().st_mtime,
    )


def collect_artifact_statuses(root: Path) -> list[ArtifactStatus]:
    artifacts: list[ArtifactStatus] = []
    for path in root.glob("*.md"):
        artifact = parse_artifact_status(path)
        if artifact is not None:
            artifacts.append(artifact)

    return sorted(artifacts, key=lambda artifact: artifact.last_modified, reverse=True)


def parse_planning_artifact(path: Path) -> PlanningArtifact | None:
    if not CURRENT_STATE_FILE_RE.search(path.name):
        return None

    text = path.read_text(encoding="utf-8")
    title_match = CURRENT_STATE_TITLE_RE.search(text)
    title = title_match.group(1).strip() if title_match else path.stem

    return PlanningArtifact(
        path=path,
        title=title,
        artifact_type="current-state",
        last_modified=path.stat().st_mtime,
    )


def collect_planning_artifacts(roots: Sequence[Path]) -> list[PlanningArtifact]:
    planning_artifacts: list[PlanningArtifact] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.md"):
            artifact = parse_planning_artifact(path)
            if artifact is not None:
                planning_artifacts.append(artifact)

    return sorted(planning_artifacts, key=lambda artifact: artifact.last_modified, reverse=True)


def summarize_artifact_statuses(root: Path, planning_roots: Sequence[Path] | None = None) -> dict:
    artifacts = collect_artifact_statuses(root)
    counts: dict[str, int] = {}
    for artifact in artifacts:
        counts[artifact.status] = counts.get(artifact.status, 0) + 1

    current = next((artifact for artifact in artifacts if artifact.status != "done"), None)
    if current is None and artifacts:
        current = artifacts[0]

    planning_artifacts = collect_planning_artifacts(planning_roots or [])

    return {
        "artifact_root": root,
        "current": current,
        "counts": counts,
        "artifacts": artifacts,
        "planning_artifacts": planning_artifacts,
    }


def execute_command(
    command: Sequence[str],
    *,
    input_text: str | None = None,
    cwd: Path | None = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        input=input_text,
        text=True,
        cwd=str(cwd) if cwd else None,
        capture_output=capture_output,
        check=False,
    )


def load_command_contract(command_name: str, contracts_root: Path | None = None) -> CommandContract | None:
    root = contracts_root or DEFAULT_CONTRACTS_ROOT
    path = root / f"{command_name}.json"
    if not path.exists():
        return None

    data = json.loads(path.read_text(encoding="utf-8"))
    declared_command = data.get("command", command_name)
    if declared_command != command_name:
        raise ValueError(f"Contract command mismatch in {path}: expected {command_name}, found {declared_command}")

    required_fields = tuple(data.get("required_response_fields", DEFAULT_RESPONSE_FIELDS))
    return CommandContract(
        path=path,
        command=declared_command,
        prompt_profile=data.get("prompt_profile", "contracted"),
        required_inputs=tuple(data.get("required_inputs", [])),
        output_artifact_types=tuple(data.get("output_artifact_types", [])),
        materialized_artifact_types=tuple(data.get("materialized_artifact_types", [])),
        required_response_fields=required_fields,
        default_next_command=data.get("default_next_command"),
        artifact_path_guidance=tuple(data.get("artifact_path_guidance", [])),
        raw=data,
    )


def resolve_prompt_profile(prompt_profile: str, contract: CommandContract | None) -> str:
    if prompt_profile == "auto":
        return contract.prompt_profile if contract else "plain"
    return prompt_profile


def build_context_artifacts(context_files: Sequence[Path]) -> list[dict[str, str]]:
    return [{"path": path.as_posix(), "role": "context"} for path in context_files]


def build_command_prompt(
    command_name: str,
    context_files: Sequence[Path],
    instruction: str = "",
    *,
    contract: CommandContract | None = None,
    prompt_profile: str = "auto",
) -> str:
    resolved_profile = resolve_prompt_profile(prompt_profile, contract)
    lines = [
        "You are executing a BMAD command selected by the local operator.",
        "",
        f"Use BMAD command/skill: `{command_name}`",
        "",
    ]

    if context_files:
        lines.extend(["Read these files before acting:"])
        lines.extend(f"- {path.as_posix()}" for path in context_files)
        lines.append("")

    lines.extend(
        [
            "Execution rules:",
            "- Follow the BMAD command strictly.",
            "- Preserve existing architecture and conventions.",
            "- Keep scope constrained to the requested task.",
            "- If the request is ambiguous, ask for clarification before making broad changes.",
        ]
    )

    if contract is not None and resolved_profile == "contracted":
        lines.extend(
            [
                "",
                "Input contract:",
            ]
        )
        if contract.required_inputs:
            for item in contract.required_inputs:
                role = item.get("role", "input")
                description = item.get("description", "")
                lines.append(f"- {role}: {description}".rstrip(": "))
        else:
            lines.append("- Use the provided context files as the required operator inputs.")

        if contract.artifact_path_guidance:
            lines.extend(["", "Artifact path guidance:"])
            for item in contract.artifact_path_guidance:
                artifact_type = item.get("artifact_type", "artifact")
                path_hint = item.get("path_hint", "")
                lines.append(f"- {artifact_type}: {path_hint}".rstrip(": "))

        lines.extend(
            [
                "",
                "Output contract:",
                "- Return a single JSON object inside a ```json fenced block.",
                f"- Required top-level fields: {', '.join(contract.required_response_fields)}.",
                "- `input_artifacts` must be a list of objects with at least `path` and `role`.",
                "- `output_artifacts` must be a list of objects with at least `artifact_type` and `path`.",
            ]
        )
        if contract.output_artifact_types:
            lines.append(f"- Allowed output artifact types: {', '.join(contract.output_artifact_types)}.")
        if contract.materialized_artifact_types:
            lines.append(
                "- For materialized artifacts, include `content` with the final artifact body for: "
                + ", ".join(contract.materialized_artifact_types)
                + "."
            )
        if contract.default_next_command:
            lines.append(f"- If the next step is clear, set `next_command` to `{contract.default_next_command}` or a better justified command.")

    if instruction.strip():
        lines.extend(["", "Additional operator instruction:", instruction.strip()])

    return "\n".join(lines)


def extract_structured_response(response_text: str) -> dict[str, Any]:
    stripped = response_text.strip()
    if not stripped:
        raise ValueError("Empty command response.")

    try:
        candidate = json.loads(stripped)
        if isinstance(candidate, dict):
            return candidate
    except json.JSONDecodeError:
        pass

    fenced_blocks = re.findall(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.IGNORECASE | re.DOTALL)
    for block in fenced_blocks:
        try:
            candidate = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            return candidate

    decoder = json.JSONDecoder()
    for index, char in enumerate(stripped):
        if char != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(stripped[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            return candidate

    raise ValueError("Could not find a JSON object in the command response.")


def infer_next_command(response: dict[str, Any], contract: CommandContract | None) -> str | None:
    next_command = response.get("next_command")
    if isinstance(next_command, str) and next_command.strip():
        return next_command.strip()
    if contract is None:
        return None
    return contract.default_next_command


def validate_command_response(
    response: dict[str, Any],
    contract: CommandContract,
    context_files: Sequence[Path],
) -> dict[str, Any]:
    missing_fields = [field for field in contract.required_response_fields if field not in response]
    if missing_fields:
        raise ValueError(f"Missing required response fields: {', '.join(missing_fields)}")

    if not isinstance(response["summary"], str) or not response["summary"].strip():
        raise ValueError("Response field `summary` must be a non-empty string.")
    if not isinstance(response["approval_required"], bool):
        raise ValueError("Response field `approval_required` must be a boolean.")

    for list_field in ("decisions", "risks", "input_artifacts", "output_artifacts"):
        if not isinstance(response[list_field], list):
            raise ValueError(f"Response field `{list_field}` must be a list.")

    normalized_inputs = response["input_artifacts"] or build_context_artifacts(context_files)
    for item in normalized_inputs:
        if not isinstance(item, dict):
            raise ValueError("Each `input_artifacts` item must be an object.")
        if not isinstance(item.get("path"), str) or not item["path"].strip():
            raise ValueError("Each `input_artifacts` item must include a non-empty `path`.")
        if not isinstance(item.get("role"), str) or not item["role"].strip():
            raise ValueError("Each `input_artifacts` item must include a non-empty `role`.")

    normalized_outputs: list[dict[str, Any]] = []
    for item in response["output_artifacts"]:
        if not isinstance(item, dict):
            raise ValueError("Each `output_artifacts` item must be an object.")
        artifact_type = item.get("artifact_type")
        if not isinstance(artifact_type, str) or not artifact_type.strip():
            raise ValueError("Each `output_artifacts` item must include a non-empty `artifact_type`.")
        if contract.output_artifact_types and artifact_type not in contract.output_artifact_types:
            raise ValueError(f"Artifact type `{artifact_type}` is not allowed by contract `{contract.command}`.")
        path_value = item.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            raise ValueError("Each `output_artifacts` item must include a non-empty `path`.")
        if artifact_type in contract.materialized_artifact_types:
            content_value = item.get("content")
            if not isinstance(content_value, str) or not content_value.strip():
                raise ValueError(
                    f"Artifact `{artifact_type}` must include non-empty `content` for materialization."
                )
        normalized_outputs.append(item)

    normalized_response = dict(response)
    normalized_response["input_artifacts"] = normalized_inputs
    normalized_response["output_artifacts"] = normalized_outputs
    normalized_response["next_command"] = infer_next_command(response, contract)
    return normalized_response


def _resolve_repo_relative_path(path_value: str, repo_root: Path) -> Path:
    candidate = (repo_root / Path(path_value)).resolve()
    root_resolved = repo_root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"Refusing to write outside the repository root: {path_value}") from exc
    return candidate


def materialize_output_artifacts(
    response: dict[str, Any],
    contract: CommandContract,
    *,
    repo_root: Path | None = None,
) -> list[Path]:
    root = (repo_root or Path.cwd()).resolve()
    written_paths: list[Path] = []

    for artifact in response["output_artifacts"]:
        if artifact["artifact_type"] not in contract.materialized_artifact_types:
            continue
        resolved_path = _resolve_repo_relative_path(artifact["path"], root)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        content = artifact["content"].rstrip() + "\n"
        resolved_path.write_text(content, encoding="utf-8")
        written_paths.append(resolved_path)

    return written_paths


def create_response_capture_path(
    command_name: str,
    *,
    root: Path | None = None,
    timestamp: datetime | None = None,
) -> Path:
    capture_root = root or DEFAULT_RESPONSE_CAPTURE_ROOT
    capture_root.mkdir(parents=True, exist_ok=True)
    stamp = (timestamp or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%S%fZ")
    return capture_root / f"{stamp}-{command_name}.md"


def run_codex_exec(
    codex_bin: str,
    prompt_text: str,
    response_capture_path: Path,
    *,
    cwd: Path | None = None,
) -> None:
    resolved_codex = shutil.which(codex_bin)
    if resolved_codex is None:
        raise ValueError(f"Codex CLI not found: {codex_bin}")

    command = [resolved_codex, "exec", "-", "--cd", str(cwd or Path.cwd()), "-o", str(response_capture_path)]
    completed = execute_command(command, input_text=prompt_text, capture_output=True)
    if completed.returncode != 0:
        stdout = completed.stdout.strip() if completed.stdout else ""
        stderr = completed.stderr.strip() if completed.stderr else ""
        details = "\n".join(part for part in [stdout, stderr] if part)
        message = f"Codex exec failed with exit code {completed.returncode}."
        if details:
            message = f"{message}\n{details}"
        raise RuntimeError(message)


def execute_bmad_command(
    command_name: str,
    *,
    prompt_text: str,
    context_files: Sequence[Path],
    prompt_profile: str,
    contract: CommandContract | None,
    codex_bin: str = "codex",
    event_log_root: Path | None = None,
    response_capture_path: Path | None = None,
    repo_root: Path | None = None,
) -> CommandExecutionResult:
    capture_path = response_capture_path or create_response_capture_path(command_name)
    capture_path.parent.mkdir(parents=True, exist_ok=True)
    run_codex_exec(codex_bin, prompt_text, capture_path, cwd=repo_root or Path.cwd())

    response_text = capture_path.read_text(encoding="utf-8") if capture_path.exists() else ""
    normalized_response = None
    materialized_paths: tuple[Path, ...] = ()
    if contract is not None and prompt_profile == "contracted":
        structured_response = extract_structured_response(response_text)
        normalized_response = validate_command_response(structured_response, contract, context_files)
        materialized_paths = tuple(
            materialize_output_artifacts(normalized_response, contract, repo_root=repo_root or Path.cwd())
        )

    event_log_path = write_event_log(
        command_name,
        prompt_profile=prompt_profile,
        execution_mode="execute",
        context_files=context_files,
        contract=contract,
        response=normalized_response,
        response_capture_path=capture_path,
        event_root=event_log_root,
    )

    return CommandExecutionResult(
        command=command_name,
        prompt_profile=prompt_profile,
        contract=contract,
        response_capture_path=capture_path,
        event_log_path=event_log_path,
        response=normalized_response,
        materialized_paths=materialized_paths,
    )


def write_event_log(
    command_name: str,
    *,
    prompt_profile: str,
    execution_mode: str,
    context_files: Sequence[Path],
    contract: CommandContract | None = None,
    response: dict[str, Any] | None = None,
    response_capture_path: Path | None = None,
    event_root: Path | None = None,
) -> Path:
    root = event_root or DEFAULT_EVENT_LOG_ROOT
    root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc)
    event_path = root / f"{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}-{command_name}.json"

    payload: dict[str, Any] = {
        "timestamp_utc": timestamp.isoformat(),
        "command": command_name,
        "prompt_profile": prompt_profile,
        "execution_mode": execution_mode,
        "contract": contract.command if contract else None,
        "response_capture_path": response_capture_path.as_posix() if response_capture_path else None,
        "input_artifacts": build_context_artifacts(context_files),
    }

    if response is not None:
        payload.update(
            {
                "status": response.get("status"),
                "summary": response.get("summary"),
                "decisions": response.get("decisions", []),
                "risks": response.get("risks", []),
                "approval_required": response.get("approval_required"),
                "next_command": infer_next_command(response, contract),
                "input_artifacts": response.get("input_artifacts", payload["input_artifacts"]),
                "output_artifacts": [
                    {
                        "artifact_type": artifact.get("artifact_type"),
                        "path": artifact.get("path"),
                        "title": artifact.get("title"),
                    }
                    for artifact in response.get("output_artifacts", [])
                ],
            }
        )

    event_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return event_path


def load_event_log(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def format_event_summary(event: dict[str, Any]) -> str:
    lines = [
        f"command        : {event.get('command', 'unknown')}",
        f"status         : {event.get('status', 'no-structured-status')}",
    ]

    summary = event.get("summary")
    if isinstance(summary, str) and summary.strip():
        lines.append(f"summary        : {summary.strip()}")

    approval_required = event.get("approval_required")
    if approval_required is not None:
        lines.append(f"approval_gate  : {'yes' if approval_required else 'no'}")

    next_command = event.get("next_command")
    if isinstance(next_command, str) and next_command.strip():
        lines.append(f"next_command   : {next_command.strip()}")

    output_artifacts = event.get("output_artifacts") or []
    if output_artifacts:
        lines.append("output_artifacts:")
        for artifact in output_artifacts:
            artifact_type = artifact.get("artifact_type", "artifact")
            path = artifact.get("path", "")
            lines.append(f"- {artifact_type}: {path}".rstrip(": "))

    event_log_path = event.get("event_log_path")
    if isinstance(event_log_path, str) and event_log_path.strip():
        lines.append(f"event_log      : {event_log_path}")

    return "\n".join(lines)
