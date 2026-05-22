from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.storage.json_repository import JsonRepository


def default_enrollment_store_path() -> Path:
    configured = os.getenv("ENROLLMENT_STORE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "enrollments.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")



class EnrollmentRepository:
    def delete_all(self) -> None:
        """Remove all enrollments from the store."""
        self._write_items([])

    def __init__(self, file_path: str | Path | None = None) -> None:
        self._store = JsonRepository(file_path or default_enrollment_store_path())
        if not self._store.file_path.exists():
            self._store.write({"version": 1, "items": []})

    def _read_items(self) -> list[dict[str, Any]]:
        payload = self._store.read()
        items = payload.get("items", [])
        return [item for item in items if isinstance(item, dict)]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        self._store.write({"version": 1, "items": items})

    def list_enrollments(self) -> list[dict[str, Any]]:
        return self._read_items()

    def create(
        self,
        *,
        student_id: str,
        organization_id: str,
        mentor_id: str | None = None,
        progress_score: float,
        engagement_score: float,
        urgency_status: str = "normal",
        day: int = 0,
        total_days: int = 0,
        days_left: int = 0,
        ltv_cents: int = 0,
        link_reason: str | None = None,
        source_enrollment_id: str | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        items = self._read_items()
        now = _now_iso()
        enrollment = {
            "id": f"enr_{len(items) + 1}",
            "student_id": student_id,
            "organization_id": organization_id,
            "mentor_id": mentor_id,
            "progress_score": float(progress_score),
            "engagement_score": float(engagement_score),
            "urgency_status": urgency_status,
            "day": int(day),
            "total_days": int(total_days),
            "days_left": int(days_left),
            "ltv_cents": int(ltv_cents),
            "link_reason": link_reason,
            "source_enrollment_id": source_enrollment_id,
            "created_by": created_by,
            "deactivated_at": None,
            "deactivated_reason": None,
            "deactivated_by": None,
            "reassigned_to_mentor_id": None,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        items.append(enrollment)
        self._write_items(items)
        return enrollment

    def list_by_organization(self, organization_id: str) -> list[dict[str, Any]]:
        return [
            enrollment
            for enrollment in self._read_items()
            if str(enrollment.get("organization_id")) == organization_id
        ]

    def list_by_mentor(self, mentor_id: str) -> list[dict[str, Any]]:
        return [
            enrollment
            for enrollment in self._read_items()
            if str(enrollment.get("mentor_id") or "") == mentor_id
        ]

    def list_by_student(self, student_id: str) -> list[dict[str, Any]]:
        return [
            enrollment
            for enrollment in self._read_items()
            if str(enrollment.get("student_id") or "") == student_id
        ]

    def get_active_by_student(self, student_id: str) -> dict[str, Any] | None:
        for enrollment in self._read_items():
            if str(enrollment.get("student_id")) == student_id and bool(enrollment.get("is_active", True)):
                return enrollment
        return None

    def get_by_id(self, enrollment_id: str) -> dict[str, Any] | None:
        for enrollment in self._read_items():
            if str(enrollment.get("id") or "") == enrollment_id:
                return enrollment
        return None

    def deactivate(
        self,
        enrollment_id: str,
        *,
        justification: str,
        performed_by: str | None = None,
        reassigned_to_mentor_id: str | None = None,
    ) -> dict[str, Any] | None:
        items = self._read_items()
        for index, enrollment in enumerate(items):
            if str(enrollment.get("id") or "") != enrollment_id:
                continue
            enrollment["is_active"] = False
            enrollment["deactivated_at"] = _now_iso()
            enrollment["deactivated_reason"] = justification
            enrollment["deactivated_by"] = performed_by
            enrollment["reassigned_to_mentor_id"] = reassigned_to_mentor_id
            enrollment["updated_at"] = enrollment["deactivated_at"]
            items[index] = enrollment
            self._write_items(items)
            return enrollment
        return None
