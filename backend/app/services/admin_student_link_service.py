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


class AdminStudentLinkService:
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

    def _get_active_student(self, student_id: str) -> dict[str, Any]:
        student = self._students.get_by_id(student_id)
        if not student or not bool(student.get("is_active", True)):
            raise EntityNotFoundError("student not found")
        return student

    def _get_active_mentor(self, mentor_id: str) -> dict[str, Any]:
        mentor = self._mentors.get_by_id(mentor_id)
        if not mentor or not bool(mentor.get("is_active", True)):
            raise EntityNotFoundError("mentor not found")
        return mentor

    def _get_active_product(self, product_id: str) -> dict[str, Any]:
        product = self._organizations.get_by_id(product_id)
        if not product or not bool(product.get("is_active", True)):
            raise EntityNotFoundError("product not found")
        return product

    def _get_active_enrollment(self, student_id: str) -> dict[str, Any]:
        enrollment = self._enrollments.get_active_by_student(student_id)
        if not enrollment:
            raise EntityNotFoundError("active enrollment not found")
        return enrollment

    def reassign_student(
        self,
        *,
        student_id: str,
        target_mentor_id: str,
        justificativa: str,
        performed_by: str | None = None,
    ) -> dict[str, Any]:
        student = self._get_active_student(student_id)
        current_enrollment = self._get_active_enrollment(student_id)
        target_mentor = self._get_active_mentor(target_mentor_id)

        justification = justificativa.strip()
        if not justification:
            raise ValidationError("justification is required")

        current_mentor_id = str(current_enrollment.get("mentor_id") or "")
        if current_mentor_id == target_mentor_id:
            raise ConsistencyError("student already linked to mentor")

        current_product_id = str(current_enrollment.get("organization_id") or "")
        target_product_id = str(target_mentor.get("organization_id") or "")
        if not current_product_id or not target_product_id:
            raise ConsistencyError("mentor not linked to product")
        if current_product_id != target_product_id:
            raise ConsistencyError("mentor product mismatch")

        self._get_active_product(current_product_id)
        self._enrollments.deactivate(
            str(current_enrollment.get("id")),
            justification=justification,
            performed_by=performed_by,
            reassigned_to_mentor_id=target_mentor_id,
        )
        new_enrollment = self._enrollments.create(
            student_id=student_id,
            organization_id=current_product_id,
            mentor_id=target_mentor_id,
            progress_score=float(current_enrollment.get("progress_score", 0)),
            engagement_score=float(current_enrollment.get("engagement_score", 0)),
            urgency_status=str(current_enrollment.get("urgency_status") or "normal"),
            day=int(current_enrollment.get("day", 0)),
            total_days=int(current_enrollment.get("total_days", 0)),
            days_left=int(current_enrollment.get("days_left", 0)),
            ltv_cents=int(current_enrollment.get("ltv_cents", 0)),
            link_reason=justification,
            source_enrollment_id=str(current_enrollment.get("id")),
            created_by=performed_by,
        )
        return {
            **student,
            "mentor_id": target_mentor_id,
            "organization_id": current_product_id,
            "enrollment_id": new_enrollment["id"],
        }

    def unlink_student(
        self,
        *,
        student_id: str,
        justificativa: str,
        performed_by: str | None = None,
    ) -> dict[str, Any]:
        self._get_active_student(student_id)
        current_enrollment = self._get_active_enrollment(student_id)
        justification = justificativa.strip()
        if not justification:
            raise ValidationError("justification is required")

        deactivated = self._enrollments.deactivate(
            str(current_enrollment.get("id")),
            justification=justification,
            performed_by=performed_by,
            reassigned_to_mentor_id=None,
        )
        if not deactivated:
            raise EntityNotFoundError("active enrollment not found")
        return deactivated
