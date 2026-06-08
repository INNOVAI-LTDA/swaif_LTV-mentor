from __future__ import annotations

from typing import Any

from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.contact_user_repository import ContactUserRepository
from app.storage.mentor_repository import MentorRepository
from app.storage.organization_repository import OrganizationRepository
from app.storage.product_assignment_repository import ProductAssignmentRepository
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
        mentors: MentorRepository | None,
        students: StudentRepository,
        enrollments: EnrollmentRepository,
        contacts: ContactUserRepository,
        product_assignments: ProductAssignmentRepository | None = None,
    ) -> None:
        self._organizations = organizations
        self._mentors = mentors
        self._students = students
        self._enrollments = enrollments
        self._contacts = contacts
        self._product_assignments = product_assignments

    @staticmethod
    def _normalize_prefixed_id(value: Any, prefix: str) -> str:
        raw = str(value or "").strip()
        expected = f"{prefix}_"
        if raw.startswith(expected):
            return raw[len(expected):]
        return raw

    def _get_active_product(self, product_id: str) -> dict[str, Any]:
        product = self._organizations.get_by_id(product_id)
        if not product or not bool(product.get("is_active", True)):
            raise EntityNotFoundError("product not found")
        return product

    def _get_active_mentor(self, mentor_id: str) -> dict[str, Any]:
        mentor = None
        if self._mentors is not None:
            try:
                mentor = self._mentors.get_by_id(mentor_id)
            except RuntimeError:
                mentor = None

        if mentor and bool(mentor.get("is_active", True)):
            return mentor

        for contact in self._contacts.list_items():
            if str(contact.get("id") or "") != str(mentor_id):
                continue
            role = str(contact.get("role") or "").strip().lower()
            if role not in {"mentor", "provider"}:
                continue
            if not bool(contact.get("is_active", True)):
                continue
            organization_id = str(contact.get("organization_id") or "")
            canonical_mentor_id = ""
            if organization_id:
                product = self._organizations.get_by_id(organization_id)
                if product:
                    canonical_mentor_id = str(product.get("mentor_id") or "")
            return {
                "id": canonical_mentor_id or str(contact.get("id") or ""),
                "full_name": str(contact.get("full_name") or ""),
                "email": str(contact.get("email") or ""),
                "organization_id": organization_id,
                "is_active": bool(contact.get("is_active", True)),
            }

        # Supabase snapshots may expose mentor relationships only through products.
        for product in self._organizations.list_organizations():
            if not bool(product.get("is_active", True)):
                continue
            if str(product.get("mentor_id") or "") != str(mentor_id):
                continue
            return {
                "id": str(product.get("mentor_id") or ""),
                "full_name": "",
                "email": "",
                "organization_id": str(product.get("id") or ""),
                "is_active": True,
            }

        raise EntityNotFoundError("mentor not found")

    def list_students_by_product(self, product_id: str) -> list[dict[str, Any]]:
        self._get_active_product(product_id)
        students_by_id = self._build_active_students_index()
        items = [
            self._build_student_row(enrollment, students_by_id)
            for enrollment in self._enrollments.list_by_organization(product_id)
        ]
        return sorted(
            [item for item in items if item is not None],
            key=lambda item: (str(item.get("full_name") or "").lower(), str(item.get("id") or "")),
        )

    def list_students_by_mentor(self, mentor_id: str) -> list[dict[str, Any]]:
        mentor = self._get_active_mentor(mentor_id)
        students_by_id = self._build_active_students_index()
        items = [
            self._build_student_row(enrollment, students_by_id)
            for enrollment in self._list_enrollments_for_mentor(mentor)
        ]
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
        if self._product_assignments is not None:
            self._product_assignments.upsert_from_enrollment(enrollment)
        try:
            self._contacts.create(
                id=str(student["id"]),
                full_name=str(student.get("full_name") or normalized_name),
                email=str(student.get("email") or f"{student['id']}@unknown.local"),
                role="aluno",
                is_active=True,
                cpf=normalized_cpf,
                phone=phone,
                organization_id=product_id,
                notes=notes,
            )
        except ValueError:
            pass
        return {**student, "mentor_id": mentor_id, "organization_id": product_id, "enrollment_id": enrollment["id"]}

    def _build_active_students_index(self) -> dict[str, dict[str, Any]]:
        index: dict[str, dict[str, Any]] = {}
        for student in self._students.list_students():
            if not bool(student.get("is_active", True)):
                continue
            raw_id = str(student.get("id") or "")
            if not raw_id:
                continue
            index[raw_id] = student
            normalized = self._normalize_prefixed_id(raw_id, "std")
            if normalized:
                index[normalized] = student
        return index

    def _build_student_row(
        self,
        enrollment: dict[str, Any],
        students_by_id: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        if not bool(enrollment.get("is_active", True)):
            return None
        student_id = str(enrollment.get("student_id") or "")
        student = None
        if students_by_id is not None:
            student = students_by_id.get(student_id) or students_by_id.get(self._normalize_prefixed_id(student_id, "std"))
        if student is None:
            student = self._students.get_by_id(student_id)
            if student is None:
                student = self._students.get_by_id(self._normalize_prefixed_id(student_id, "std"))
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

        product = self._organizations.get_by_id(organization_id)
        if not product:
            return enrollments

        canonical_mentor_id = str(product.get("mentor_id") or "")
        if canonical_mentor_id and canonical_mentor_id != mentor_id:
            for enrollment in self._enrollments.list_by_mentor(canonical_mentor_id):
                if any(str(existing.get("id") or "") == str(enrollment.get("id") or "") for existing in enrollments):
                    continue
                enrollments.append(enrollment)

        if canonical_mentor_id not in {"", mentor_id}:
            return enrollments

        # Legacy seeds may have enrollments created before mentor_id became mandatory.

        for enrollment in self._enrollments.list_by_organization(organization_id):
            if str(enrollment.get("mentor_id") or "").strip():
                continue
            if any(str(existing.get("id") or "") == str(enrollment.get("id") or "") for existing in enrollments):
                continue
            enrollments.append(enrollment)
        return enrollments
