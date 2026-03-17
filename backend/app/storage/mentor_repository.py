from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.storage.json_repository import JsonRepository


def default_mentor_store_path() -> Path:
    configured = os.getenv("MENTOR_STORE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "mentors.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_cpf(value: str | None) -> str | None:
    if value is None:
        return None
    digits = "".join(char for char in value if char.isdigit())
    return digits or None


class MentorRepository:
    def __init__(self, file_path: str | Path | None = None) -> None:
        self._store = JsonRepository(file_path or default_mentor_store_path())
        if not self._store.file_path.exists():
            self._store.write({"version": 1, "items": []})

    def _read_items(self) -> list[dict[str, Any]]:
        payload = self._store.read()
        items = payload.get("items", [])
        return [item for item in items if isinstance(item, dict)]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        self._store.write({"version": 1, "items": items})

    def list_mentors(self) -> list[dict[str, Any]]:
        return self._read_items()

    def list_by_organization(self, organization_id: str) -> list[dict[str, Any]]:
        return [
            item
            for item in self._read_items()
            if str(item.get("organization_id") or "") == organization_id
        ]

    def create(
        self,
        *,
        full_name: str,
        email: str,
        cpf: str | None = None,
        organization_id: str | None = None,
        phone: str | None = None,
        bio: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        items = self._read_items()
        normalized_name = full_name.strip()
        normalized_email = email.strip().lower()
        normalized_cpf = _normalize_cpf(cpf)
        if any(str(item.get("email", "")).strip().lower() == normalized_email for item in items):
            raise ValueError("mentor email already exists")
        if normalized_cpf and any(_normalize_cpf(str(item.get("cpf") or "")) == normalized_cpf for item in items):
            raise ValueError("mentor cpf already exists")

        now = _now_iso()

        mentor = {
            "id": f"mtr_{len(items) + 1}",
            "full_name": normalized_name,
            "email": normalized_email,
            "cpf": normalized_cpf,
            "phone": phone.strip() if phone else None,
            "bio": bio.strip() if bio else None,
            "notes": notes.strip() if notes else None,
            "status": "active",
            "is_active": True,
            "organization_id": organization_id,
            "created_at": now,
            "updated_at": now,
        }
        items.append(mentor)
        self._write_items(items)
        return mentor

    def get_by_id(self, mentor_id: str) -> dict[str, Any] | None:
        for mentor in self._read_items():
            if str(mentor.get("id")) == mentor_id:
                return mentor
        return None

    def set_organization(self, mentor_id: str, organization_id: str) -> dict[str, Any] | None:
        items = self._read_items()
        for idx, mentor in enumerate(items):
            if str(mentor.get("id")) == mentor_id:
                mentor["organization_id"] = organization_id
                mentor["updated_at"] = _now_iso()
                items[idx] = mentor
                self._write_items(items)
                return mentor
        return None
