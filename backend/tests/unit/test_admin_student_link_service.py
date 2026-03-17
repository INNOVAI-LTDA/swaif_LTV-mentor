from app.services.admin_student_link_service import AdminStudentLinkService, ConsistencyError, EntityNotFoundError, ValidationError


class _FakeOrganizationRepository:
    def __init__(self) -> None:
        self.items = {
            "org_1": {"id": "org_1", "name": "Produto A", "is_active": True},
            "org_2": {"id": "org_2", "name": "Produto B", "is_active": True},
        }

    def get_by_id(self, product_id: str) -> dict | None:
        return self.items.get(product_id)


class _FakeMentorRepository:
    def __init__(self) -> None:
        self.items = {
            "mtr_1": {"id": "mtr_1", "full_name": "Ana Mentora", "organization_id": "org_1", "is_active": True},
            "mtr_2": {"id": "mtr_2", "full_name": "Bea Mentora", "organization_id": "org_1", "is_active": True},
            "mtr_3": {"id": "mtr_3", "full_name": "Caio Mentor", "organization_id": "org_2", "is_active": True},
        }

    def get_by_id(self, mentor_id: str) -> dict | None:
        return self.items.get(mentor_id)


class _FakeStudentRepository:
    def __init__(self) -> None:
        self.items = {
            "std_1": {"id": "std_1", "full_name": "Aluno Teste", "is_active": True},
        }

    def get_by_id(self, student_id: str) -> dict | None:
        return self.items.get(student_id)


class _FakeEnrollmentRepository:
    def __init__(self) -> None:
        self.items = [
            {
                "id": "enr_1",
                "student_id": "std_1",
                "organization_id": "org_1",
                "mentor_id": "mtr_1",
                "progress_score": 0.4,
                "engagement_score": 0.6,
                "urgency_status": "watch",
                "day": 10,
                "total_days": 90,
                "days_left": 80,
                "ltv_cents": 1000,
                "is_active": True,
            }
        ]

    def get_active_by_student(self, student_id: str) -> dict | None:
        for item in self.items:
            if item["student_id"] == student_id and item["is_active"]:
                return item
        return None

    def deactivate(self, enrollment_id: str, **payload) -> dict | None:
        for item in self.items:
            if item["id"] == enrollment_id:
                item["is_active"] = False
                item["deactivated_reason"] = payload["justification"]
                item["reassigned_to_mentor_id"] = payload.get("reassigned_to_mentor_id")
                return item
        return None

    def create(self, **payload) -> dict:
        item = {"id": f"enr_{len(self.items) + 1}", "is_active": True, **payload}
        self.items.append(item)
        return item


def test_service_reassigns_student_and_preserves_history() -> None:
    enrollments = _FakeEnrollmentRepository()
    service = AdminStudentLinkService(_FakeOrganizationRepository(), _FakeMentorRepository(), _FakeStudentRepository(), enrollments)

    reassigned = service.reassign_student(
        student_id="std_1",
        target_mentor_id="mtr_2",
        justificativa="Redistribuicao operacional",
        performed_by="admin@swaif.local",
    )

    assert reassigned["mentor_id"] == "mtr_2"
    assert enrollments.items[0]["is_active"] is False
    assert enrollments.items[0]["reassigned_to_mentor_id"] == "mtr_2"
    assert enrollments.items[1]["source_enrollment_id"] == "enr_1"


def test_service_unlinks_student_logically() -> None:
    enrollments = _FakeEnrollmentRepository()
    service = AdminStudentLinkService(_FakeOrganizationRepository(), _FakeMentorRepository(), _FakeStudentRepository(), enrollments)

    unlinked = service.unlink_student(student_id="std_1", justificativa="Aluno pausado")

    assert unlinked["is_active"] is False
    assert unlinked["deactivated_reason"] == "Aluno pausado"


def test_service_requires_justification() -> None:
    service = AdminStudentLinkService(_FakeOrganizationRepository(), _FakeMentorRepository(), _FakeStudentRepository(), _FakeEnrollmentRepository())

    try:
        service.unlink_student(student_id="std_1", justificativa=" ")
    except ValidationError as exc:
        assert str(exc) == "justification is required"
    else:
        raise AssertionError("ValidationError was expected")


def test_service_blocks_cross_product_reassignment() -> None:
    service = AdminStudentLinkService(_FakeOrganizationRepository(), _FakeMentorRepository(), _FakeStudentRepository(), _FakeEnrollmentRepository())

    try:
        service.reassign_student(student_id="std_1", target_mentor_id="mtr_3", justificativa="Mover")
    except ConsistencyError as exc:
        assert str(exc) == "mentor product mismatch"
    else:
        raise AssertionError("ConsistencyError was expected")


def test_service_requires_existing_active_enrollment() -> None:
    enrollments = _FakeEnrollmentRepository()
    enrollments.items[0]["is_active"] = False
    service = AdminStudentLinkService(_FakeOrganizationRepository(), _FakeMentorRepository(), _FakeStudentRepository(), enrollments)

    try:
        service.unlink_student(student_id="std_1", justificativa="Mover")
    except EntityNotFoundError as exc:
        assert str(exc) == "active enrollment not found"
    else:
        raise AssertionError("EntityNotFoundError was expected")
