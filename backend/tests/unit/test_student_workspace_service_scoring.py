from __future__ import annotations

from pathlib import Path

import pytest

from app.storage.analytical_history_repository import AnalyticalHistoryRepository
from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.measurement_history_repository import MeasurementHistoryRepository
from app.storage.measurement_overall_repository import MeasurementOverallRepository
from app.storage.measurement_repository import MeasurementRepository
from app.storage.metric_repository import MetricRepository
from app.storage.organization_repository import OrganizationRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository
from app.storage.student_repository import StudentRepository
from app.services.student_workspace_service import StudentWorkspaceService


class _FakeIndicatorCargaService:
    def get_student_radar(self, *, student_id: str) -> dict[str, str]:
        return {"studentId": student_id}


def _build_workspace(tmp_path: Path) -> dict[str, object]:
    students = StudentRepository(tmp_path / "students.json")
    enrollments = EnrollmentRepository(tmp_path / "enrollments.json")
    measurements = MeasurementRepository(tmp_path / "measurements.json")
    metrics = MetricRepository(tmp_path / "metrics.json")
    pillars = PillarRepository(tmp_path / "pillars.json")
    protocols = ProtocolRepository(tmp_path / "protocols.json")
    organizations = OrganizationRepository(tmp_path / "organizations.json")
    overalls = MeasurementOverallRepository(tmp_path / "measurement_overalls.json")
    measurement_history = MeasurementHistoryRepository(tmp_path / "measurement_history.json")
    analytical_history = AnalyticalHistoryRepository(tmp_path / "analytical_history.json")

    organization = organizations.create(name="Mentoria Teste")
    protocol = protocols.create(organization_id=organization["id"], name="Metodo Teste")
    pillar = pillars.create(protocol_id=protocol["id"], name="Produto")
    student = students.create(full_name="Aluno Teste", email="aluno.teste@swaif.local")
    enrollment = enrollments.create(
        student_id=student["id"],
        organization_id=organization["id"],
        mentor_id="men_1",
        progress_score=0.0,
        engagement_score=0.0,
        day=10,
        total_days=100,
        days_left=90,
        ltv_cents=10000,
    )

    faturamento = metrics.create(
        protocol_id=protocol["id"],
        pillar_id=pillar["id"],
        name="Faturamento",
        code="faturamento",
        direction="higher_better",
        unit="R$",
        scoring_rules={
            "version": 2,
            "input": {"kind": "number", "unit": "R$"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {"when": {"op": "lt", "value": 100000}, "then": {"assign": 5}},
                    {"when": {"range": {"min": 100000, "max": 500000}}, "then": {"assign": 10}},
                    {"when": {"op": "gt", "value": 500000}, "then": {"assign": 20}},
                ],
            },
            "normalization": {"basis": "max_score", "value": 20},
        },
        score_type="static",
        min_score=5,
        max_score=20,
        max_basis_score="MAX_VALUE",
        mcv_score=10,
    )
    recorrencia = metrics.create(
        protocol_id=protocol["id"],
        pillar_id=pillar["id"],
        name="Recorrencia",
        code="recorrencia",
        direction="higher_better",
        scoring_rules={
            "version": 2,
            "input": {"kind": "number"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {"when": {"op": "gt", "value": 0}, "then": {"assign": 20}},
                ],
            },
            "normalization": {"basis": "max_score", "value": 20},
        },
        score_type="static",
        min_score=0,
        max_score=20,
        max_basis_score="MAX_VALUE",
        mcv_score=20,
    )

    measurements.replace_for_enrollment(
        enrollment["id"],
        [
            {
                "metric_id": faturamento["id"],
                "value_baseline": 100000.0,
                "value_current": 100000.0,
                "value_projected": 500000.5,
                "improving_trend": True,
            },
            {
                "metric_id": recorrencia["id"],
                "value_baseline": 1.0,
                "value_current": 1.0,
                "value_projected": 1.0,
                "improving_trend": True,
            },
        ],
    )

    return {
        "students": students,
        "enrollments": enrollments,
        "measurements": measurements,
        "metrics": metrics,
        "pillars": pillars,
        "protocols": protocols,
        "overalls": overalls,
        "measurement_history": measurement_history,
        "analytical_history": analytical_history,
        "student": student,
        "enrollment": enrollment,
        "pillar": pillar,
        "faturamento": faturamento,
    }


def test_generate_measurement_overall_uses_normalized_metric_scores(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace = _build_workspace(tmp_path)
    monkeypatch.setenv("ENROLLMENT_STORE_PATH", str(tmp_path / "enrollments.json"))
    monkeypatch.setenv("PROTOCOL_STORE_PATH", str(tmp_path / "protocols.json"))
    monkeypatch.setenv("PILLAR_STORE_PATH", str(tmp_path / "pillars.json"))
    monkeypatch.setenv("METRIC_STORE_PATH", str(tmp_path / "metrics.json"))
    monkeypatch.setenv("MEASUREMENT_STORE_PATH", str(tmp_path / "measurements.json"))
    monkeypatch.setenv("STUDENT_STORE_PATH", str(tmp_path / "students.json"))
    monkeypatch.setenv("MEASUREMENT_OVERALL_STORE_PATH", str(tmp_path / "measurement_overalls.json"))
    monkeypatch.setenv("ANALYTICAL_HISTORY_STORE_PATH", str(tmp_path / "analytical_history.json"))
    monkeypatch.setenv("MEASUREMENT_HISTORY_STORE_PATH", str(tmp_path / "measurement_history.json"))

    overalls = workspace["overalls"]
    assert isinstance(overalls, MeasurementOverallRepository)
    overalls.generate_for_all_enrollments()

    overall = overalls.get_by_enrollment(workspace["enrollment"]["id"])
    assert overall is not None

    metric_values = {item["metric_id"]: item["values"] for item in overall["metrics"]}
    faturamento_values = metric_values[workspace["faturamento"]["id"]]
    assert faturamento_values == {"goal": 1.0, "base": 0.5, "real": 0.5}


def test_update_self_measurement_current_accepts_raw_value_and_recomputes_overall(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace = _build_workspace(tmp_path)
    monkeypatch.setenv("ENROLLMENT_STORE_PATH", str(tmp_path / "enrollments.json"))
    monkeypatch.setenv("PROTOCOL_STORE_PATH", str(tmp_path / "protocols.json"))
    monkeypatch.setenv("PILLAR_STORE_PATH", str(tmp_path / "pillars.json"))
    monkeypatch.setenv("METRIC_STORE_PATH", str(tmp_path / "metrics.json"))
    monkeypatch.setenv("MEASUREMENT_STORE_PATH", str(tmp_path / "measurements.json"))
    monkeypatch.setenv("STUDENT_STORE_PATH", str(tmp_path / "students.json"))
    monkeypatch.setenv("MEASUREMENT_OVERALL_STORE_PATH", str(tmp_path / "measurement_overalls.json"))

    overalls = workspace["overalls"]
    assert isinstance(overalls, MeasurementOverallRepository)
    overalls.generate_for_all_enrollments()

    service = StudentWorkspaceService(
        students=workspace["students"],
        enrollments=workspace["enrollments"],
        measurements=workspace["measurements"],
        metrics=workspace["metrics"],
        pillars=workspace["pillars"],
        measurement_overalls=workspace["overalls"],
        indicator_carga=_FakeIndicatorCargaService(),
        measurement_history=workspace["measurement_history"],
        analytical_history=workspace["analytical_history"],
    )

    measurements = workspace["measurements"]
    assert isinstance(measurements, MeasurementRepository)
    measurement = next(item for item in measurements.list_by_enrollment(workspace["enrollment"]["id"]) if item["metric_id"] == workspace["faturamento"]["id"])
    service.resolve_student_context = lambda *, user: (workspace["student"], workspace["enrollment"])  # type: ignore[method-assign]

    result = service.update_self_measurement_current(
        user={"role": "aluno", "email": workspace["student"]["email"]},
        measurement_id=measurement["id"],
        value_current=500000.5,
    )

    assert result["valueCurrent"] == 500000.5

    measurement_history = workspace["measurement_history"]
    assert isinstance(measurement_history, MeasurementHistoryRepository)
    history_events = measurement_history.list_by_measurement(measurement["id"])
    assert len(history_events) == 1
    history = history_events[0]
    assert history["metric_id"] == workspace["faturamento"]["id"]
    assert history["actor_role"] == "client"
    assert history["value_absolute_before"] == 100000.0
    assert history["value_absolute_after"] == 500000.5
    assert float(history["value_relative_before"]) == 0.5
    assert float(history["value_relative_after"]) == 1.0

    analytical_history = workspace["analytical_history"]
    assert isinstance(analytical_history, AnalyticalHistoryRepository)
    analytical_events = analytical_history.list_by_enrollment(workspace["enrollment"]["id"])
    event_types = {event["event_type"] for event in analytical_events}
    assert "assignment_score_snapshot" in event_types
    assert "decision_matrix_snapshot" in event_types
    assert "radar_axis_snapshot" in event_types

    product_events = analytical_history.list_by_product(workspace["enrollment"]["organization_id"])
    assert any(event["event_type"] == "product_radar_snapshot" for event in product_events)

    overall = overalls.get_by_enrollment(workspace["enrollment"]["id"])
    assert overall is not None
    updated_pillar = next(item for item in overall["pillars"] if item["pillar_id"] == workspace["pillar"]["id"])
    assert float(updated_pillar["metric_average"]["real"]) == 1.0


def test_product_radar_snapshot_uses_geometric_mean_across_students(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace = _build_workspace(tmp_path)
    monkeypatch.setenv("ENROLLMENT_STORE_PATH", str(tmp_path / "enrollments.json"))
    monkeypatch.setenv("PROTOCOL_STORE_PATH", str(tmp_path / "protocols.json"))
    monkeypatch.setenv("PILLAR_STORE_PATH", str(tmp_path / "pillars.json"))
    monkeypatch.setenv("METRIC_STORE_PATH", str(tmp_path / "metrics.json"))
    monkeypatch.setenv("MEASUREMENT_STORE_PATH", str(tmp_path / "measurements.json"))
    monkeypatch.setenv("STUDENT_STORE_PATH", str(tmp_path / "students.json"))
    monkeypatch.setenv("MEASUREMENT_OVERALL_STORE_PATH", str(tmp_path / "measurement_overalls.json"))
    monkeypatch.setenv("ANALYTICAL_HISTORY_STORE_PATH", str(tmp_path / "analytical_history.json"))

    students = workspace["students"]
    enrollments = workspace["enrollments"]
    measurements = workspace["measurements"]
    metrics = workspace["metrics"]
    assert isinstance(students, StudentRepository)
    assert isinstance(enrollments, EnrollmentRepository)
    assert isinstance(measurements, MeasurementRepository)
    assert isinstance(metrics, MetricRepository)

    second_student = students.create(full_name="Aluno Dois", email="aluno.dois@swaif.local")
    second_enrollment = enrollments.create(
        student_id=second_student["id"],
        organization_id=workspace["enrollment"]["organization_id"],
        mentor_id="men_1",
        progress_score=0.0,
        engagement_score=0.0,
        day=11,
        total_days=100,
        days_left=89,
        ltv_cents=10000,
    )

    measurements.replace_for_enrollment(
        second_enrollment["id"],
        [
            {
                "metric_id": workspace["faturamento"]["id"],
                "value_baseline": 100000.0,
                "value_current": 100000.0,
                "value_projected": 500000.5,
                "improving_trend": True,
            },
            {
                "metric_id": next(
                    metric["id"]
                    for metric in metrics.list_metrics()
                    if metric["id"] != workspace["faturamento"]["id"]
                ),
                "value_baseline": 1.0,
                "value_current": 1.0,
                "value_projected": 1.0,
                "improving_trend": True,
            },
        ],
    )

    overalls = workspace["overalls"]
    assert isinstance(overalls, MeasurementOverallRepository)
    overalls.generate_for_all_enrollments()

    service = StudentWorkspaceService(
        students=workspace["students"],
        enrollments=workspace["enrollments"],
        measurements=workspace["measurements"],
        metrics=workspace["metrics"],
        pillars=workspace["pillars"],
        measurement_overalls=workspace["overalls"],
        indicator_carga=_FakeIndicatorCargaService(),
        measurement_history=workspace["measurement_history"],
        analytical_history=workspace["analytical_history"],
    )

    measurement = next(
        item
        for item in measurements.list_by_enrollment(workspace["enrollment"]["id"])
        if item["metric_id"] == workspace["faturamento"]["id"]
    )
    service.resolve_student_context = lambda *, user: (workspace["student"], workspace["enrollment"])  # type: ignore[method-assign]

    service.update_self_measurement_current(
        user={"role": "aluno", "email": workspace["student"]["email"]},
        measurement_id=measurement["id"],
        value_current=500000.5,
    )

    analytical_history = workspace["analytical_history"]
    assert isinstance(analytical_history, AnalyticalHistoryRepository)
    product_events = [
        event
        for event in analytical_history.list_by_product(workspace["enrollment"]["organization_id"])
        if event["event_type"] == "product_radar_snapshot" and event["pillar_id"] == workspace["pillar"]["id"]
    ]
    assert product_events

    latest_product_snapshot = product_events[-1]
    # Student 1 pillar current = 1.0; Student 2 pillar current = 0.75.
    # Product default current = geometric mean across students.
    assert round(float(latest_product_snapshot["payload"]["current_score"]), 6) == 0.866025