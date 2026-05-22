from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.main import app
from app.storage.checkpoint_repository import CheckpointRepository
from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.measurement_history_repository import MeasurementHistoryRepository
from app.storage.measurement_repository import MeasurementRepository
from app.storage.mentor_repository import MentorRepository
from app.storage.product_assignment_repository import ProductAssignmentRepository
from app.storage.student_repository import StudentRepository
from app.storage.user_repository import UserRepository


def _configure_stores(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    monkeypatch.delenv("SUPABASE_RUNTIME_REQUIRED", raising=False)
    monkeypatch.setenv("USER_STORE_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(tmp_path / "contacts_users_v2.json"))
    monkeypatch.setenv("PRODUCT_ASSIGNMENT_STORE_PATH", str(tmp_path / "product_assignments.json"))
    monkeypatch.setenv("ORG_STORE_PATH", str(tmp_path / "organizations.json"))
    monkeypatch.setenv("MENTOR_STORE_PATH", str(tmp_path / "mentors.json"))
    monkeypatch.setenv("PROTOCOL_STORE_PATH", str(tmp_path / "protocols.json"))
    monkeypatch.setenv("PILLAR_STORE_PATH", str(tmp_path / "pillars.json"))
    monkeypatch.setenv("METRIC_STORE_PATH", str(tmp_path / "metrics.json"))
    monkeypatch.setenv("STUDENT_STORE_PATH", str(tmp_path / "students.json"))
    monkeypatch.setenv("ENROLLMENT_STORE_PATH", str(tmp_path / "enrollments.json"))
    monkeypatch.setenv("MEASUREMENT_STORE_PATH", str(tmp_path / "measurements.json"))
    monkeypatch.setenv("CHECKPOINT_STORE_PATH", str(tmp_path / "checkpoints.json"))
    monkeypatch.setenv("MEASUREMENT_OVERALL_STORE_PATH", str(tmp_path / "measurement_overalls.json"))
    monkeypatch.setenv("MEASUREMENT_HISTORY_STORE_PATH", str(tmp_path / "measurement_history.json"))
    monkeypatch.setenv("ANALYTICAL_HISTORY_STORE_PATH", str(tmp_path / "analytical_history.json"))


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _create_mentor_user(*, email: str, password: str) -> dict[str, str]:
    mentor = MentorRepository().create(full_name=f"Mentor {email}", email=email)
    UserRepository().create(
        id=f"usr_{mentor['id']}",
        email=email,
        password_hash=hash_password(password),
        role="mentor",
    )
    return {"mentor_id": str(mentor["id"]), "email": email, "password": password}


def _prepare_live_mentor_data(
    client: TestClient,
    *,
    headers: dict[str, str],
    mentor_id: str,
    other_mentor_id: str,
    tmp_path: Path,
) -> dict[str, str | int]:
    organization = client.post("/admin/mentorias", json={"name": "Mentoria Mentor"}, headers=headers).json()
    organization_id = organization["id"]

    protocol = client.post(
        "/admin/protocolos",
        json={"organization_id": organization_id, "name": "Metodo Mentor"},
        headers=headers,
    ).json()
    protocol_id = protocol["id"]

    pillar_a = client.post(
        "/admin/pilares",
        json={"protocol_id": protocol_id, "name": "Compromisso", "code": "compromisso", "order_index": 1},
        headers=headers,
    ).json()
    pillar_b = client.post(
        "/admin/pilares",
        json={"protocol_id": protocol_id, "name": "Evolucao", "code": "evolucao", "order_index": 2},
        headers=headers,
    ).json()

    metric_a = client.post(
        "/admin/metricas",
        json={"protocol_id": protocol_id, "pillar_id": pillar_a["id"], "name": "Frequencia"},
        headers=headers,
    ).json()
    metric_b = client.post(
        "/admin/metricas",
        json={"protocol_id": protocol_id, "pillar_id": pillar_b["id"], "name": "Consistencia"},
        headers=headers,
    ).json()

    primary_student = client.post("/admin/alunos", json={"full_name": "Aluno Mentor"}, headers=headers).json()
    hidden_student = client.post("/admin/alunos", json={"full_name": "Aluno Outro Mentor"}, headers=headers).json()

    today = datetime.now(timezone.utc).date()
    start_date = (today - timedelta(days=40)).isoformat()
    end_date = (today + timedelta(days=20)).isoformat()
    StudentRepository().update(
        id=primary_student["id"],
        start_enrollment_date=start_date,
        end_enrollment_date=end_date,
    )

    primary_link = client.post(
        f"/admin/alunos/{primary_student['id']}/vincular-mentoria",
        json={
            "organization_id": organization_id,
            "mentor_id": mentor_id,
            "progress_score": 0.0,
            "engagement_score": 0.0,
            "day": 0,
            "total_days": 0,
            "days_left": 0,
            "ltv_cents": 150000,
        },
        headers=headers,
    )
    assert primary_link.status_code == 200
    primary_enrollment = primary_link.json()

    hidden_link = client.post(
        f"/admin/alunos/{hidden_student['id']}/vincular-mentoria",
        json={
            "organization_id": organization_id,
            "mentor_id": other_mentor_id,
            "progress_score": 0.0,
            "engagement_score": 0.0,
            "day": 0,
            "total_days": 0,
            "days_left": 0,
            "ltv_cents": 90000,
        },
        headers=headers,
    )
    assert hidden_link.status_code == 200
    hidden_enrollment = hidden_link.json()

    load_payload = {
        "metric_values": [
            {
                "metric_id": metric_a["id"],
                "value_baseline": 80,
                "value_current": 52,
                "value_projected": 65,
                "improving_trend": False,
            },
            {
                "metric_id": metric_b["id"],
                "value_baseline": 60,
                "value_current": 64,
                "value_projected": 72,
                "improving_trend": True,
            },
        ],
        "checkpoints": [
            {"week": 2, "status": "yellow", "label": "Oscilacao detectada"},
            {"week": 4, "status": "green", "label": "Recuperacao"},
        ],
    }
    load = client.post(
        f"/admin/alunos/{primary_student['id']}/indicadores/carga-inicial",
        json=load_payload,
        headers=headers,
    )
    if load.status_code == 409:
        measurements = MeasurementRepository()
        checkpoints = CheckpointRepository()
        measurements.replace_for_enrollment(
            str(primary_enrollment["id"]),
            load_payload["metric_values"],
        )
        checkpoints.replace_for_enrollment(
            str(primary_enrollment["id"]),
            load_payload["checkpoints"],
        )
    else:
        assert load.status_code == 200

    overalls_payload = {
        "version": 1,
        "items": [
            {
                "enrollment_id": primary_enrollment["id"],
                "protocol_id": protocol_id,
                "metrics": [],
                "pillars": [
                    {"pillar_id": pillar_a["id"], "metric_average": {"goal": 1.0, "base": 0.2, "real": 0.4}},
                    {"pillar_id": pillar_b["id"], "metric_average": {"goal": 1.0, "base": 0.6, "real": 0.8}},
                ],
                "decision_matrix": {
                    "product_score": 0.71,
                    "engagement_score": 0.69,
                    "thresholds": {"prd_thr": 0.7, "eng_thr": 0.7},
                },
            },
            {
                "enrollment_id": hidden_enrollment["id"],
                "protocol_id": protocol_id,
                "metrics": [],
                "pillars": [
                    {"pillar_id": pillar_a["id"], "metric_average": {"goal": 1.0, "base": 0.3, "real": 0.3}},
                    {"pillar_id": pillar_b["id"], "metric_average": {"goal": 1.0, "base": 0.5, "real": 0.5}},
                ],
                "decision_matrix": {
                    "product_score": 0.35,
                    "engagement_score": 0.42,
                    "thresholds": {"prd_thr": 0.7, "eng_thr": 0.7},
                },
            },
        ],
    }
    (tmp_path / "measurement_overalls.json").write_text(json.dumps(overalls_payload), encoding="utf-8")

    expected_total_days = (datetime.fromisoformat(end_date) - datetime.fromisoformat(start_date)).days
    expected_day = (today - datetime.fromisoformat(start_date).date()).days
    expected_days_left = (datetime.fromisoformat(end_date).date() - today).days

    return {
        "organization_id": str(organization_id),
        "enrollment_id": str(primary_enrollment["id"]),
        "student_id": str(primary_student["id"]),
        "hidden_student_id": str(hidden_student["id"]),
        "pillar_id": str(pillar_a["id"]),
        "expected_day": expected_day,
        "expected_total_days": expected_total_days,
        "expected_days_left": expected_days_left,
    }


def _patch_record_backfill_inputs(
    *,
    tmp_path: Path,
    organization_id: str,
    enrollment_id: str,
    mentor_id: str,
) -> None:
    org_file = tmp_path / "organizations.json"
    org_payload = json.loads(org_file.read_text(encoding="utf-8"))
    for item in org_payload.get("items", []):
        if str(item.get("id") or "") == organization_id:
            item["mentor_id"] = mentor_id
    org_file.write_text(json.dumps(org_payload), encoding="utf-8")

    enr_file = tmp_path / "enrollments.json"
    enr_payload = json.loads(enr_file.read_text(encoding="utf-8"))
    for item in enr_payload.get("items", []):
        if str(item.get("id") or "") == enrollment_id:
            item["mentor_id"] = None
    enr_file.write_text(json.dumps(enr_payload), encoding="utf-8")

    asg_file = tmp_path / "product_assignments.json"
    asg_payload = json.loads(asg_file.read_text(encoding="utf-8"))
    for item in asg_payload.get("items", []):
        if str(item.get("id") or "") == enrollment_id:
            item["mentor_id"] = None
            item["provider_id"] = None
    asg_file.write_text(json.dumps(asg_payload), encoding="utf-8")


def _patch_assignment_alias_conflict(
    *,
    tmp_path: Path,
    enrollment_id: str,
    mentor_id: str,
    provider_id: str,
) -> None:
    asg_file = tmp_path / "product_assignments.json"
    asg_payload = json.loads(asg_file.read_text(encoding="utf-8"))
    for item in asg_payload.get("items", []):
        if str(item.get("id") or "") == enrollment_id:
            item["mentor_id"] = mentor_id
            item["provider_id"] = provider_id
    asg_file.write_text(json.dumps(asg_payload), encoding="utf-8")


def test_mentor_routes_require_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/mentor/matriz-renovacao")

    assert response.status_code == 401


def test_mentor_runtime_requires_supabase_db_url_when_enforced(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    monkeypatch.setenv("SUPABASE_RUNTIME_REQUIRED", "true")
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)

    client = TestClient(app)
    mentor_user = _create_mentor_user(email="mentor.requireddb@swaif.local", password="mentor123")
    token = _login(client, mentor_user["email"], mentor_user["password"])

    response = client.get(
        "/mentor/matriz-renovacao",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 503
    payload = response.json()
    assert payload["error"]["code"] == "SUPABASE_DB_URL_REQUIRED"


def test_mentor_matrix_uses_live_data_and_scopes_by_mentor(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    primary_mentor = _create_mentor_user(email="mentor2@swaif.local", password="mentor456")
    other_mentor = _create_mentor_user(email="mentor3@swaif.local", password="mentor789")

    client = TestClient(app)
    admin_headers = {"Authorization": f"Bearer {_login(client, 'admin@swaif.local', 'admin123')}"}
    mentor_headers = {"Authorization": f"Bearer {_login(client, primary_mentor['email'], primary_mentor['password'])}"}

    prepared = _prepare_live_mentor_data(
        client,
        headers=admin_headers,
        mentor_id=str(primary_mentor["mentor_id"]),
        other_mentor_id=str(other_mentor["mentor_id"]),
        tmp_path=tmp_path,
    )

    admin_response = client.get("/mentor/matriz-renovacao", headers=admin_headers)
    assert admin_response.status_code == 403
    assert admin_response.json()["error"]["code"] == "AUTH_FORBIDDEN"

    mentor_response = client.get("/mentor/matriz-renovacao?filter=all", headers=mentor_headers)
    assert mentor_response.status_code == 200
    payload = mentor_response.json()

    assert payload["filter"] == "all"
    assert payload["context"]["mentorId"] == primary_mentor["mentor_id"]
    assert payload["context"]["mentorName"] == f"Mentor {primary_mentor['email']}"
    assert payload["context"]["protocolId"] == "prt_1"
    assert payload["context"]["protocolName"] == "Metodo Mentor"
    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["id"] == prepared["student_id"]
    assert item["progress"] == 0.71
    assert item["engagement"] == 0.69
    assert item["quadrant"] == "bottomRight"
    assert item["daysLeft"] == prepared["expected_days_left"]
    assert payload["kpis"]["totalLTV"] == 150000


def test_mentor_command_center_radar_and_timeline_use_live_student_data(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    primary_mentor = _create_mentor_user(email="mentor2@swaif.local", password="mentor456")
    other_mentor = _create_mentor_user(email="mentor3@swaif.local", password="mentor789")

    client = TestClient(app)
    admin_headers = {"Authorization": f"Bearer {_login(client, 'admin@swaif.local', 'admin123')}"}
    mentor_headers = {"Authorization": f"Bearer {_login(client, primary_mentor['email'], primary_mentor['password'])}"}

    prepared = _prepare_live_mentor_data(
        client,
        headers=admin_headers,
        mentor_id=str(primary_mentor["mentor_id"]),
        other_mentor_id=str(other_mentor["mentor_id"]),
        tmp_path=tmp_path,
    )

    list_response = client.get("/mentor/centro-comando/alunos", headers=mentor_headers)
    assert list_response.status_code == 200
    payload = list_response.json()
    items = payload["items"]
    assert len(items) == 1
    assert payload["rankingMode"] == "full"
    assert items[0]["id"] == prepared["student_id"]
    assert items[0]["day"] == prepared["expected_day"]
    assert items[0]["totalDays"] == prepared["expected_total_days"]
    assert items[0]["daysLeft"] == prepared["expected_days_left"]

    detail_response = client.get(
        f"/mentor/centro-comando/alunos/{prepared['student_id']}",
        headers=mentor_headers,
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert len(detail["metricValues"]) == 2
    assert len(detail["checkpoints"]) == 2
    assert detail["day"] == prepared["expected_day"]

    forbidden_detail = client.get(
        f"/mentor/centro-comando/alunos/{prepared['hidden_student_id']}",
        headers=mentor_headers,
    )
    assert forbidden_detail.status_code == 404

    radar_response = client.get(f"/mentor/radar/alunos/{prepared['student_id']}", headers=mentor_headers)
    assert radar_response.status_code == 200
    radar = radar_response.json()
    assert len(radar["axisScores"]) == 2
    assert radar["avgBaseline"] == 0.4
    assert radar["avgCurrent"] == 0.6
    assert radar["avgProjected"] == 1.0

    clients_radar_response = client.get("/mentor/radar/clientes", headers=mentor_headers)
    assert clients_radar_response.status_code == 200
    clients_radar = clients_radar_response.json()
    assert len(clients_radar["clients"]) == 1
    assert clients_radar["clients"][0]["studentId"] == prepared["student_id"]
    assert len(clients_radar["axisScores"]) == 2
    assert clients_radar["avgCurrent"] == 0.6
    assert "mockTransformationPreview" not in clients_radar

    clients_radar_preview_response = client.get(
        "/mentor/radar/clientes?include_mock_preview=true",
        headers=mentor_headers,
    )
    assert clients_radar_preview_response.status_code == 200
    clients_radar_preview = clients_radar_preview_response.json()
    assert "mockTransformationPreview" in clients_radar_preview
    preview = clients_radar_preview["mockTransformationPreview"]
    assert preview["processingMode"] == "python_rules"
    assert preview["metricsCovered"] >= 1
    assert preview["parityWithDeclarative"] is True
    assert isinstance(preview["sourceRows"], list)
    assert isinstance(preview["transformed"], dict)

    metrics_response = client.get(
        f"/mentor/radar/alunos/{prepared['student_id']}/pilares/{prepared['pillar_id']}/metricas",
        headers=mentor_headers,
    )
    assert metrics_response.status_code == 200
    metrics_payload = metrics_response.json()
    assert metrics_payload["studentId"] == prepared["student_id"]
    assert len(metrics_payload["items"]) >= 1

    hidden_metrics = client.get(
        f"/mentor/radar/alunos/{prepared['hidden_student_id']}/pilares/{prepared['pillar_id']}/metricas",
        headers=mentor_headers,
    )
    assert hidden_metrics.status_code == 404

    timeline_response = client.get(
        f"/mentor/centro-comando/alunos/{prepared['student_id']}/timeline-anomalias",
        headers=mentor_headers,
    )
    assert timeline_response.status_code == 200
    timeline = timeline_response.json()
    assert timeline["summary"]["hasAnomalies"] is True
    assert timeline["summary"]["anomalyCount"] >= 1


def test_mentor_student_id_returns_product_pillars_and_pillar_metrics(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    primary_mentor = _create_mentor_user(email="mentor2@swaif.local", password="mentor456")
    other_mentor = _create_mentor_user(email="mentor3@swaif.local", password="mentor789")

    client = TestClient(app)
    admin_headers = {"Authorization": f"Bearer {_login(client, 'admin@swaif.local', 'admin123')}"}
    mentor_headers = {"Authorization": f"Bearer {_login(client, primary_mentor['email'], primary_mentor['password'])}"}

    prepared = _prepare_live_mentor_data(
        client,
        headers=admin_headers,
        mentor_id=str(primary_mentor["mentor_id"]),
        other_mentor_id=str(other_mentor["mentor_id"]),
        tmp_path=tmp_path,
    )

    detail_response = client.get(
        f"/mentor/centro-comando/alunos/{prepared['student_id']}",
        headers=mentor_headers,
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == prepared["student_id"]
    assert detail["programName"] == "Mentoria Mentor"

    radar_response = client.get(
        f"/mentor/radar/alunos/{prepared['student_id']}",
        headers=mentor_headers,
    )
    assert radar_response.status_code == 200
    radar = radar_response.json()
    assert radar["studentId"] == prepared["student_id"]
    assert len(radar["axisScores"]) == 2
    first_axis = radar["axisScores"][0]
    assert first_axis["axisId"] == prepared["pillar_id"]
    assert first_axis["baseline"] == 0.2
    assert first_axis["current"] == 0.4
    assert first_axis["projected"] == 1.0

    pillar_metrics_response = client.get(
        f"/mentor/radar/alunos/{prepared['student_id']}/pilares/{prepared['pillar_id']}/metricas",
        headers=mentor_headers,
    )
    assert pillar_metrics_response.status_code == 200
    pillar_metrics = pillar_metrics_response.json()
    assert pillar_metrics["studentId"] == prepared["student_id"]
    assert pillar_metrics["pillar"]["id"] == prepared["pillar_id"]
    assert len(pillar_metrics["items"]) >= 1

    first_metric = pillar_metrics["items"][0]
    assert first_metric["measurementId"]
    assert first_metric["metricId"]
    assert first_metric["valueBaseline"] == 80.0
    assert first_metric["valueCurrent"] == 52.0
    assert first_metric["valueProjected"] == 65.0


def test_mentor_can_edit_student_individual_radar_metric(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    primary_mentor = _create_mentor_user(email="mentor2@swaif.local", password="mentor456")
    other_mentor = _create_mentor_user(email="mentor3@swaif.local", password="mentor789")

    client = TestClient(app)
    admin_headers = {"Authorization": f"Bearer {_login(client, 'admin@swaif.local', 'admin123')}"}
    mentor_headers = {"Authorization": f"Bearer {_login(client, primary_mentor['email'], primary_mentor['password'])}"}

    prepared = _prepare_live_mentor_data(
        client,
        headers=admin_headers,
        mentor_id=str(primary_mentor["mentor_id"]),
        other_mentor_id=str(other_mentor["mentor_id"]),
        tmp_path=tmp_path,
    )

    metrics_response = client.get(
        f"/mentor/radar/alunos/{prepared['student_id']}/pilares/{prepared['pillar_id']}/metricas",
        headers=mentor_headers,
    )
    assert metrics_response.status_code == 200
    measurement_id = metrics_response.json()["items"][0]["measurementId"]

    update_response = client.patch(
        f"/mentor/radar/alunos/{prepared['student_id']}/measurements/{measurement_id}",
        json={"value_current": 33},
        headers=mentor_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["valueCurrent"] == 33.0

    reread_response = client.get(
        f"/mentor/radar/alunos/{prepared['student_id']}/pilares/{prepared['pillar_id']}/metricas",
        headers=mentor_headers,
    )
    assert reread_response.status_code == 200
    assert any(item["measurementId"] == measurement_id and item["valueCurrent"] == 33.0 for item in reread_response.json()["items"])

    history_events = MeasurementHistoryRepository().list_by_measurement(measurement_id)
    assert len(history_events) == 1
    assert history_events[0]["actor_role"] == "provider"

    forbidden_update = client.patch(
        f"/mentor/radar/alunos/{prepared['hidden_student_id']}/measurements/{measurement_id}",
        json={"value_current": 21},
        headers=mentor_headers,
    )
    assert forbidden_update.status_code == 404
    assert forbidden_update.json()["error"]["code"] == "ALUNO_NOT_FOUND"


def test_mentor_workspace_repair_gate_backfills_links_and_is_idempotent(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    primary_mentor = _create_mentor_user(email="mentor2@swaif.local", password="mentor456")
    other_mentor = _create_mentor_user(email="mentor3@swaif.local", password="mentor789")

    client = TestClient(app)
    admin_headers = {"Authorization": f"Bearer {_login(client, 'admin@swaif.local', 'admin123')}"}
    mentor_headers = {"Authorization": f"Bearer {_login(client, primary_mentor['email'], primary_mentor['password'])}"}

    prepared = _prepare_live_mentor_data(
        client,
        headers=admin_headers,
        mentor_id=str(primary_mentor["mentor_id"]),
        other_mentor_id=str(other_mentor["mentor_id"]),
        tmp_path=tmp_path,
    )

    _patch_record_backfill_inputs(
        tmp_path=tmp_path,
        organization_id=str(prepared["organization_id"]),
        enrollment_id=str(prepared["enrollment_id"]),
        mentor_id=str(primary_mentor["mentor_id"]),
    )
    monkeypatch.setenv("MENTOR_WORKSPACE_BACKFILL_REPAIR_ENABLED", "true")

    center_response = client.get("/mentor/centro-comando/alunos", headers=mentor_headers)
    assert center_response.status_code == 200
    center_payload = center_response.json()
    assert len(center_payload["items"]) == 1
    assert center_payload["items"][0]["id"] == prepared["student_id"]

    radar_response = client.get(
        f"/mentor/radar/alunos/{prepared['student_id']}",
        headers=mentor_headers,
    )
    assert radar_response.status_code == 200
    radar_payload = radar_response.json()
    assert radar_payload["studentId"] == prepared["student_id"]
    assert len(radar_payload["axisScores"]) == 2

    matrix_response = client.get("/mentor/matriz-renovacao?filter=all", headers=mentor_headers)
    assert matrix_response.status_code == 200
    matrix_payload = matrix_response.json()
    assert len(matrix_payload["items"]) == 1
    assert matrix_payload["items"][0]["id"] == prepared["student_id"]

    enrollment = EnrollmentRepository().get_by_id(str(prepared["enrollment_id"]))
    assignment = ProductAssignmentRepository().get_by_id(str(prepared["enrollment_id"]))

    assert enrollment is not None
    assert enrollment["mentor_id"] == primary_mentor["mentor_id"]
    assert assignment is not None
    assert assignment["mentor_id"] == primary_mentor["mentor_id"]
    assert assignment["provider_id"] == primary_mentor["mentor_id"]
    first_enrollment_updated_at = str(enrollment["updated_at"])
    first_assignment_updated_at = str(assignment["updated_at"])

    second_center_response = client.get("/mentor/centro-comando/alunos", headers=mentor_headers)
    assert second_center_response.status_code == 200

    enrollment_after_second = EnrollmentRepository().get_by_id(str(prepared["enrollment_id"]))
    assignment_after_second = ProductAssignmentRepository().get_by_id(str(prepared["enrollment_id"]))
    assert enrollment_after_second is not None
    assert assignment_after_second is not None
    assert str(enrollment_after_second["updated_at"]) == first_enrollment_updated_at
    assert str(assignment_after_second["updated_at"]) == first_assignment_updated_at


def test_mentor_workspace_get_does_not_write_without_repair_gate(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    primary_mentor = _create_mentor_user(email="mentor2@swaif.local", password="mentor456")
    other_mentor = _create_mentor_user(email="mentor3@swaif.local", password="mentor789")

    client = TestClient(app)
    admin_headers = {"Authorization": f"Bearer {_login(client, 'admin@swaif.local', 'admin123')}"}
    mentor_headers = {"Authorization": f"Bearer {_login(client, primary_mentor['email'], primary_mentor['password'])}"}

    prepared = _prepare_live_mentor_data(
        client,
        headers=admin_headers,
        mentor_id=str(primary_mentor["mentor_id"]),
        other_mentor_id=str(other_mentor["mentor_id"]),
        tmp_path=tmp_path,
    )

    _patch_record_backfill_inputs(
        tmp_path=tmp_path,
        organization_id=str(prepared["organization_id"]),
        enrollment_id=str(prepared["enrollment_id"]),
        mentor_id=str(primary_mentor["mentor_id"]),
    )

    center_response = client.get("/mentor/centro-comando/alunos", headers=mentor_headers)
    assert center_response.status_code == 200
    center_payload = center_response.json()
    assert isinstance(center_payload.get("items"), list)

    radar_response = client.get(
        f"/mentor/radar/alunos/{prepared['student_id']}",
        headers=mentor_headers,
    )
    assert radar_response.status_code == 404
    assert radar_response.json()["error"]["code"] == "ALUNO_NOT_FOUND"

    matrix_response = client.get("/mentor/matriz-renovacao?filter=all", headers=mentor_headers)
    assert matrix_response.status_code == 200
    matrix_payload = matrix_response.json()
    assert isinstance(matrix_payload.get("items"), list)
    assert len(matrix_payload["items"]) == 0

    enrollment = EnrollmentRepository().get_by_id(str(prepared["enrollment_id"]))
    assignment = ProductAssignmentRepository().get_by_id(str(prepared["enrollment_id"]))
    assert enrollment is not None
    assert assignment is not None
    assert enrollment["mentor_id"] is None
    assert assignment["mentor_id"] is None
    assert assignment["provider_id"] is None


def test_mentor_workspace_repair_logs_provider_mentor_conflicts(monkeypatch, tmp_path: Path, caplog) -> None:
    _configure_stores(monkeypatch, tmp_path)
    primary_mentor = _create_mentor_user(email="mentor2@swaif.local", password="mentor456")
    other_mentor = _create_mentor_user(email="mentor3@swaif.local", password="mentor789")

    client = TestClient(app)
    admin_headers = {"Authorization": f"Bearer {_login(client, 'admin@swaif.local', 'admin123')}"}
    mentor_headers = {"Authorization": f"Bearer {_login(client, primary_mentor['email'], primary_mentor['password'])}"}

    prepared = _prepare_live_mentor_data(
        client,
        headers=admin_headers,
        mentor_id=str(primary_mentor["mentor_id"]),
        other_mentor_id=str(other_mentor["mentor_id"]),
        tmp_path=tmp_path,
    )

    _patch_assignment_alias_conflict(
        tmp_path=tmp_path,
        enrollment_id=str(prepared["enrollment_id"]),
        mentor_id=str(primary_mentor["mentor_id"]),
        provider_id=str(other_mentor["mentor_id"]),
    )
    monkeypatch.setenv("MENTOR_WORKSPACE_BACKFILL_REPAIR_ENABLED", "true")

    with caplog.at_level("WARNING", logger="swaif.runtime"):
        center_response = client.get("/mentor/centro-comando/alunos", headers=mentor_headers)

    assert center_response.status_code == 200
    assert any("mentor_workspace_backfill_conflicts_detected" in record.message for record in caplog.records)

    assignment = ProductAssignmentRepository().get_by_id(str(prepared["enrollment_id"]))
    assert assignment is not None
    assert assignment["mentor_id"] == primary_mentor["mentor_id"]
    assert assignment["provider_id"] == other_mentor["mentor_id"]
