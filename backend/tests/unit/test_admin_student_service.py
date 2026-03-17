from app.services.admin_student_service import (
    AdminStudentService,
    ConsistencyError,
    EntityNotFoundError,
    ValidationError,
)


class _FakeOrganizationRepository:
    def __init__(self) -> None:
        self.items = {
            "org_1": {
                "id": "org_1",
                "name": "Acelerador Medico Premium",
                "mentor_id": "mtr_1",
                "is_active": True,
            }
        }

    def get_by_id(self, product_id: str) -> dict | None:
        return self.items.get(product_id)


class _FakeMentorRepository:
    def __init__(self) -> None:
        self.items = {
            "mtr_1": {
                "id": "mtr_1",
                "full_name": "Ana Mentora",
                "organization_id": "org_1",
                "is_active": True,
            }
        }

    def get_by_id(self, mentor_id: str) -> dict | None:
        return self.items.get(mentor_id)


class _FakeStudentRepository:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def create(self, **payload) -> dict:
        if any(item.get("cpf") == payload.get("cpf") for item in self.items if payload.get("cpf")):
            raise ValueError("student cpf already exists")
        item = {
            "id": f"std_{len(self.items) + 1}",
            "initials": "AT",
            "status": "active",
            "is_active": True,
            "created_at": "2026-03-15T00:00:00Z",
            "updated_at": "2026-03-15T00:00:00Z",
            **payload,
        }
        self.items.append(item)
        return item

    def get_by_id(self, student_id: str) -> dict | None:
        return next((item for item in self.items if item["id"] == student_id), None)


class _FakeEnrollmentRepository:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def create(self, **payload) -> dict:
        item = {"id": f"enr_{len(self.items) + 1}", "is_active": True, **payload}
        self.items.append(item)
        return item

    def list_by_organization(self, organization_id: str) -> list[dict]:
        return [item for item in self.items if item["organization_id"] == organization_id]

    def list_by_mentor(self, mentor_id: str) -> list[dict]:
        return [item for item in self.items if item["mentor_id"] == mentor_id]


def test_service_creates_student_linked_to_mentor_and_product() -> None:
    service = AdminStudentService(
        organizations=_FakeOrganizationRepository(),
        mentors=_FakeMentorRepository(),
        students=_FakeStudentRepository(),
        enrollments=_FakeEnrollmentRepository(),
    )

    created = service.create_student(
        mentor_id="mtr_1",
        full_name="Aluno Teste",
        cpf="123.456.789-00",
        email="aluno@swaif.local",
    )

    assert created["mentor_id"] == "mtr_1"
    assert created["organization_id"] == "org_1"
    assert created["cpf"] == "12345678900"


def test_service_rejects_blank_required_fields() -> None:
    service = AdminStudentService(
        organizations=_FakeOrganizationRepository(),
        mentors=_FakeMentorRepository(),
        students=_FakeStudentRepository(),
        enrollments=_FakeEnrollmentRepository(),
    )

    try:
        service.create_student(mentor_id="mtr_1", full_name=" ", cpf=" ")
    except ValidationError as exc:
        assert str(exc) == "full_name and cpf are required"
    else:
        raise AssertionError("ValidationError was expected")


def test_service_requires_existing_mentor() -> None:
    service = AdminStudentService(
        organizations=_FakeOrganizationRepository(),
        mentors=_FakeMentorRepository(),
        students=_FakeStudentRepository(),
        enrollments=_FakeEnrollmentRepository(),
    )

    try:
        service.list_students_by_mentor("mtr_missing")
    except EntityNotFoundError as exc:
        assert str(exc) == "mentor not found"
    else:
        raise AssertionError("EntityNotFoundError was expected")


def test_service_requires_mentor_linked_to_product() -> None:
    mentors = _FakeMentorRepository()
    mentors.items["mtr_1"]["organization_id"] = None
    service = AdminStudentService(
        organizations=_FakeOrganizationRepository(),
        mentors=mentors,
        students=_FakeStudentRepository(),
        enrollments=_FakeEnrollmentRepository(),
    )

    try:
        service.create_student(mentor_id="mtr_1", full_name="Aluno Teste", cpf="12345678900")
    except ConsistencyError as exc:
        assert str(exc) == "mentor not linked to product"
    else:
        raise AssertionError("ConsistencyError was expected")


def test_service_lists_legacy_students_without_mentor_id_for_primary_mentor() -> None:
    students = _FakeStudentRepository()
    created_student = students.create(full_name="Aluno Legado", cpf="12345678900", email="legado@swaif.local")

    enrollments = _FakeEnrollmentRepository()
    enrollments.items.append(
        {
            "id": "enr_legacy",
            "student_id": created_student["id"],
            "organization_id": "org_1",
            "mentor_id": None,
            "is_active": True,
        }
    )

    service = AdminStudentService(
        organizations=_FakeOrganizationRepository(),
        mentors=_FakeMentorRepository(),
        students=students,
        enrollments=enrollments,
    )

    items = service.list_students_by_mentor("mtr_1")

    assert len(items) == 1
    assert items[0]["id"] == created_student["id"]
    assert items[0]["organization_id"] == "org_1"
    assert items[0]["enrollment_id"] == "enr_legacy"
