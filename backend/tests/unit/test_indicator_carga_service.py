from app.services.indicator_carga_service import EntityNotFoundError, IndicatorCargaService
from app.services.indicator_carga_service import DomainNotReadyError, RuntimeDependencyError
from app.services.indicator_carga_service import JsonFallbackForbiddenError


class _FakeStudentRepository:
    def __init__(self) -> None:
        self.items = {"std_1": {"id": "std_1", "full_name": "Aluno Um", "initials": "AU", "email": None, "status": "active", "is_active": True}}

    def get_by_id(self, student_id: str):
        return self.items.get(student_id)

    def list_students(self):
        return list(self.items.values())


class _FakeOrganizationRepository:
    def __init__(self) -> None:
        self.items = {"org_1": {"id": "org_1", "name": "Mentoria Prime"}}

    def get_by_id(self, organization_id: str):
        return self.items.get(organization_id)

    def list_organizations(self):
        return list(self.items.values())


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

    def list_enrollments(self):
        return [self.item]


class _FakeMetricRepository:
    def __init__(self) -> None:
        self.items = {
            "met_1": {"id": "met_1", "name": "Frequencia", "unit": "%", "pillar_id": "plr_1"},
            "met_2": {"id": "met_2", "name": "Consistencia", "unit": "pts", "pillar_id": "plr_1"},
        }

    def get_by_id(self, metric_id: str):
        return self.items.get(metric_id)

    def list_metrics(self):
        return list(self.items.values())


class _FakeMeasurementRepository:
    runtime_backend = "postgres"

    def __init__(self) -> None:
        self.items: list[dict] = []

    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict]):
        self.items = [{"id": f"mea_{idx+1}", "enrollment_id": enrollment_id, **row} for idx, row in enumerate(rows)]
        return self.items

    def list_by_enrollment(self, enrollment_id: str):
        return [item for item in self.items if item["enrollment_id"] == enrollment_id]

    def list_measurements(self):
        return list(self.items)


class _FakeCheckpointRepository:
    runtime_backend = "postgres"

    def __init__(self) -> None:
        self.items: list[dict] = []

    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict]):
        self.items = [{"id": f"chk_{idx+1}", "enrollment_id": enrollment_id, **row} for idx, row in enumerate(rows)]
        return self.items

    def list_by_enrollment(self, enrollment_id: str):
        return [item for item in self.items if item["enrollment_id"] == enrollment_id]


class _FakePillarRepository:
    def __init__(self) -> None:
        self.items = {
            "plr_1": {"id": "plr_1", "code": "frequencia", "name": "Frequencia", "order_index": 1, "axis_sub": ""}
        }

    def list_pillars(self):
        return list(self.items.values())


class _FakeMeasurementOverallRepository:
    def list_all(self):
        return [{"enrollment_id": "enr_1", "protocol_id": "prt_1", "pillars": []}]


class _FakeProductAssignmentRepository:
    def list_assignments(self):
        return [
            {
                "id": "enr_999",
                "assignment_id": "enr_999",
                "student_id": "std_999",
                "end_user_id": "std_999",
                "organization_id": "org_1",
                "product_id": "org_1",
                "mentor_id": "mtr_2",
                "provider_id": "mtr_2",
                "is_active": True,
                "updated_at": "2026-05-20T20:29:01.552Z",
            }
        ]


class _JsonBackendMeasurementRepository(_FakeMeasurementRepository):
    runtime_backend = "json"


class _JsonBackendCheckpointRepository(_FakeCheckpointRepository):
    runtime_backend = "json"


def test_load_initial_indicators_and_read_student_detail(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://runtime-db")
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


def test_rejects_indicator_not_registered(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://runtime-db")
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


def test_load_initial_indicators_fails_without_postgres_url_in_production_like(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
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
            metric_values=[{"metric_id": "met_1", "value_baseline": 1, "value_current": 2}],
            checkpoints=[],
        )
        assert False, "expected RuntimeDependencyError"
    except RuntimeDependencyError:
        assert True


def test_load_initial_indicators_fails_without_postgres_url_in_local_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
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
            metric_values=[{"metric_id": "met_1", "value_baseline": 1, "value_current": 2}],
            checkpoints=[],
        )
        assert False, "expected RuntimeDependencyError"
    except RuntimeDependencyError:
        assert True


def test_load_initial_indicators_flags_unready_domains_in_production_like(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://runtime-db")

    class _UnknownBackendMeasurementRepository(_FakeMeasurementRepository):
        runtime_backend = "unknown"

    class _UnknownBackendCheckpointRepository(_FakeCheckpointRepository):
        runtime_backend = "unknown"

    service = IndicatorCargaService(
        students=_FakeStudentRepository(),
        organizations=_FakeOrganizationRepository(),
        enrollments=_FakeEnrollmentRepository(),
        metrics=_FakeMetricRepository(),
        measurements=_UnknownBackendMeasurementRepository(),
        checkpoints=_UnknownBackendCheckpointRepository(),
    )

    try:
        service.load_initial_indicators(
            student_id="std_1",
            metric_values=[{"metric_id": "met_1", "value_baseline": 1, "value_current": 2}],
            checkpoints=[],
        )
        assert False, "expected DomainNotReadyError"
    except DomainNotReadyError:
        assert True


def test_load_initial_indicators_forbids_json_fallback_in_production_like(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://runtime-db")
    service = IndicatorCargaService(
        students=_FakeStudentRepository(),
        organizations=_FakeOrganizationRepository(),
        enrollments=_FakeEnrollmentRepository(),
        metrics=_FakeMetricRepository(),
        measurements=_JsonBackendMeasurementRepository(),
        checkpoints=_JsonBackendCheckpointRepository(),
    )

    try:
        service.load_initial_indicators(
            student_id="std_1",
            metric_values=[{"metric_id": "met_1", "value_baseline": 1, "value_current": 2}],
            checkpoints=[],
        )
        assert False, "expected JsonFallbackForbiddenError"
    except JsonFallbackForbiddenError:
        assert True


def test_get_student_radar_falls_back_to_measurements_when_overall_has_empty_pillars(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://runtime-db")
    measurements = _FakeMeasurementRepository()
    measurements.replace_for_enrollment(
        "enr_1",
        [
            {"metric_id": "met_1", "value_baseline": 50, "value_current": 70, "value_projected": 80, "improving_trend": True},
            {"metric_id": "met_2", "value_baseline": 4, "value_current": 5, "value_projected": 6, "improving_trend": True},
        ],
    )

    service = IndicatorCargaService(
        students=_FakeStudentRepository(),
        organizations=_FakeOrganizationRepository(),
        enrollments=_FakeEnrollmentRepository(),
        metrics=_FakeMetricRepository(),
        measurements=measurements,
        checkpoints=_FakeCheckpointRepository(),
        pillars=_FakePillarRepository(),
        measurement_overalls=_FakeMeasurementOverallRepository(),
    )

    radar = service.get_student_radar(student_id="std_1")
    assert len(radar["axisScores"]) == 1
    assert radar["axisScores"][0]["axisId"] == "plr_1"
    assert radar["axisScores"][0]["current"] > 0


def test_list_command_center_students_falls_back_to_enrollments_when_assignments_are_unlinked(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://runtime-db")
    service = IndicatorCargaService(
        students=_FakeStudentRepository(),
        organizations=_FakeOrganizationRepository(),
        enrollments=_FakeEnrollmentRepository(),
        metrics=_FakeMetricRepository(),
        measurements=_FakeMeasurementRepository(),
        checkpoints=_FakeCheckpointRepository(),
        product_assignments=_FakeProductAssignmentRepository(),
    )

    payload = service.list_command_center_students()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == "std_1"


def test_list_command_center_students_prioritizes_students_with_radar_data(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://runtime-db")

    class _Students:
        def list_students(self):
            return [
                {"id": "std_no_data", "full_name": "Aluno Sem Radar", "initials": "SR", "is_active": True},
                {"id": "std_with_data", "full_name": "Aluno Com Radar", "initials": "CR", "is_active": True},
            ]

    class _Organizations:
        def list_organizations(self):
            return [{"id": "org_1", "name": "Mentoria Prime"}]

    class _Enrollments:
        def list_enrollments(self):
            return [
                {
                    "id": "enr_1",
                    "student_id": "std_no_data",
                    "organization_id": "org_1",
                    "mentor_id": "mtr_2",
                    "is_active": True,
                    "day": 10,
                    "total_days": 100,
                    "days_left": 90,
                    "engagement_score": 0.55,
                    "progress_score": 0.6,
                    "ltv_cents": 100000,
                    "updated_at": "2026-05-01T00:00:00Z",
                },
                {
                    "id": "enr_2",
                    "student_id": "std_with_data",
                    "organization_id": "org_1",
                    "mentor_id": "mtr_2",
                    "is_active": True,
                    "day": 10,
                    "total_days": 100,
                    "days_left": 90,
                    "engagement_score": 0.55,
                    "progress_score": 0.6,
                    "ltv_cents": 100000,
                    "updated_at": "2026-05-01T00:00:00Z",
                },
            ]

    class _Measurements:
        runtime_backend = "postgres"

        def list_measurements(self):
            return [{"id": "mea_1", "enrollment_id": "enr_2", "metric_id": "met_1", "value_baseline": 1, "value_current": 2}]

    class _Metrics:
        def list_metrics(self):
            return [{"id": "met_1", "pillar_id": "plr_1", "name": "Indicador"}]

    class _Checkpoints:
        runtime_backend = "postgres"

        def list_by_enrollment(self, enrollment_id: str):
            return []

    class _Assignments:
        def list_assignments(self):
            return []

    service = IndicatorCargaService(
        students=_Students(),
        organizations=_Organizations(),
        enrollments=_Enrollments(),
        metrics=_Metrics(),
        measurements=_Measurements(),
        checkpoints=_Checkpoints(),
        product_assignments=_Assignments(),
    )

    payload = service.list_command_center_students(mentor_id="mtr_2")
    assert len(payload["items"]) == 2
    assert payload["items"][0]["id"] == "std_with_data"
    assert payload["items"][0]["hasRadarData"] is True
    assert payload["items"][1]["id"] == "std_no_data"
    assert payload["items"][1]["hasRadarData"] is False
