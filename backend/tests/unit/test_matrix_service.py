from app.services.indicator_carga_service import IndicatorCargaService


class _FakeStudentRepository:
    def __init__(self) -> None:
        self.items = {
            "std_1": {"id": "std_1", "full_name": "Aluno 1", "initials": "A1"},
            "std_2": {"id": "std_2", "full_name": "Aluno 2", "initials": "A2"},
            "std_3": {"id": "std_3", "full_name": "Aluno 3", "initials": "A3"},
            "std_4": {"id": "std_4", "full_name": "Aluno 4", "initials": "A4"},
        }

    def get_by_id(self, student_id: str):
        return self.items.get(student_id)


class _FakeOrganizationRepository:
    def get_by_id(self, organization_id: str):
        return {"id": organization_id, "name": "Mentoria Matrix"}


class _FakeEnrollmentRepository:
    def __init__(self) -> None:
        self.items = [
            {
                "id": "enr_1",
                "student_id": "std_1",
                "organization_id": "org_1",
                "day": 70,
                "total_days": 100,
                "days_left": 40,
                "engagement_score": 0.8,
                "progress_score": 0.7,
                "ltv_cents": 100000,
                "is_active": True,
            },
            {
                "id": "enr_2",
                "student_id": "std_2",
                "organization_id": "org_1",
                "day": 40,
                "total_days": 100,
                "days_left": 80,
                "engagement_score": 0.7,
                "progress_score": 0.4,
                "ltv_cents": 50000,
                "is_active": True,
            },
            {
                "id": "enr_3",
                "student_id": "std_3",
                "organization_id": "org_1",
                "day": 70,
                "total_days": 100,
                "days_left": 30,
                "engagement_score": 0.05,
                "progress_score": 0.7,
                "ltv_cents": 70000,
                "is_active": True,
            },
            {
                "id": "enr_4",
                "student_id": "std_4",
                "organization_id": "org_1",
                "day": 80,
                "total_days": 100,
                "days_left": 20,
                "engagement_score": 0.65,
                "progress_score": 0.8,
                "ltv_cents": 30000,
                "is_active": True,
            },
        ]

    def list_enrollments(self):
        return self.items

    def get_active_by_student(self, student_id: str):
        for item in self.items:
            if item["student_id"] == student_id:
                return item
        return None


class _FakeMetricRepository:
    def __init__(self) -> None:
        self.items = {
            "met_1": {"id": "met_1", "name": "Frequencia"},
            "met_2": {"id": "met_2", "name": "Consistencia"},
        }

    def get_by_id(self, metric_id: str):
        return self.items.get(metric_id)


class _FakeMeasurementRepository:
    def list_by_enrollment(self, enrollment_id: str):
        return [
            {"id": f"mea_{enrollment_id}_1", "metric_id": "met_1", "value_current": 60, "value_baseline": 50, "value_projected": 70, "improving_trend": True},
            {"id": f"mea_{enrollment_id}_2", "metric_id": "met_2", "value_current": 40, "value_baseline": 30, "value_projected": None, "improving_trend": False},
        ]

    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict]):
        return rows


class _FakeCheckpointRepository:
    def list_by_enrollment(self, enrollment_id: str):
        return []

    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict]):
        return rows


def _build_service() -> IndicatorCargaService:
    return IndicatorCargaService(
        students=_FakeStudentRepository(),
        organizations=_FakeOrganizationRepository(),
        enrollments=_FakeEnrollmentRepository(),
        metrics=_FakeMetricRepository(),
        measurements=_FakeMeasurementRepository(),
        checkpoints=_FakeCheckpointRepository(),
        pillars=None,
    )


def test_matrix_kpis_and_fields() -> None:
    service = _build_service()
    payload = service.get_renewal_matrix(filter_mode="all")

    assert payload["filter"] == "all"
    assert len(payload["items"]) == 4
    required_item_fields = {
        "id",
        "name",
        "initials",
        "programName",
        "plan",
        "progress",
        "engagement",
        "daysLeft",
        "urgency",
        "ltv",
        "renewalReason",
        "suggestion",
        "markers",
        "quadrant",
    }
    assert required_item_fields.issubset(set(payload["items"][0].keys()))

    kpis = payload["kpis"]
    assert kpis["totalLTV"] == 250000
    assert kpis["criticalRenewals"] == 2
    assert kpis["rescueCount"] == 1
    assert kpis["avgEngagement"] == 55.0


def test_matrix_filters() -> None:
    service = _build_service()

    top_right = service.get_renewal_matrix(filter_mode="topRight")
    assert len(top_right["items"]) == 2
    assert all(item["quadrant"] == "topRight" for item in top_right["items"])

    critical = service.get_renewal_matrix(filter_mode="critical")
    assert len(critical["items"]) == 2
    assert all(item["daysLeft"] <= 45 and item["quadrant"] == "topRight" for item in critical["items"])

    rescue = service.get_renewal_matrix(filter_mode="rescue")
    assert len(rescue["items"]) == 1
    assert rescue["items"][0]["urgency"] == "rescue"
