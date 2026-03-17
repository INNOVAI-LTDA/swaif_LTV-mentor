from app.services.indicator_carga_service import EntityNotFoundError, IndicatorCargaService


class _FakeStudentRepository:
    def __init__(self) -> None:
        self.items = {"std_1": {"id": "std_1", "full_name": "Aluno Um", "initials": "AU", "email": None, "status": "active", "is_active": True}}

    def get_by_id(self, student_id: str):
        return self.items.get(student_id)


class _FakeOrganizationRepository:
    def __init__(self) -> None:
        self.items = {"org_1": {"id": "org_1", "name": "Mentoria Prime"}}

    def get_by_id(self, organization_id: str):
        return self.items.get(organization_id)


class _FakeEnrollmentRepository:
    def __init__(self) -> None:
        self.item = {
            "id": "enr_1",
            "student_id": "std_1",
            "organization_id": "org_1",
            "day": 12,
            "total_days": 90,
            "days_left": 78,
            "urgency_status": "watch",
            "engagement_score": 0.7,
        }

    def get_active_by_student(self, student_id: str):
        if student_id == "std_1":
            return self.item
        return None


class _FakeMetricRepository:
    def __init__(self) -> None:
        self.items = {
            "met_1": {"id": "met_1", "name": "Frequencia", "unit": "%"},
            "met_2": {"id": "met_2", "name": "Consistencia", "unit": "pts"},
        }

    def get_by_id(self, metric_id: str):
        return self.items.get(metric_id)


class _FakeMeasurementRepository:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict]):
        self.items = [{"id": f"mea_{idx+1}", "enrollment_id": enrollment_id, **row} for idx, row in enumerate(rows)]
        return self.items

    def list_by_enrollment(self, enrollment_id: str):
        return [item for item in self.items if item["enrollment_id"] == enrollment_id]


class _FakeCheckpointRepository:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict]):
        self.items = [{"id": f"chk_{idx+1}", "enrollment_id": enrollment_id, **row} for idx, row in enumerate(rows)]
        return self.items

    def list_by_enrollment(self, enrollment_id: str):
        return [item for item in self.items if item["enrollment_id"] == enrollment_id]


def test_load_initial_indicators_and_read_student_detail() -> None:
    service = IndicatorCargaService(
        students=_FakeStudentRepository(),
        organizations=_FakeOrganizationRepository(),
        enrollments=_FakeEnrollmentRepository(),
        metrics=_FakeMetricRepository(),
        measurements=_FakeMeasurementRepository(),
        checkpoints=_FakeCheckpointRepository(),
    )

    result = service.load_initial_indicators(
        student_id="std_1",
        metric_values=[
            {"metric_id": "met_1", "value_baseline": 60, "value_current": 72, "value_projected": 80, "improving_trend": True},
            {"metric_id": "met_2", "value_baseline": 4, "value_current": 5},
        ],
        checkpoints=[
            {"week": 1, "status": "green", "label": "Aderencia inicial"},
            {"week": 2, "status": "yellow", "label": "Oscilacao"},
        ],
    )
    assert result["measurement_count"] == 2
    assert result["checkpoint_count"] == 2

    detail = service.get_student_detail(student_id="std_1")
    assert detail["id"] == "std_1"
    assert detail["programName"] == "Mentoria Prime"
    assert len(detail["metricValues"]) == 2
    assert detail["metricValues"][0]["metricLabel"] == "Frequencia"
    assert len(detail["checkpoints"]) == 2
    assert detail["checkpoints"][0]["status"] == "green"


def test_rejects_indicator_not_registered() -> None:
    service = IndicatorCargaService(
        students=_FakeStudentRepository(),
        organizations=_FakeOrganizationRepository(),
        enrollments=_FakeEnrollmentRepository(),
        metrics=_FakeMetricRepository(),
        measurements=_FakeMeasurementRepository(),
        checkpoints=_FakeCheckpointRepository(),
    )

    try:
        service.load_initial_indicators(
            student_id="std_1",
            metric_values=[{"metric_id": "met_missing", "value_baseline": 1, "value_current": 2}],
            checkpoints=[],
        )
        assert False, "expected EntityNotFoundError"
    except EntityNotFoundError:
        assert True
