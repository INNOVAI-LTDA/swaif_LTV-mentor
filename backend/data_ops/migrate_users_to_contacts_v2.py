from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROLE_PRIORITY = {"admin": 3, "provider": 2, "client": 1}


@dataclass(frozen=True)
class Candidate:
    id: str
    email: str
    role: str
    full_name: str
    is_active: bool
    source: str
    original_role: str
    password_hash: str | None = None
    organization_id: str | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_items(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    if not isinstance(items, list):
        raise ValueError(f"Invalid payload in {path}: items must be a list")
    return [item for item in items if isinstance(item, dict)]


def _normalize_email(raw: Any) -> str:
    return str(raw or "").strip().lower()


def _required(value: Any, field_name: str, source: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"Missing required field '{field_name}' for source '{source}'")
    return normalized


def _map_user_role(role: str) -> str:
    if role == "admin":
        return "admin"
    if role == "mentor":
        return "provider"
    raise ValueError(f"Unsupported user role: {role}")


def collect_candidates(*, users: list[dict[str, Any]], mentors: list[dict[str, Any]], students: list[dict[str, Any]]) -> list[Candidate]:
    candidates: list[Candidate] = []

    for item in users:
        item_id = _required(item.get("id"), "id", "users")
        email = _normalize_email(_required(item.get("email"), "email", "users"))
        role = _map_user_role(_required(item.get("role"), "role", "users"))
        candidates.append(
            Candidate(
                id=item_id,
                email=email,
                role=role,
                full_name=str(item.get("full_name") or item_id),
                is_active=bool(item.get("is_active", True)),
                source="users",
                original_role=str(item.get("role") or ""),
                password_hash=str(item.get("password_hash") or "") or None,
                organization_id=str(item.get("organization_id") or "") or None,
            )
        )

    for item in mentors:
        item_id = _required(item.get("id"), "id", "mentors")
        email = _normalize_email(_required(item.get("email"), "email", "mentors"))
        full_name = _required(item.get("full_name"), "full_name", "mentors")
        candidates.append(
            Candidate(
                id=item_id,
                email=email,
                role="provider",
                full_name=full_name,
                is_active=bool(item.get("is_active", True)),
                source="mentors",
                original_role="mentor",
                organization_id=str(item.get("organization_id") or "") or None,
            )
        )

    for item in students:
        item_id = _required(item.get("id"), "id", "students")
        email = _normalize_email(_required(item.get("email"), "email", "students"))
        full_name = _required(item.get("full_name"), "full_name", "students")
        candidates.append(
            Candidate(
                id=item_id,
                email=email,
                role="client",
                full_name=full_name,
                is_active=bool(item.get("is_active", True)),
                source="students",
                original_role="student",
            )
        )

    return candidates


def deduplicate_candidates(candidates: list[Candidate]) -> tuple[list[Candidate], list[dict[str, Any]]]:
    selected: dict[str, Candidate] = {}
    duplicates: list[dict[str, Any]] = []

    for candidate in candidates:
        existing = selected.get(candidate.email)
        if existing is None:
            selected[candidate.email] = candidate
            continue

        existing_priority = ROLE_PRIORITY[existing.role]
        current_priority = ROLE_PRIORITY[candidate.role]

        if current_priority > existing_priority:
            winner = candidate
            loser = existing
            selected[candidate.email] = candidate
        else:
            winner = existing
            loser = candidate

        duplicates.append(
            {
                "email": candidate.email,
                "kept_id": winner.id,
                "kept_role": winner.role,
                "discarded_id": loser.id,
                "discarded_role": loser.role,
                "discarded_source": loser.source,
                "reason": "email duplicate resolved by role priority admin > provider > client",
            }
        )

    return list(selected.values()), duplicates


def build_contacts_payload(items: list[Candidate]) -> dict[str, Any]:
    now = _now_iso()
    contacts: list[dict[str, Any]] = []
    for item in items:
        record: dict[str, Any] = {
            "id": item.id,
            "full_name": item.full_name,
            "email": item.email,
            "role": item.role,
            "is_active": item.is_active,
            "created_at": now,
            "updated_at": now,
        }
        if item.password_hash:
            record["password_hash"] = item.password_hash
        if item.organization_id:
            record["organization_id"] = item.organization_id
        contacts.append(record)
    return {"version": 2, "items": contacts}


def build_report(*, candidates: list[Candidate], deduped: list[Candidate], duplicates: list[dict[str, Any]]) -> dict[str, Any]:
    source_counts = Counter([item.source for item in candidates])
    final_role_counts = Counter([item.role for item in deduped])
    return {
        "generated_at": _now_iso(),
        "inputs": {
            "users": source_counts.get("users", 0),
            "mentors": source_counts.get("mentors", 0),
            "students": source_counts.get("students", 0),
            "total_candidates": len(candidates),
        },
        "outputs": {
            "total_contacts": len(deduped),
            "by_role": {
                "admin": final_role_counts.get("admin", 0),
                "provider": final_role_counts.get("provider", 0),
                "client": final_role_counts.get("client", 0),
            },
        },
        "duplicates": {
            "count": len(duplicates),
            "discarded": duplicates,
        },
        "discarded_total": len(duplicates),
        "deduplication_precedence": ["admin", "provider", "client"],
    }


def run_migration(base_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    users = _load_items(base_path / "users.json")
    mentors = _load_items(base_path / "mentors.json")
    students = _load_items(base_path / "students.json")

    candidates = collect_candidates(users=users, mentors=mentors, students=students)
    deduped, duplicates = deduplicate_candidates(candidates)

    contacts_payload = build_contacts_payload(deduped)
    report_payload = build_report(candidates=candidates, deduped=deduped, duplicates=duplicates)
    return contacts_payload, report_payload


def main() -> None:
    data_dir = Path(__file__).resolve().parents[1] / "data"
    contacts_payload, report_payload = run_migration(data_dir)

    (data_dir / "contacts_users_v2.json").write_text(json.dumps(contacts_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (data_dir / "contacts_users_v2_migration_report.json").write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
