from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.main import create_app
from app.storage.analytical_history_repository import AnalyticalHistoryRepository
from app.storage.checkpoint_repository import CheckpointRepository
from app.storage.measurement_repository import MeasurementRepository
from app.storage.measurement_history_repository import MeasurementHistoryRepository
from app.storage.measurement_overall_repository import MeasurementOverallRepository
from app.storage.user_repository import UserRepository


def _configure_store_paths(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("SUPABASE_RUNTIME_REQUIRED", raising=False)
    monkeypatch.setenv("CLIENT_STORE_PATH", str(tmp_path / "clients.json"))
    monkeypatch.setenv("PRODUCT_STORE_PATH", str(tmp_path / "products.json"))
    monkeypatch.setenv("MENTOR_STORE_PATH", str(tmp_path / "mentors.json"))
    monkeypatch.setenv("PILLAR_STORE_PATH", str(tmp_path / "pillars.json"))
    monkeypatch.setenv("METRIC_STORE_PATH", str(tmp_path / "metrics.json"))
    monkeypatch.setenv("STUDENT_STORE_PATH", str(tmp_path / "students.json"))
    monkeypatch.setenv("ENROLLMENT_STORE_PATH", str(tmp_path / "enrollments.json"))
    monkeypatch.setenv("MEASUREMENT_STORE_PATH", str(tmp_path / "measurements.json"))
    monkeypatch.setenv("CHECKPOINT_STORE_PATH", str(tmp_path / "checkpoints.json"))
    monkeypatch.setenv("ORGANIZATION_STORE_PATH", str(tmp_path / "organizations.json"))
    monkeypatch.setenv("PROTOCOL_STORE_PATH", str(tmp_path / "protocols.json"))
    monkeypatch.setenv("USER_STORE_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(tmp_path / "contacts_users_v2.json"))
    monkeypatch.setenv("PRODUCT_ASSIGNMENT_STORE_PATH", str(tmp_path / "product_assignments.json"))
    monkeypatch.setenv("MEASUREMENT_OVERALL_STORE_PATH", str(tmp_path / "measurement_overalls.json"))
    monkeypatch.setenv("MEASUREMENT_HISTORY_STORE_PATH", str(tmp_path / "measurement_history.json"))
    monkeypatch.setenv("ANALYTICAL_HISTORY_STORE_PATH", str(tmp_path / "analytical_history.json"))


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _seed_workspace_data(client: TestClient, headers: dict[str, str]) -> tuple[str, str, str, str]:
    suffix = uuid4().hex[:8]

    org_response = client.post("/admin/mentorias", json={"name": f"Mentoria Aluno {suffix}"}, headers=headers)
    assert org_response.status_code == 201
    org = org_response.json()
    org_id = org["id"]

    protocol_response = client.post(
        "/admin/protocolos",
        json={"organization_id": org_id, "name": f"Metodo Aluno {suffix}"},
        headers=headers,
    )
    assert protocol_response.status_code == 201
    protocol = protocol_response.json()
    protocol_id = protocol["id"]

    pillar_response = client.post(
        "/admin/pilares",
        json={"protocol_id": protocol_id, "name": "Consistencia", "code": f"consistencia-{suffix}"},
        headers=headers,
    )
    assert pillar_response.status_code == 201
    pillar = pillar_response.json()
    pillar_id = pillar["id"]

    metric_a = client.post(
        "/admin/metricas",
        json={"protocol_id": protocol_id, "pillar_id": pillar_id, "name": "Ritmo", "code": "ritmo", "min_score": 0, "max_score": 10},
        headers=headers,
    ).json()
    metric_b = client.post(
        "/admin/metricas",
        json={"protocol_id": protocol_id, "pillar_id": pillar_id, "name": "Execucao", "code": "execucao", "min_score": 0, "max_score": 10},
        headers=headers,
    ).json()

    student = client.post(
        "/admin/alunos",
        json={"full_name": "Aluno Workspace", "email": "aluno.workspace@swaif.local"},
        headers=headers,
    ).json()
    student_id = student["id"]

    link = client.post(
        f"/admin/alunos/{student_id}/vincular-mentoria",
        json={
            "organization_id": org_id,
            "progress_score": 0.5,
            "engagement_score": 0.6,
            "urgency_status": "watch",
            "day": 10,
            "total_days": 100,
            "days_left": 90,
            "ltv_cents": 10000,
        },
        headers=headers,
    ).json()
    enrollment_id = link["id"]

    load_payload = {
        "metric_values": [
            {
                "metric_id": metric_a["id"],
                "value_baseline": 4,
                "value_current": 4,
                "value_projected": 5,
                "improving_trend": True,
            },
            {
                "metric_id": metric_b["id"],
                "value_baseline": 9,
                "value_current": 9,
                "value_projected": 9,
                "improving_trend": True,
            },
        ],
        "checkpoints": [{"week": 1, "status": "green", "label": "Inicio"}],
    }

    load = client.post(
        f"/admin/alunos/{student_id}/indicadores/carga-inicial",
        json=load_payload,
        headers=headers,
    )
    if load.status_code == 409:
        MeasurementRepository().replace_for_enrollment(enrollment_id, load_payload["metric_values"])
        CheckpointRepository().replace_for_enrollment(enrollment_id, load_payload["checkpoints"])
    else:
        assert load.status_code == 200

    MeasurementOverallRepository().generate_for_all_enrollments()

    return student_id, enrollment_id, pillar_id, str(pillar["code"])


def test_student_workspace_self_scoped_read_and_update(monkeypatch, tmp_path: Path) -> None:
    _configure_store_paths(monkeypatch, tmp_path)
    app = create_app()
    client = TestClient(app)

    admin_headers = {"Authorization": f"Bearer {_login(client, 'admin@swaif.local', 'admin123')}"}
    student_id, enrollment_id, pillar_id, pillar_code = _seed_workspace_data(client, admin_headers)

    user_repo = UserRepository()
    user_repo.create(
        id="usr_aluno_workspace",
        email="aluno.workspace@swaif.local",
        password_hash=hash_password("aluno123"),
        role="aluno",
        is_active=True,
    )

    aluno_headers = {"Authorization": f"Bearer {_login(client, 'aluno.workspace@swaif.local', 'aluno123')}"}

    radar = client.get("/aluno/workspace/radar", headers=aluno_headers)
    assert radar.status_code == 200
    radar_payload = radar.json()
    assert radar_payload["studentId"] == student_id
    assert len(radar_payload["pillarScores"]) == 1
    assert {"pillarId", "baseline", "current", "goal"}.issubset(set(radar_payload["pillarScores"][0].keys()))

    metric_scores = radar_payload["metricScoresByPillar"]
    assert len(metric_scores) == 1
    assert metric_scores[0]["pillarId"] == pillar_id
    assert len(metric_scores[0]["items"]) == 2
    assert {"metricId", "baseline", "current", "goal"}.issubset(set(metric_scores[0]["items"][0].keys()))

    metrics = client.get(f"/aluno/workspace/pilares/{pillar_id}/metricas", headers=aluno_headers)
    assert metrics.status_code == 200
    assert metrics.json()["enrollmentId"] == enrollment_id
    assert len(metrics.json()["items"]) == 2

    metrics_by_code = client.get(f"/aluno/workspace/pilares/{pillar_code}/metricas", headers=aluno_headers)
    assert metrics_by_code.status_code == 200
    assert metrics_by_code.json()["pillar"]["id"] == pillar_id
    assert len(metrics_by_code.json()["items"]) == 2

    measurement_id = metrics.json()["items"][0]["measurementId"]
    update = client.patch(
        f"/aluno/workspace/measurements/{measurement_id}",
        json={"value_current": 1},
        headers=aluno_headers,
    )
    assert update.status_code == 200
    assert update.json()["valueCurrent"] == 1.0

    reread = client.get(f"/aluno/workspace/pilares/{pillar_id}/metricas", headers=aluno_headers)
    current_values = [item["valueCurrent"] for item in reread.json()["items"]]
    assert 1.0 in current_values

    history_events = MeasurementHistoryRepository().list_by_measurement(measurement_id)
    assert len(history_events) == 1
    history_event = history_events[0]
    assert history_event["enrollment_id"] == enrollment_id
    assert history_event["actor_role"] == "client"
    assert history_event["value_absolute_before"] == 4.0
    assert history_event["value_absolute_after"] == 1.0

    analytical_events = AnalyticalHistoryRepository().list_by_enrollment(enrollment_id)
    analytical_event_types = {event["event_type"] for event in analytical_events}
    assert "assignment_score_snapshot" in analytical_event_types
    assert "decision_matrix_snapshot" in analytical_event_types
    assert "radar_axis_snapshot" in analytical_event_types

    product_events = AnalyticalHistoryRepository().list_by_product(
        next(
            item["organization_id"]
            for item in json.loads((tmp_path / "enrollments.json").read_text(encoding="utf-8"))["items"]
            if item["id"] == enrollment_id
        )
    )
    assert any(event["event_type"] == "product_radar_snapshot" for event in product_events)

    overall = MeasurementOverallRepository().get_by_enrollment(enrollment_id)
    assert overall is not None
    updated_pillar = next(
        pillar for pillar in overall["pillars"]
        if pillar["pillar_id"] == pillar_id
    )
    # Geometric mean(1, 9) = 3
    assert round(float(updated_pillar["metric_average"]["real"]), 3) == 3.0

    missing_pillar = client.get("/aluno/workspace/pilares/inexistente/metricas", headers=aluno_headers)
    assert missing_pillar.status_code == 404
    assert missing_pillar.json()["error"]["code"] == "ALUNO_RESOURCE_NOT_FOUND"


def test_student_workspace_rejects_non_aluno(monkeypatch, tmp_path: Path) -> None:
    _configure_store_paths(monkeypatch, tmp_path)
    app = create_app()
    client = TestClient(app)

    mentor_token = _login(client, "mentor@swaif.local", "mentor123")
    response = client.get("/aluno/workspace/radar", headers={"Authorization": f"Bearer {mentor_token}"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "AUTH_FORBIDDEN"


def test_student_workspace_runtime_requires_supabase_db_url_when_enforced(monkeypatch, tmp_path: Path) -> None:
    _configure_store_paths(monkeypatch, tmp_path)
    monkeypatch.setenv("SUPABASE_RUNTIME_REQUIRED", "true")
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)

    app = create_app()
    client = TestClient(app)

    UserRepository().create(
        id="usr_supabase_required_aluno",
        email="aluno@swaif.local",
        password_hash=hash_password("aluno123"),
        role="aluno",
        is_active=True,
    )

    token = _login(client, "aluno@swaif.local", "aluno123")
    response = client.get("/aluno/workspace/radar", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SUPABASE_DB_URL_REQUIRED"


def test_student_workspace_accepts_legacy_client_role(monkeypatch, tmp_path: Path) -> None:
    _configure_store_paths(monkeypatch, tmp_path)
    app = create_app()
    client = TestClient(app)

    admin_headers = {"Authorization": f"Bearer {_login(client, 'admin@swaif.local', 'admin123')}"}
    student_id, _, _, _ = _seed_workspace_data(client, admin_headers)

    user_repo = UserRepository()
    user_repo.create(
        id="usr_legacy_client_workspace",
        email="aluno.workspace@swaif.local",
        password_hash=hash_password("legacy123"),
        role="client",
        is_active=True,
    )

    legacy_token = _login(client, "aluno.workspace@swaif.local", "legacy123")
    response = client.get("/aluno/workspace/radar", headers={"Authorization": f"Bearer {legacy_token}"})

    assert response.status_code == 200
    assert response.json()["studentId"] == student_id


def test_student_workspace_fails_closed_for_ambiguous_student_context(monkeypatch, tmp_path: Path) -> None:
    _configure_store_paths(monkeypatch, tmp_path)

    students_path = tmp_path / "students.json"
    students_path.write_text(
        json.dumps(
            {
                "version": 1,
                "items": [
                    {"id": "std_1", "full_name": "Aluno A", "email": "dup@swaif.local", "is_active": True},
                    {"id": "std_2", "full_name": "Aluno B", "email": "dup@swaif.local", "is_active": True},
                ],
            }
        ),
        encoding="utf-8",
    )

    app = create_app()
    client = TestClient(app)

    user_repo = UserRepository()
    user_repo.create(
        id="usr_dup_ctx",
        email="dup@swaif.local",
        password_hash=hash_password("dup123"),
        role="aluno",
        is_active=True,
    )

    token = _login(client, "dup@swaif.local", "dup123")
    response = client.get("/aluno/workspace/radar", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ALUNO_CONTEXT_NOT_FOUND"


def test_student_workspace_rejects_pillar_out_of_scope(monkeypatch, tmp_path: Path) -> None:
    _configure_store_paths(monkeypatch, tmp_path)
    app = create_app()
    client = TestClient(app)

    admin_headers = {"Authorization": f"Bearer {_login(client, 'admin@swaif.local', 'admin123')}"}
    _, _, _, _ = _seed_workspace_data(client, admin_headers)

    org_response = client.post("/admin/mentorias", json={"name": f"Mentoria Extra {uuid4().hex[:6]}"}, headers=admin_headers)
    assert org_response.status_code == 201
    org_id = org_response.json()["id"]

    protocol_response = client.post(
        "/admin/protocolos",
        json={"organization_id": org_id, "name": f"Metodo Extra {uuid4().hex[:6]}"},
        headers=admin_headers,
    )
    assert protocol_response.status_code == 201
    protocol_id = protocol_response.json()["id"]

    foreign_pillar_response = client.post(
        "/admin/pilares",
        json={"protocol_id": protocol_id, "name": "Pilar Externo", "code": f"externo-{uuid4().hex[:6]}"},
        headers=admin_headers,
    )
    assert foreign_pillar_response.status_code == 201
    foreign_pillar_id = foreign_pillar_response.json()["id"]

    user_repo = UserRepository()
    user_repo.create(
        id="usr_scope_ctx",
        email="aluno.workspace@swaif.local",
        password_hash=hash_password("scope123"),
        role="aluno",
        is_active=True,
    )

    token = _login(client, "aluno.workspace@swaif.local", "scope123")
    response = client.get(f"/aluno/workspace/pilares/{foreign_pillar_id}/metricas", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "MEASUREMENT_FORBIDDEN"


def test_student_workspace_allows_empty_metrics_for_in_scope_pillar(monkeypatch, tmp_path: Path) -> None:
    _configure_store_paths(monkeypatch, tmp_path)
    app = create_app()
    client = TestClient(app)

    admin_headers = {"Authorization": f"Bearer {_login(client, 'admin@swaif.local', 'admin123')}"}
    _, enrollment_id, _, _ = _seed_workspace_data(client, admin_headers)

    enrollment = next(
        item
        for item in client.get("/admin/matriz-renovacao", headers=admin_headers).json()["items"]
        if item["enrollmentId"] == enrollment_id
    )
    protocol_id = enrollment["protocolId"]

    second_pillar = client.post(
        "/admin/pilares",
        json={"protocol_id": protocol_id, "name": "Pilar Sem Medicao", "code": f"sem-medicao-{uuid4().hex[:6]}"},
        headers=admin_headers,
    )
    assert second_pillar.status_code == 201
    second_pillar_id = second_pillar.json()["id"]

    user_repo = UserRepository()
    user_repo.create(
        id="usr_empty_scope",
        email="aluno.workspace@swaif.local",
        password_hash=hash_password("scope-empty123"),
        role="aluno",
        is_active=True,
    )

    token = _login(client, "aluno.workspace@swaif.local", "scope-empty123")
    response = client.get(
        f"/aluno/workspace/pilares/{second_pillar_id}/metricas",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["enrollmentId"] == enrollment_id
    assert body["pillar"]["id"] == second_pillar_id
    assert body["items"] == []
