from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


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


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _prepare_student_and_metric(client: TestClient, headers: dict[str, str]) -> tuple[str, str]:
    mentoria_response = client.post("/admin/mentorias", json={"name": "Mentoria Indicadores"}, headers=headers)
    assert mentoria_response.status_code == 201
    organization_id = mentoria_response.json()["id"]

    student_response = client.post("/admin/alunos", json={"full_name": "Aluno Indicadores"}, headers=headers)
    assert student_response.status_code == 201
    student_id = student_response.json()["id"]

    link_response = client.post(
        f"/admin/alunos/{student_id}/vincular-mentoria",
        json={"organization_id": organization_id, "progress_score": 0.35, "engagement_score": 0.6},
        headers=headers,
    )
    assert link_response.status_code == 200

    protocol_response = client.post(
        "/admin/protocolos",
        json={"organization_id": organization_id, "name": "Metodo Indicadores"},
        headers=headers,
    )
    assert protocol_response.status_code == 201
    protocol_id = protocol_response.json()["id"]

    pillar_response = client.post(
        "/admin/pilares",
        json={"protocol_id": protocol_id, "name": "Compromisso"},
        headers=headers,
    )
    assert pillar_response.status_code == 201
    pillar_id = pillar_response.json()["id"]

    metric_response = client.post(
        "/admin/metricas",
        json={"protocol_id": protocol_id, "pillar_id": pillar_id, "name": "Frequencia", "unit": "%"},
        headers=headers,
    )
    assert metric_response.status_code == 201
    return student_id, metric_response.json()["id"]


def test_indicator_load_requires_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.post(
        "/admin/alunos/std_1/indicadores/carga-inicial",
        json={"metric_values": [], "checkpoints": []},
    )
    assert response.status_code == 401


def test_admin_can_load_initial_indicators_and_read_student_detail(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    student_id, metric_id = _prepare_student_and_metric(client, headers)

    load_response = client.post(
        f"/admin/alunos/{student_id}/indicadores/carga-inicial",
        json={
            "metric_values": [
                {"metric_id": metric_id, "value_baseline": 55, "value_current": 68, "value_projected": 75, "improving_trend": True}
            ],
            "checkpoints": [
                {"week": 1, "status": "green", "label": "Inicio consistente"},
                {"week": 2, "status": "yellow", "label": "Ajustar rotina"},
            ],
        },
        headers=headers,
    )
    assert load_response.status_code == 200
    assert load_response.json()["measurement_count"] == 1
    assert load_response.json()["checkpoint_count"] == 2

    detail_response = client.get(f"/admin/alunos/{student_id}/detalhe", headers=headers)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == student_id
    assert len(detail["metricValues"]) == 1
    assert detail["metricValues"][0]["valueCurrent"] == 68
    assert len(detail["checkpoints"]) == 2


def test_indicator_load_rejects_non_registered_metric(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    student_id, _ = _prepare_student_and_metric(client, headers)

    load_response = client.post(
        f"/admin/alunos/{student_id}/indicadores/carga-inicial",
        json={
            "metric_values": [{"metric_id": "met_missing", "value_baseline": 10, "value_current": 15}],
            "checkpoints": [],
        },
        headers=headers,
    )
    assert load_response.status_code == 404


def test_indicator_load_rejects_inactive_metric(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    student_id, metric_id = _prepare_student_and_metric(client, headers)

    metric_store = tmp_path / "metrics.json"
    content = metric_store.read_text(encoding="utf-8")
    metric_store.write_text(content.replace('"is_active": true', '"is_active": false', 1), encoding="utf-8")

    load_response = client.post(
        f"/admin/alunos/{student_id}/indicadores/carga-inicial",
        json={
            "metric_values": [{"metric_id": metric_id, "value_baseline": 10, "value_current": 15}],
            "checkpoints": [],
        },
        headers=headers,
    )
    assert load_response.status_code == 404
