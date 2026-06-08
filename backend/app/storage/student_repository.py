from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from app.config.runtime import get_supabase_db_connect_timeout_seconds, get_supabase_db_url

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


def _connect(database_url: str) -> Any:
    if psycopg is None:
        raise RuntimeError("SUPABASE_DB_URL is configured but psycopg is not installed.")
    return psycopg.connect(
        database_url,
        prepare_threshold=None,
        connect_timeout=get_supabase_db_connect_timeout_seconds(),
    )


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


def _as_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    text = str(value).strip()
    return text or None


def _normalize_cpf(value: str | None) -> str | None:
    if value is None:
        return None
    digits = "".join(char for char in value if char.isdigit())
    return digits or None


class StudentRepository:
    _memory_stores: dict[str, list[dict[str, Any]]] = {}
    _memory_lock = RLock()

    def __init__(self, file_path: str | Path | None = None) -> None:
        self._namespace = str((Path(file_path) if file_path is not None else default_student_store_path()).resolve())
        self._database_url = get_supabase_db_url()
        self._use_postgres = bool(self._database_url)
        if self._use_postgres and psycopg is None:
            raise RuntimeError("SUPABASE_DB_URL is configured but psycopg is not installed.")
        if not self._use_postgres:
            self._memory_items()

    def _memory_items(self) -> list[dict[str, Any]]:
        with self._memory_lock:
            items = self._memory_stores.get(self._namespace)
            if items is None:
                items = []
                self._memory_stores[self._namespace] = items
            return items

    @staticmethod
    def _row_to_student(row: dict[str, Any]) -> dict[str, Any]:
        full_name = str(row.get("full_name") or row.get("email") or "Aluno")
        created_at = _as_iso(row.get("created_at")) or _now_iso()
        updated_at = _as_iso(row.get("updated_at")) or _now_iso()
        return {
            "id": str(row.get("id") or ""),
            "full_name": full_name,
            "initials": _default_initials(full_name),
            "email": str(row.get("email") or "").strip().lower() or None,
            "cpf": None,
            "phone": None,
            "notes": None,
            "start_enrollment_date": None,
            "end_enrollment_date": None,
            "status": "active" if bool(row.get("is_active", True)) else "inactive",
            "is_active": bool(row.get("is_active", True)),
            "created_at": created_at,
            "updated_at": updated_at,
        }

    def _list_students_from_postgres(self) -> list[dict[str, Any]]:
        assert self._database_url
        with _connect(self._database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, full_name, email, is_active, created_at, updated_at
                    FROM deva_accmed_users
                    WHERE lower(role) IN ('client', 'student', 'aluno')
                    """
                )
                columns = [column[0] for column in (cur.description or ())]
                rows = [dict(zip(columns, row)) for row in cur.fetchall()]
        return [self._row_to_student(row) for row in rows]

    def _list_students_from_snapshot(self) -> list[dict[str, Any]]:
        snapshot_path = Path(self._namespace)
        if not snapshot_path.exists():
            return []
        try:
            payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []

        raw_items = payload.get("items", []) if isinstance(payload, dict) else []
        students = [dict(item) for item in raw_items if isinstance(item, dict)]
        if students:
            return students
        return []

    def update(self, **kwargs) -> dict[str, Any]:
        if self._use_postgres:
            raise RuntimeError("Student update is not supported in Supabase runtime store mode.")
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
        if self._use_postgres:
            raise RuntimeError("Student delete is not supported in Supabase runtime store mode.")
        items = self._read_items()
        new_items = [student for student in items if str(student.get("id")) != student_id]
        if len(new_items) == len(items):
            return False
        self._write_items(new_items)
        return True

    def _read_items(self) -> list[dict[str, Any]]:
        if self._use_postgres:
            snapshot_students = self._list_students_from_snapshot()
            if snapshot_students:
                return snapshot_students
            return self._list_students_from_postgres()
        return [dict(item) for item in self._memory_items() if isinstance(item, dict)]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        if self._use_postgres:
            raise RuntimeError("Student write is not supported in Supabase runtime store mode.")
        with self._memory_lock:
            self._memory_stores[self._namespace] = [dict(item) for item in items]

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
        start_enrollment_date: str | None = None,
        end_enrollment_date: str | None = None,
    ) -> dict[str, Any]:
        if self._use_postgres:
            raise RuntimeError("Student create is not supported in Supabase runtime store mode.")
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
            "start_enrollment_date": start_enrollment_date.strip() if start_enrollment_date else None,
            "end_enrollment_date": end_enrollment_date.strip() if end_enrollment_date else None,
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
