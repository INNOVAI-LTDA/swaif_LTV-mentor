from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.main import create_app
from app.storage.measurement_overall_repository import MeasurementOverallRepository
from app.storage.user_repository import UserRepository


def _configure_store_paths(monkeypatch, tmp_path: Path) -> None:
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
    monkeypatch.setenv("MEASUREMENT_OVERALL_STORE_PATH", str(tmp_path / "measurement_overalls.json"))


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _seed_workspace_data(client: TestClient, headers: dict[str, str]) -> tuple[str, str, str]:
    org = client.post("/admin/mentorias", json={"name": "Mentoria Aluno"}, headers=headers).json()
    org_id = org["id"]

    protocol = client.post(
        "/admin/protocolos",
        json={"organization_id": org_id, "name": "Metodo Aluno"},
        headers=headers,
    ).json()
    protocol_id = protocol["id"]

    pillar = client.post(
        "/admin/pilares",
        json={"protocol_id": protocol_id, "name": "Consistencia", "code": "consistencia"},
        headers=headers,
    ).json()
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

    load = client.post(
        f"/admin/alunos/{student_id}/indicadores/carga-inicial",
        json={
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
        },
        headers=headers,
    )
    assert load.status_code == 200

    MeasurementOverallRepository().generate_for_all_enrollments()

    return student_id, enrollment_id, pillar_id


def test_student_workspace_self_scoped_read_and_update(monkeypatch, tmp_path: Path) -> None:
    _configure_store_paths(monkeypatch, tmp_path)
    app = create_app()
    client = TestClient(app)

    admin_headers = {"Authorization": f"Bearer {_login(client, 'admin@swaif.local', 'admin123')}"}
    student_id, enrollment_id, pillar_id = _seed_workspace_data(client, admin_headers)

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
    assert radar.json()["studentId"] == student_id

    metrics = client.get(f"/aluno/workspace/pilares/{pillar_id}/metricas", headers=aluno_headers)
    assert metrics.status_code == 200
    assert metrics.json()["enrollmentId"] == enrollment_id
    assert len(metrics.json()["items"]) == 2

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

    overall = MeasurementOverallRepository().get_by_enrollment(enrollment_id)
    assert overall is not None
    updated_pillar = next(
        pillar for pillar in overall["pillars"]
        if pillar["pillar_id"] == pillar_id
    )
    # Geometric mean(1, 9) = 3
    assert round(float(updated_pillar["metric_average"]["real"]), 3) == 3.0


def test_student_workspace_rejects_non_aluno(monkeypatch, tmp_path: Path) -> None:
    _configure_store_paths(monkeypatch, tmp_path)
    app = create_app()
    client = TestClient(app)

    mentor_token = _login(client, "mentor@swaif.local", "mentor123")
    response = client.get("/aluno/workspace/radar", headers={"Authorization": f"Bearer {mentor_token}"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "AUTH_FORBIDDEN"
