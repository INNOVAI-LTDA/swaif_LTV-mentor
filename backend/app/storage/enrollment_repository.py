from pathlib import Path
from datetime import datetime, timezone
from threading import RLock
from typing import Any

def default_enrollment_store_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "enrollments.json"

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

class EnrollmentRepository:
    _memory_stores: dict[str, list[dict[str, Any]]] = {}
    _memory_lock = RLock()

    def __init__(self, file_path: str | Path | None = None) -> None:
        self._namespace = str((file_path or default_enrollment_store_path()).resolve())
        if self._namespace not in self._memory_stores:
            self._memory_stores[self._namespace] = []

    def _memory_items(self) -> list[dict[str, Any]]:
        with self._memory_lock:
            return self._memory_stores.get(self._namespace, [])

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        with self._memory_lock:
            self._memory_stores[self._namespace] = [dict(item) for item in items]

    def _read_items(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._memory_items() if isinstance(item, dict) and item.get("deleted_at") is None]

    def list_enrollments(self) -> list[dict[str, Any]]:
        return self._read_items()

    def create(
        self,
        *,
        student_id: int,
        organization_id: int,
        mentor_id: int | None = None,
        progress_score: float,
        engagement_score: float,
        urgency_status: str = "normal",
        day: int = 0,
        total_days: int = 0,
        days_left: int = 0,
        ltv_cents: int = 0,
        link_reason: str | None = None,
        source_enrollment_id: int | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        items = self._read_items()
        now = _now_iso()
        new_id = max([e["id"] for e in items if "id" in e and isinstance(e["id"], int)] + [0]) + 1
        enrollment = {
            "id": new_id,
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
            "deleted_at": None,
        }
        items.append(enrollment)
        self._write_items(items)
        return enrollment

    def list_by_organization(self, organization_id: int) -> list[dict[str, Any]]:
        return [
            enrollment
            for enrollment in self._read_items()
            if int(enrollment.get("organization_id") or 0) == int(organization_id)
        ]

    def list_by_mentor(self, mentor_id: int) -> list[dict[str, Any]]:
        return [
            enrollment
            for enrollment in self._read_items()
            if int(enrollment.get("mentor_id") or 0) == int(mentor_id)
        ]

    def list_by_student(self, student_id: int) -> list[dict[str, Any]]:
        return [
            enrollment
            for enrollment in self._read_items()
            if int(enrollment.get("student_id") or 0) == int(student_id)
        ]

    def get_active_by_student(self, student_id: int) -> dict[str, Any] | None:
        for enrollment in self._read_items():
            if int(enrollment.get("student_id") or 0) == int(student_id) and bool(enrollment.get("is_active", True)):
                return enrollment
        return None

    def get_by_id(self, enrollment_id: int) -> dict[str, Any] | None:
        for enrollment in self._read_items():
            if int(enrollment.get("id") or 0) == int(enrollment_id):
                return enrollment
        return None

    def deactivate(
        self,
        enrollment_id: int,
        *,
        justification: str,
        performed_by: str | None = None,
        reassigned_to_mentor_id: int | None = None,
    ) -> dict[str, Any] | None:
        items = self._read_items()
        for index, enrollment in enumerate(items):
            if int(enrollment.get("id") or 0) != int(enrollment_id):
                continue
            enrollment["is_active"] = False
            enrollment["deactivated_at"] = _now_iso()
            enrollment["deactivated_reason"] = justification
            enrollment["deactivated_by"] = performed_by
            enrollment["reassigned_to_mentor_id"] = reassigned_to_mentor_id
            enrollment["updated_at"] = enrollment["deactivated_at"]
            enrollment["deleted_at"] = enrollment["deactivated_at"]
            items[index] = enrollment
            self._write_items(items)
            return enrollment
        return None

    def soft_delete(self, enrollment_id: int) -> bool:
        items = self._read_items()
        for enrollment in items:
            if int(enrollment.get("id") or 0) == int(enrollment_id):
                enrollment["deleted_at"] = _now_iso()
                self._write_items(items)
                return True
        return False
from pathlib import Path
from datetime import datetime, timezone
from threading import RLock
from typing import Any

def default_enrollment_store_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "enrollments.json"

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    _memory_stores: dict[str, list[dict[str, Any]]] = {}
    _memory_lock = RLock()

    def __init__(self, file_path: str | Path | None = None) -> None:
        self._namespace = str((file_path or default_enrollment_store_path()).resolve())
        if self._namespace not in self._memory_stores:
            self._memory_stores[self._namespace] = []

    def _memory_items(self) -> list[dict[str, Any]]:
        with self._memory_lock:
            return self._memory_stores.get(self._namespace, [])

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        with self._memory_lock:
            self._memory_stores[self._namespace] = [dict(item) for item in items]

    def _read_items(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._memory_items() if isinstance(item, dict) and item.get("deleted_at") is None]


    def list_enrollments(self) -> list[dict[str, Any]]:
        return self._read_items()

    def create(
        self,
        *,
        student_id: int,
        organization_id: int,
        mentor_id: int | None = None,
        progress_score: float,
        engagement_score: float,
        urgency_status: str = "normal",
        day: int = 0,
        total_days: int = 0,
        days_left: int = 0,
        ltv_cents: int = 0,
        link_reason: str | None = None,
        source_enrollment_id: int | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        items = self._read_items()
        now = _now_iso()
        new_id = max([e["id"] for e in items if "id" in e and isinstance(e["id"], int)] + [0]) + 1
        enrollment = {
            "id": new_id,
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
            "deleted_at": None,
        }
        items.append(enrollment)
        self._write_items(items)
        return enrollment

    def list_by_organization(self, organization_id: int) -> list[dict[str, Any]]:
        return [
            enrollment
            for enrollment in self._read_items()
            if int(enrollment.get("organization_id") or 0) == int(organization_id)
        ]

    def list_by_mentor(self, mentor_id: int) -> list[dict[str, Any]]:
        return [
            enrollment
            for enrollment in self._read_items()
            if int(enrollment.get("mentor_id") or 0) == int(mentor_id)
        ]

    def backfill_active_mentor_ids(self, mentor_id_by_organization: dict[int, int]) -> dict[str, int]:
        """
        Controlled backfill for legacy active enrollments missing mentor linkage.
        Only fills empty mentor_id using an explicit organization->mentor mapping.
        """
        items = self._read_items()
        updated = 0
        scanned_active = 0

        for index, enrollment in enumerate(items):
            if not bool(enrollment.get("is_active", True)):
                continue
            scanned_active += 1

            current_mentor_id = str(enrollment.get("mentor_id") or "").strip()
            if current_mentor_id:
                continue

            organization_id = str(enrollment.get("organization_id") or "").strip()
            mapped_mentor_id = str(mentor_id_by_organization.get(organization_id) or "").strip()
            if not mapped_mentor_id:
                continue

            patched = dict(enrollment)
            patched["mentor_id"] = mapped_mentor_id
            patched["updated_at"] = _now_iso()
            items[index] = patched
            updated += 1

        if updated:
            self._write_items(items)

        return {"scanned_active": scanned_active, "updated": updated}

    def list_by_student(self, student_id: int) -> list[dict[str, Any]]:
        return [
            enrollment
            for enrollment in self._read_items()
            if int(enrollment.get("student_id") or 0) == int(student_id)
        ]

    def get_active_by_student(self, student_id: int) -> dict[str, Any] | None:
        for enrollment in self._read_items():
            if int(enrollment.get("student_id") or 0) == int(student_id) and bool(enrollment.get("is_active", True)):
                return enrollment
        return None

    def get_by_id(self, enrollment_id: int) -> dict[str, Any] | None:
        for enrollment in self._read_items():
            if int(enrollment.get("id") or 0) == int(enrollment_id):
                return enrollment
        return None

    def deactivate(
        self,
        enrollment_id: int,
        *,
        justification: str,
        performed_by: str | None = None,
        reassigned_to_mentor_id: int | None = None,
    ) -> dict[str, Any] | None:
        items = self._read_items()
        for index, enrollment in enumerate(items):
            if int(enrollment.get("id") or 0) != int(enrollment_id):
                continue
            enrollment["is_active"] = False
            enrollment["deactivated_at"] = _now_iso()
            enrollment["deactivated_reason"] = justification
            enrollment["deactivated_by"] = performed_by
            enrollment["reassigned_to_mentor_id"] = reassigned_to_mentor_id
            enrollment["updated_at"] = enrollment["deactivated_at"]
            enrollment["deleted_at"] = enrollment["deactivated_at"]
            items[index] = enrollment
            self._write_items(items)
            return enrollment
        return None
    def soft_delete(self, enrollment_id: int) -> bool:
        items = self._read_items()
        for enrollment in items:
            if int(enrollment.get("id") or 0) == int(enrollment_id):
                enrollment["deleted_at"] = _now_iso()
                self._write_items(items)
                return True
        return False
