from app.services.indicator_carga_service import IndicatorCargaService


class _FakeStudentRepository:
    def get_by_id(self, student_id: str):
        if student_id == "std_1":
            return {"id": "std_1", "full_name": "Aluno Radar"}
        return None


class _FakeOrganizationRepository:
    def get_by_id(self, organization_id: str):
        return {"id": organization_id, "name": "Mentoria Radar"}


class _FakeEnrollmentRepository:
    def get_active_by_student(self, student_id: str):
        if student_id != "std_1":
            return None
        return {"id": "enr_1", "student_id": "std_1", "organization_id": "org_1", "is_active": True}


class _FakeMetricRepository:
    def __init__(self) -> None:
        self.items = {
            "met_1": {"id": "met_1", "name": "Metrica 1", "pillar_id": "plr_1"},
            "met_2": {"id": "met_2", "name": "Metrica 2", "pillar_id": "plr_2"},
        }

    def get_by_id(self, metric_id: str):
        return self.items.get(metric_id)


class _FakePillarRepository:
    def __init__(self) -> None:
        self.items = {
            "plr_1": {"id": "plr_1", "name": "Compromisso", "code": "compromisso", "order_index": 1},
            "plr_2": {"id": "plr_2", "name": "Evolucao", "code": "evolucao", "order_index": 2},
        }

    def get_by_id(self, pillar_id: str):
        return self.items.get(pillar_id)


class _FakeMeasurementRepository:
    def list_by_enrollment(self, enrollment_id: str):
        return [
            {"id": "mea_1", "enrollment_id": enrollment_id, "metric_id": "met_1", "value_baseline": 50, "value_current": 60, "value_projected": 75},
            {"id": "mea_2", "enrollment_id": enrollment_id, "metric_id": "met_2", "value_baseline": 40, "value_current": 55, "value_projected": None},
        ]

    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict]):
        return rows


class _FakeCheckpointRepository:
    def list_by_enrollment(self, enrollment_id: str):
        return []

    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict]):
        return rows


def test_radar_axis_scores_with_projected_fallback_and_averages() -> None:
    service = IndicatorCargaService(
        students=_FakeStudentRepository(),
        organizations=_FakeOrganizationRepository(),
        enrollments=_FakeEnrollmentRepository(),
        metrics=_FakeMetricRepository(),
        measurements=_FakeMeasurementRepository(),
        checkpoints=_FakeCheckpointRepository(),
        pillars=_FakePillarRepository(),
    )

    radar = service.get_student_radar(student_id="std_1")

    assert "axisScores" in radar
    assert len(radar["axisScores"]) == 2
    first = radar["axisScores"][0]
    assert {"axisKey", "axisLabel", "axisSub", "baseline", "current", "projected", "insight"}.issubset(first.keys())
    assert isinstance(first["insight"], str)
    assert first["insight"] != ""

    second = radar["axisScores"][1]
    assert second["axisKey"] == "evolucao"
    assert second["projected"] == second["current"]
    assert isinstance(second["insight"], str)
    assert second["insight"] != ""

    assert radar["avgBaseline"] == 45.0
    assert radar["avgCurrent"] == 57.5
    assert radar["avgProjected"] == 65.0
