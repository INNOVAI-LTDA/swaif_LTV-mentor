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
