from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.json_repository import JsonRepository


def default_product_assignment_store_path() -> Path:
    configured = os.getenv("PRODUCT_ASSIGNMENT_STORE_PATH")
    if configured:
        return Path(configured)

    enrollment_configured = os.getenv("ENROLLMENT_STORE_PATH")
    if enrollment_configured:
        return Path(enrollment_configured).with_name("product_assignments.json")

    return Path(__file__).resolve().parents[2] / "data" / "product_assignments.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ProductAssignmentRepository:
    def __init__(
        self,
        file_path: str | Path | None = None,
        enrollments: EnrollmentRepository | None = None,
    ) -> None:
        self._store = JsonRepository(file_path or default_product_assignment_store_path())
        self._enrollments = enrollments or EnrollmentRepository()
        if not self._store.file_path.exists():
            self._store.write({"version": 1, "items": []})

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        self._store.write({"version": 1, "items": items})

    @staticmethod
    def _as_optional_str(value: Any) -> str | None:
        text = str(value or "").strip()
        return text or None

    @classmethod
    def _from_enrollment(cls, enrollment: dict[str, Any]) -> dict[str, Any]:
        assignment_id = str(enrollment.get("id") or "")
        product_id = str(enrollment.get("organization_id") or "")
        provider_id = cls._as_optional_str(enrollment.get("mentor_id"))
        end_user_id = str(enrollment.get("student_id") or "")
        is_active = bool(enrollment.get("is_active", True))
        status = str(enrollment.get("status") or ("active" if is_active else "inactive"))
        created_at = cls._as_optional_str(enrollment.get("created_at"))
        updated_at = cls._as_optional_str(enrollment.get("updated_at")) or _now_iso()
        deactivated_at = cls._as_optional_str(enrollment.get("deactivated_at"))
        start_at = cls._as_optional_str(enrollment.get("start_at")) or created_at
        end_at = cls._as_optional_str(enrollment.get("end_at")) or deactivated_at

        return {
            "id": assignment_id,
            "assignment_id": assignment_id,
            "product_id": product_id,
            "provider_id": provider_id,
            "end_user_id": end_user_id,
            "status": status,
            "start_at": start_at,
            "end_at": end_at,
            "days_left": int(enrollment.get("days_left") or 0),
            "ltv_cents": int(enrollment.get("ltv_cents") or 0),
            "progress_score": float(enrollment.get("progress_score") or 0),
            "engagement_score": float(enrollment.get("engagement_score") or 0),
            "urgency_status": str(enrollment.get("urgency_status") or "normal"),
            "day": int(enrollment.get("day") or 0),
            "total_days": int(enrollment.get("total_days") or 0),
            "is_active": is_active,
            "link_reason": cls._as_optional_str(enrollment.get("link_reason")),
            "source_assignment_id": cls._as_optional_str(enrollment.get("source_enrollment_id")),
            "created_by": cls._as_optional_str(enrollment.get("created_by")),
            "deactivated_at": deactivated_at,
            "deactivated_reason": cls._as_optional_str(enrollment.get("deactivated_reason")),
            "deactivated_by": cls._as_optional_str(enrollment.get("deactivated_by")),
            "reassigned_to_provider_id": cls._as_optional_str(enrollment.get("reassigned_to_mentor_id")),
            "created_at": created_at,
            "updated_at": updated_at,
            # Legacy aliases maintained for v1 compatibility within service assembly.
            "organization_id": product_id,
            "mentor_id": provider_id,
            "student_id": end_user_id,
            "source_enrollment_id": cls._as_optional_str(enrollment.get("source_enrollment_id")),
            "reassigned_to_mentor_id": cls._as_optional_str(enrollment.get("reassigned_to_mentor_id")),
        }

    def _seed_from_enrollments_if_needed(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if items:
            return items

        seeded = [self._from_enrollment(item) for item in self._enrollments.list_enrollments()]
        if seeded:
            self._write_items(seeded)
        return seeded

    def _read_items(self) -> list[dict[str, Any]]:
        payload = self._store.read()
        raw_items = payload.get("items", [])
        items = [item for item in raw_items if isinstance(item, dict)]
        return self._seed_from_enrollments_if_needed(items)

    def list_assignments(self) -> list[dict[str, Any]]:
        return self._read_items()

    def get_by_id(self, assignment_id: str) -> dict[str, Any] | None:
        for item in self._read_items():
            if str(item.get("id") or "") == assignment_id:
                return item
        return None

    def list_by_student(self, student_id: str) -> list[dict[str, Any]]:
        return [
            item
            for item in self._read_items()
            if str(item.get("student_id") or "") == student_id
        ]

    def list_by_mentor(self, mentor_id: str) -> list[dict[str, Any]]:
        return [
            item
            for item in self._read_items()
            if str(item.get("mentor_id") or "") == mentor_id
        ]

    def get_active_by_student(self, student_id: str) -> dict[str, Any] | None:
        for item in self.list_by_student(student_id):
            if bool(item.get("is_active", True)):
                return item
        return None

    def upsert_from_enrollment(self, enrollment: dict[str, Any]) -> dict[str, Any]:
        row = self._from_enrollment(enrollment)
        items = self._read_items()
        assignment_id = str(row.get("id") or "")
        for index, existing in enumerate(items):
            if str(existing.get("id") or "") == assignment_id:
                items[index] = row
                self._write_items(items)
                return row

        items.append(row)
        self._write_items(items)
        return row

    def deactivate(
        self,
        assignment_id: str,
        *,
        justification: str,
        performed_by: str | None = None,
        reassigned_to_provider_id: str | None = None,
    ) -> dict[str, Any] | None:
        items = self._read_items()
        for index, item in enumerate(items):
            if str(item.get("id") or "") != assignment_id:
                continue

            deactivated_at = _now_iso()
            item["is_active"] = False
            item["status"] = "inactive"
            item["end_at"] = deactivated_at
            item["deactivated_at"] = deactivated_at
            item["deactivated_reason"] = justification
            item["deactivated_by"] = performed_by
            item["reassigned_to_provider_id"] = reassigned_to_provider_id
            item["reassigned_to_mentor_id"] = reassigned_to_provider_id
            item["updated_at"] = deactivated_at
            items[index] = item
            self._write_items(items)
            return item
        return None
