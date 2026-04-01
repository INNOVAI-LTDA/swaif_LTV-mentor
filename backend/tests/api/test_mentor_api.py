from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.main import app
from app.storage.mentor_repository import MentorRepository
from app.storage.student_repository import StudentRepository
from app.storage.user_repository import UserRepository


def _configure_stores(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("USER_STORE_PATH", str(tmp_path / "users.json"))
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

    load = client.post(
        f"/admin/alunos/{primary_student['id']}/indicadores/carga-inicial",
        json={
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
        },
        headers=headers,
    )
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
        "student_id": str(primary_student["id"]),
        "hidden_student_id": str(hidden_student["id"]),
        "expected_day": expected_day,
        "expected_total_days": expected_total_days,
        "expected_days_left": expected_days_left,
    }


def test_mentor_routes_require_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/mentor/matriz-renovacao")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_MISSING_TOKEN"


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

    timeline_response = client.get(
        f"/mentor/centro-comando/alunos/{prepared['student_id']}/timeline-anomalias",
        headers=mentor_headers,
    )
    assert timeline_response.status_code == 200
    timeline = timeline_response.json()
    assert timeline["summary"]["hasAnomalies"] is True
    assert timeline["summary"]["anomalyCount"] >= 1