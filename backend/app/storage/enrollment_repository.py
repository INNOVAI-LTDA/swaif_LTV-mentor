from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
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
        self._file_path = Path(file_path) if file_path is not None else default_enrollment_store_path()
        self._namespace = str(self._file_path.resolve())
        with self._memory_lock:
            if self._namespace not in self._memory_stores:
                self._memory_stores[self._namespace] = []
        self._bootstrap_from_disk_if_needed()

    @staticmethod
    def _normalize_prefixed_id(value: Any, prefix: str) -> str:
        raw = str(value or "").strip()
        expected = f"{prefix}_"
        if raw.startswith(expected):
            return raw[len(expected):]
        return raw

    @classmethod
    def _ids_match(cls, left: Any, right: Any, prefix: str) -> bool:
        return cls._normalize_prefixed_id(left, prefix) == cls._normalize_prefixed_id(right, prefix)

    def _bootstrap_from_disk_if_needed(self) -> None:
        with self._memory_lock:
            if self._memory_stores.get(self._namespace):
                return

        if not self._file_path.exists():
            return

        try:
            payload = json.loads(self._file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        items = payload.get("items", []) if isinstance(payload, dict) else []
        seeded = [dict(item) for item in items if isinstance(item, dict) and item.get("deleted_at") is None]

        with self._memory_lock:
            if not self._memory_stores.get(self._namespace):
                self._memory_stores[self._namespace] = seeded

    def _memory_items(self) -> list[dict[str, Any]]:
        with self._memory_lock:
            return self._memory_stores.get(self._namespace, [])

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        with self._memory_lock:
            self._memory_stores[self._namespace] = [dict(item) for item in items]

    def _read_items(self) -> list[dict[str, Any]]:
        self._bootstrap_from_disk_if_needed()
        return [dict(item) for item in self._memory_items() if isinstance(item, dict) and item.get("deleted_at") is None]

    def list_enrollments(self) -> list[dict[str, Any]]:
        return self._read_items()

    def create(
        self,
        *,
        student_id: str | int,
        organization_id: str | int,
        mentor_id: str | int | None = None,
        progress_score: float,
        engagement_score: float,
        urgency_status: str = "normal",
        day: int = 0,
        total_days: int = 0,
        days_left: int = 0,
        ltv_cents: int = 0,
        link_reason: str | None = None,
        source_enrollment_id: str | int | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        items = self._read_items()
        now = _now_iso()

        numeric_ids: list[int] = []
        for enrollment in items:
            raw_id = str(enrollment.get("id") or "").strip()
            if raw_id.isdigit():
                numeric_ids.append(int(raw_id))
            elif raw_id.startswith("enr_") and raw_id[4:].isdigit():
                numeric_ids.append(int(raw_id[4:]))
        new_id = max(numeric_ids + [0]) + 1

        enrollment = {
            "id": f"enr_{new_id}",
            "student_id": str(student_id),
            "organization_id": str(organization_id),
            "mentor_id": str(mentor_id) if mentor_id is not None else None,
            "progress_score": float(progress_score),
            "engagement_score": float(engagement_score),
            "urgency_status": urgency_status,
            "day": int(day),
            "total_days": int(total_days),
            "days_left": int(days_left),
            "ltv_cents": int(ltv_cents),
            "link_reason": link_reason,
            "source_enrollment_id": str(source_enrollment_id) if source_enrollment_id is not None else None,
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

    def list_by_organization(self, organization_id: str | int) -> list[dict[str, Any]]:
        return [
            enrollment
            for enrollment in self._read_items()
            if self._ids_match(enrollment.get("organization_id"), organization_id, "org")
        ]

    def list_by_mentor(self, mentor_id: str | int) -> list[dict[str, Any]]:
        return [
            enrollment
            for enrollment in self._read_items()
            if self._ids_match(enrollment.get("mentor_id"), mentor_id, "mtr")
        ]

    def backfill_active_mentor_ids(self, mentor_id_by_organization: dict[str, str]) -> dict[str, int]:
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

    def list_by_student(self, student_id: str | int) -> list[dict[str, Any]]:
        return [
            enrollment
            for enrollment in self._read_items()
            if self._ids_match(enrollment.get("student_id"), student_id, "std")
        ]

    def get_active_by_student(self, student_id: str | int) -> dict[str, Any] | None:
        for enrollment in self._read_items():
            if self._ids_match(enrollment.get("student_id"), student_id, "std") and bool(enrollment.get("is_active", True)):
                return enrollment
        return None

    def get_by_id(self, enrollment_id: str | int) -> dict[str, Any] | None:
        for enrollment in self._read_items():
            candidate = str(enrollment.get("id") or "").strip()
            target = str(enrollment_id).strip()
            if candidate == target:
                return enrollment
            if candidate.startswith("enr_") and candidate[4:] == target:
                return enrollment
            if target.startswith("enr_") and target[4:] == candidate:
                return enrollment
        return None

    def deactivate(
        self,
        enrollment_id: str | int,
        *,
        justification: str,
        performed_by: str | None = None,
        reassigned_to_mentor_id: str | int | None = None,
    ) -> dict[str, Any] | None:
        items = self._read_items()
        for index, enrollment in enumerate(items):
            target = self.get_by_id(enrollment_id)
            if target is None:
                break
            if str(enrollment.get("id") or "") != str(target.get("id") or ""):
                continue
            enrollment["is_active"] = False
            enrollment["deactivated_at"] = _now_iso()
            enrollment["deactivated_reason"] = justification
            enrollment["deactivated_by"] = performed_by
            enrollment["reassigned_to_mentor_id"] = (
                str(reassigned_to_mentor_id) if reassigned_to_mentor_id is not None else None
            )
            enrollment["updated_at"] = enrollment["deactivated_at"]
            enrollment["deleted_at"] = enrollment["deactivated_at"]
            items[index] = enrollment
            self._write_items(items)
            return enrollment
        return None

    def soft_delete(self, enrollment_id: str | int) -> bool:
        items = self._read_items()
        target = self.get_by_id(enrollment_id)
        if target is None:
            return False
        for enrollment in items:
            if str(enrollment.get("id") or "") == str(target.get("id") or ""):
                enrollment["deleted_at"] = _now_iso()
                self._write_items(items)
                return True
        return False
