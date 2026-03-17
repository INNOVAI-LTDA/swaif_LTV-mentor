from __future__ import annotations

from typing import Any

from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.organization_repository import OrganizationRepository
from app.storage.student_repository import StudentRepository


class EntityNotFoundError(Exception):
    pass


class ConsistencyError(Exception):
    pass


class StudentVinculoService:
    def __init__(
        self,
        organizations: OrganizationRepository,
        students: StudentRepository,
        enrollments: EnrollmentRepository,
    ) -> None:
        self._organizations = organizations
        self._students = students
        self._enrollments = enrollments

    def create_student(self, *, full_name: str, initials: str | None = None, email: str | None = None) -> dict[str, Any]:
        return self._students.create(full_name=full_name, initials=initials, email=email)

    def link_student_to_organization(
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
    ) -> dict[str, Any]:
        organization = self._organizations.get_by_id(organization_id)
        if not organization:
            raise EntityNotFoundError("organization not found")

        student = self._students.get_by_id(student_id)
        if not student:
            raise EntityNotFoundError("student not found")

        if not (0 <= float(progress_score) <= 1):
            raise ConsistencyError("progress score must be between 0 and 1")
        if not (0 <= float(engagement_score) <= 1):
            raise ConsistencyError("engagement score must be between 0 and 1")

        if int(day) < 0 or int(total_days) < 0 or int(days_left) < 0:
            raise ConsistencyError("timeline values must be non-negative")
        if int(total_days) > 0 and int(day) > int(total_days):
            raise ConsistencyError("day cannot be greater than total_days")

        return self._enrollments.create(
            student_id=student_id,
            organization_id=organization_id,
            mentor_id=mentor_id,
            progress_score=progress_score,
            engagement_score=engagement_score,
            urgency_status=urgency_status,
            day=day,
            total_days=total_days,
            days_left=days_left,
            ltv_cents=ltv_cents,
        )

    def list_students_by_organization(self, organization_id: str) -> list[dict[str, Any]]:
        organization = self._organizations.get_by_id(organization_id)
        if not organization:
            raise EntityNotFoundError("organization not found")

        linked_students: list[dict[str, Any]] = []
        for enrollment in self._enrollments.list_by_organization(organization_id):
            student_id = str(enrollment.get("student_id"))
            student = self._students.get_by_id(student_id)
            if not student:
                continue
            linked_students.append({**enrollment, "student": student})
        return linked_students
