from app.services.indicator_carga_service import IndicatorCargaService


class _FakeStudentRepository:
    def __init__(self) -> None:
        self.items = {
            "std_1": {"id": "std_1", "full_name": "Aluno Um"},
            "std_2": {"id": "std_2", "full_name": "Aluno Dois"},
        }

    def get_by_id(self, student_id: str):
        return self.items.get(student_id)

    def list_students(self):
        return list(self.items.values())


class _FakeOrganizationRepository:
    def __init__(self) -> None:
        self.items = {"org_1": {"id": "org_1", "name": "Mentoria Prime"}}

    def get_by_id(self, organization_id: str):
        return self.items.get(organization_id)


class _FakeEnrollmentRepository:
    def list_enrollments(self):
        return [
            {
                "id": "enr_1",
                "student_id": "std_1",
                "organization_id": "org_1",
                "day": 45,
                "total_days": 90,
                "days_left": 45,
                "engagement_score": 0.0,
                "progress_score": 0.2,
                "is_active": True,
            },
            {
                "id": "enr_2",
                "student_id": "std_2",
                "organization_id": "org_1",
                "day": 0,
                "total_days": 0,
                "days_left": 80,
                "engagement_score": 0.7,
                "progress_score": 0.4,
                "is_active": True,
            },
        ]

    def get_active_by_student(self, student_id: str):
        for item in self.list_enrollments():
            if item["student_id"] == student_id:
                return item
        return None


class _FakeMetricRepository:
    def get_by_id(self, metric_id: str):
        return {"id": metric_id, "name": "Metrica", "unit": "%", "metadata": {}}


class _FakeMeasurementRepository:
    def list_by_enrollment(self, enrollment_id: str):
        return []

    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict]):
        return rows


class _FakeCheckpointRepository:
    def list_by_enrollment(self, enrollment_id: str):
        return []

    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict]):
        return rows


def test_command_center_derivations_include_edge_cases() -> None:
    service = IndicatorCargaService(
        students=_FakeStudentRepository(),
        organizations=_FakeOrganizationRepository(),
        enrollments=_FakeEnrollmentRepository(),
        metrics=_FakeMetricRepository(),
        measurements=_FakeMeasurementRepository(),
        checkpoints=_FakeCheckpointRepository(),
    )

    items = service.list_command_center_students()
    by_id = {item["id"]: item for item in items}

    first = by_id["std_1"]
    assert first["daysLeft"] == 45
    assert first["d45"] is True
    assert first["engagement"] == 0.0
    assert first["urgency"] in {"critical", "rescue"}
    assert first["progress"] == 0.5

    second = by_id["std_2"]
    assert second["totalDays"] == 0
    assert second["progress"] == 0.4
    assert 0 <= second["hormoziScore"] <= 100
