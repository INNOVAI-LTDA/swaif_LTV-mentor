from app.services.student_vinculo_service import ConsistencyError, EntityNotFoundError, StudentVinculoService


class _FakeOrganizationRepository:
    def __init__(self) -> None:
        self.items = {"org_1": {"id": "org_1", "name": "Mentoria 1"}}

    def get_by_id(self, organization_id: str):
        return self.items.get(organization_id)


class _FakeStudentRepository:
    def __init__(self) -> None:
        self.items: dict[str, dict] = {}
        self._seq = 0

    def create(self, *, full_name: str, initials: str | None = None, email: str | None = None):
        self._seq += 1
        student = {
            "id": f"std_{self._seq}",
            "full_name": full_name,
            "initials": initials or "ST",
            "email": email,
            "status": "active",
        }
        self.items[student["id"]] = student
        return student

    def get_by_id(self, student_id: str):
        return self.items.get(student_id)


class _FakeEnrollmentRepository:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def create(self, **kwargs):
        record = {"id": f"enr_{len(self.items) + 1}", **kwargs}
        self.items.append(record)
        return record

    def list_by_organization(self, organization_id: str):
        return [item for item in self.items if item["organization_id"] == organization_id]

    def list_by_student(self, student_id: str):
        return [item for item in self.items if item["student_id"] == student_id]

    def deactivate(self, enrollment_id: str, *, justification: str):
        for item in self.items:
            if item["id"] != enrollment_id:
                continue
            item["is_active"] = False
            item["deactivated_reason"] = justification
            return item
        return None


class _FakeProductAssignmentRepository:
    def __init__(self) -> None:
        self.upsert_calls: list[dict] = []
        self.deactivate_calls: list[dict] = []

    def upsert_from_enrollment(self, enrollment: dict) -> dict:
        self.upsert_calls.append(enrollment)
        return {"assignment_id": enrollment["id"]}

    def deactivate(self, assignment_id: str, *, justification: str):
        self.deactivate_calls.append({"assignment_id": assignment_id, "justification": justification})
        return {"id": assignment_id, "status": "inactive"}


def test_student_create_and_link_to_mentoria() -> None:
    service = StudentVinculoService(
        organizations=_FakeOrganizationRepository(),
        students=_FakeStudentRepository(),
        enrollments=_FakeEnrollmentRepository(),
    )
    student = service.create_student(full_name="Aluno Teste", initials="AT")
    enrollment = service.link_student_to_organization(
        student_id=student["id"],
        organization_id="org_1",
        progress_score=0.3,
        engagement_score=0.7,
    )

    assert enrollment["student_id"] == student["id"]
    assert enrollment["organization_id"] == "org_1"


def test_link_rejects_invalid_ranges_and_missing_org() -> None:
    service = StudentVinculoService(
        organizations=_FakeOrganizationRepository(),
        students=_FakeStudentRepository(),
        enrollments=_FakeEnrollmentRepository(),
    )
    student = service.create_student(full_name="Aluno Teste")

    try:
        service.link_student_to_organization(
            student_id=student["id"],
            organization_id="org_1",
            progress_score=1.2,
            engagement_score=0.7,
        )
        assert False, "expected ConsistencyError"
    except ConsistencyError:
        assert True

    try:
        service.link_student_to_organization(
            student_id=student["id"],
            organization_id="org_missing",
            progress_score=0.2,
            engagement_score=0.7,
        )
        assert False, "expected EntityNotFoundError"
    except EntityNotFoundError:
        assert True


def test_link_student_syncs_authoritative_product_assignment_and_deactivates_previous() -> None:
    organizations = _FakeOrganizationRepository()
    students = _FakeStudentRepository()
    enrollments = _FakeEnrollmentRepository()
    product_assignments = _FakeProductAssignmentRepository()

    service = StudentVinculoService(
        organizations=organizations,
        students=students,
        enrollments=enrollments,
        product_assignments=product_assignments,
    )

    student = service.create_student(full_name="Aluno Historico")

    first = service.link_student_to_organization(
        student_id=student["id"],
        organization_id="org_1",
        progress_score=0.2,
        engagement_score=0.4,
    )
    second = service.link_student_to_organization(
        student_id=student["id"],
        organization_id="org_1",
        progress_score=0.6,
        engagement_score=0.8,
    )

    assert first["id"] != second["id"]
    assert len(product_assignments.upsert_calls) == 2
    assert len(product_assignments.deactivate_calls) == 1
    assert product_assignments.deactivate_calls[0]["assignment_id"] == first["id"]
