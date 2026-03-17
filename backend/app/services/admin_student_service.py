from __future__ import annotations

from typing import Any

from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.mentor_repository import MentorRepository
from app.storage.organization_repository import OrganizationRepository
from app.storage.student_repository import StudentRepository


class EntityNotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


class ConsistencyError(Exception):
    pass


class AdminStudentService:
    def __init__(
        self,
        organizations: OrganizationRepository,
        mentors: MentorRepository,
        students: StudentRepository,
        enrollments: EnrollmentRepository,
    ) -> None:
        self._organizations = organizations
        self._mentors = mentors
        self._students = students
        self._enrollments = enrollments

    def _get_active_product(self, product_id: str) -> dict[str, Any]:
        product = self._organizations.get_by_id(product_id)
        if not product or not bool(product.get("is_active", True)):
            raise EntityNotFoundError("product not found")
        return product

    def _get_active_mentor(self, mentor_id: str) -> dict[str, Any]:
        mentor = self._mentors.get_by_id(mentor_id)
        if not mentor or not bool(mentor.get("is_active", True)):
            raise EntityNotFoundError("mentor not found")
        return mentor

    def list_students_by_product(self, product_id: str) -> list[dict[str, Any]]:
        self._get_active_product(product_id)
        items = [self._build_student_row(enrollment) for enrollment in self._enrollments.list_by_organization(product_id)]
        return sorted(
            [item for item in items if item is not None],
            key=lambda item: (str(item.get("full_name") or "").lower(), str(item.get("id") or "")),
        )

    def list_students_by_mentor(self, mentor_id: str) -> list[dict[str, Any]]:
        mentor = self._get_active_mentor(mentor_id)
        items = [self._build_student_row(enrollment) for enrollment in self._list_enrollments_for_mentor(mentor)]
        return sorted(
            [item for item in items if item is not None],
            key=lambda item: (str(item.get("full_name") or "").lower(), str(item.get("id") or "")),
        )

    def create_student(
        self,
        *,
        mentor_id: str,
        full_name: str,
        cpf: str,
        email: str | None = None,
        phone: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        mentor = self._get_active_mentor(mentor_id)
        product_id = str(mentor.get("organization_id") or "")
        if not product_id:
            raise ConsistencyError("mentor not linked to product")

        self._get_active_product(product_id)
        normalized_name = full_name.strip()
        normalized_cpf = "".join(char for char in cpf if char.isdigit())
        if not normalized_name or not normalized_cpf:
            raise ValidationError("full_name and cpf are required")

        student = self._students.create(
            full_name=normalized_name,
            cpf=normalized_cpf,
            email=email.strip() if email else None,
            phone=phone,
            notes=notes,
        )
        enrollment = self._enrollments.create(
            student_id=str(student["id"]),
            organization_id=product_id,
            mentor_id=mentor_id,
            progress_score=0,
            engagement_score=0,
            urgency_status="normal",
            day=0,
            total_days=0,
            days_left=0,
            ltv_cents=0,
        )
        return {**student, "mentor_id": mentor_id, "organization_id": product_id, "enrollment_id": enrollment["id"]}

    def _build_student_row(self, enrollment: dict[str, Any]) -> dict[str, Any] | None:
        if not bool(enrollment.get("is_active", True)):
            return None
        student = self._students.get_by_id(str(enrollment.get("student_id")))
        if not student or not bool(student.get("is_active", True)):
            return None
        return {
            **student,
            "mentor_id": enrollment.get("mentor_id"),
            "organization_id": enrollment.get("organization_id"),
            "enrollment_id": enrollment.get("id"),
        }

    def _list_enrollments_for_mentor(self, mentor: dict[str, Any]) -> list[dict[str, Any]]:
        mentor_id = str(mentor.get("id") or "")
        organization_id = str(mentor.get("organization_id") or "")
        enrollments = list(self._enrollments.list_by_mentor(mentor_id))
        if not mentor_id or not organization_id:
            return enrollments

        # Legacy seeds may have enrollments created before mentor_id became mandatory.
        product = self._organizations.get_by_id(organization_id)
        if not product or str(product.get("mentor_id") or "") != mentor_id:
            return enrollments

        for enrollment in self._enrollments.list_by_organization(organization_id):
            if str(enrollment.get("mentor_id") or "").strip():
                continue
            if any(str(existing.get("id") or "") == str(enrollment.get("id") or "") for existing in enrollments):
                continue
            enrollments.append(enrollment)
        return enrollments
