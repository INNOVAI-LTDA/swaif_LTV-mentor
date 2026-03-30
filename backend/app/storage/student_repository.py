from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.storage.json_repository import JsonRepository


def default_student_store_path() -> Path:
    configured = os.getenv("STUDENT_STORE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "students.json"


def _default_initials(full_name: str) -> str:
    parts = [part for part in full_name.strip().split() if part]
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    compact = full_name.strip().replace(" ", "")
    return (compact[:2] or "AL").upper()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_cpf(value: str | None) -> str | None:
    if value is None:
        return None
    digits = "".join(char for char in value if char.isdigit())
    return digits or None


class StudentRepository:
    def update(self, **kwargs) -> dict[str, Any]:
        student_id = kwargs.get("id")
        if not student_id:
            raise ValueError("Student id is required for update")
        items = self._read_items()
        for idx, student in enumerate(items):
            if str(student.get("id")) == student_id:
                updated = {**student, **kwargs, "updated_at": _now_iso()}
                items[idx] = updated
                self._write_items(items)
                return updated
        raise ValueError(f"Student with id {student_id} not found")

    def delete(self, student_id: str) -> bool:
        items = self._read_items()
        new_items = [student for student in items if str(student.get("id")) != student_id]
        if len(new_items) == len(items):
            return False
        self._write_items(new_items)
        return True
    def __init__(self, file_path: str | Path | None = None) -> None:
        self._store = JsonRepository(file_path or default_student_store_path())
        if not self._store.file_path.exists():
            self._store.write({"version": 1, "items": []})

    def _read_items(self) -> list[dict[str, Any]]:
        payload = self._store.read()
        items = payload.get("items", [])
        return [item for item in items if isinstance(item, dict)]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        self._store.write({"version": 1, "items": items})

    def list_students(self) -> list[dict[str, Any]]:
        return self._read_items()

    def create(
        self,
        *,
        full_name: str,
        initials: str | None = None,
        email: str | None = None,
        cpf: str | None = None,
        phone: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        items = self._read_items()
        normalized_email = email.strip().lower() if email else None
        normalized_cpf = _normalize_cpf(cpf)
        if normalized_email and any(str(item.get("email", "")).strip().lower() == normalized_email for item in items):
            raise ValueError("student email already exists")
        if normalized_cpf and any(_normalize_cpf(str(item.get("cpf") or "")) == normalized_cpf for item in items):
            raise ValueError("student cpf already exists")
        if any(str(item.get("full_name", "")).strip().lower() == full_name.strip().lower() for item in items):
            raise ValueError("student full_name already exists")
        now = _now_iso()
        student = {
            "id": f"std_{len(items) + 1}",
            "full_name": full_name.strip(),
            "initials": (initials or _default_initials(full_name)).upper(),
            "email": normalized_email,
            "cpf": normalized_cpf,
            "phone": phone.strip() if phone else None,
            "notes": notes.strip() if notes else None,
            "status": "active",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        items.append(student)
        self._write_items(items)
        return student

    def get_by_id(self, student_id: str) -> dict[str, Any] | None:
        for student in self._read_items():
            if str(student.get("id")) == student_id:
                return student
        return None
