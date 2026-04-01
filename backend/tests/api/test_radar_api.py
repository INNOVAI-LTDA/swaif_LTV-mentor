from pathlib import Path
import json

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
    monkeypatch.setenv("MEASUREMENT_OVERALL_STORE_PATH", str(tmp_path / "measurement_overalls.json"))


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _prepare_radar_data(client: TestClient, headers: dict[str, str]) -> str:
    org = client.post("/admin/mentorias", json={"name": "Mentoria Radar"}, headers=headers).json()
    org_id = org["id"]

    protocol = client.post("/admin/protocolos", json={"organization_id": org_id, "name": "Metodo Radar"}, headers=headers).json()
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

    student = client.post("/admin/alunos", json={"full_name": "Aluno Radar"}, headers=headers).json()
    student_id = student["id"]

    link = client.post(
        f"/admin/alunos/{student_id}/vincular-mentoria",
        json={"organization_id": org_id, "progress_score": 0.3, "engagement_score": 0.6},
        headers=headers,
    )
    assert link.status_code == 200

    load = client.post(
        f"/admin/alunos/{student_id}/indicadores/carga-inicial",
        json={
            "metric_values": [
                {"metric_id": metric_a["id"], "value_baseline": 50, "value_current": 70, "value_projected": 80},
                {"metric_id": metric_b["id"], "value_baseline": 40, "value_current": 60},
            ],
            "checkpoints": [],
        },
        headers=headers,
    )
    assert load.status_code == 200
    return student_id


def test_radar_endpoint_requires_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/admin/radar/alunos/std_1")
    assert response.status_code == 401


def test_radar_axis_scores_contract_and_averages(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    student_id = _prepare_radar_data(client, headers)

    response = client.get(f"/admin/radar/alunos/{student_id}", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert "axisScores" in payload
    assert len(payload["axisScores"]) == 2
    required = {"axisKey", "axisLabel", "axisSub", "baseline", "current", "projected", "insight"}
    assert required.issubset(set(payload["axisScores"][0].keys()))

    eixo_b = [axis for axis in payload["axisScores"] if axis["axisKey"] == "evolucao"][0]
    assert eixo_b["projected"] == eixo_b["current"]
    assert isinstance(eixo_b["insight"], str)
    assert eixo_b["insight"] != ""

    assert payload["avgBaseline"] == 45.0
    assert payload["avgCurrent"] == 65.0
    assert payload["avgProjected"] == 70.0


def test_radar_uses_measurement_overalls_when_available(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    student_id = _prepare_radar_data(client, headers)

    enrollments_payload = json.loads((tmp_path / "enrollments.json").read_text(encoding="utf-8"))
    enrollment_id = next(
        item["id"]
        for item in enrollments_payload.get("items", [])
        if item.get("student_id") == student_id
    )

    overalls_payload = {
        "version": 1,
        "items": [
            {
                "enrollment_id": enrollment_id,
                "protocol_id": "prt_test",
                "metrics": [],
                "pillars": [
                    {
                        "pillar_id": "plr_1",
                        "metric_average": {"goal": 1.0, "base": 0.2, "real": 0.4},
                    },
                    {
                        "pillar_id": "plr_2",
                        "metric_average": {"goal": 1.0, "base": 0.6, "real": 0.8},
                    },
                ],
                "decision_matrix": {
                    "product_score": 0.6,
                    "engagement_score": 0.7,
                    "thresholds": {"prd_thr": 0.7, "eng_thr": 0.7},
                },
            }
        ],
    }
    (tmp_path / "measurement_overalls.json").write_text(json.dumps(overalls_payload), encoding="utf-8")

    response = client.get(f"/admin/radar/alunos/{student_id}", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert len(payload["axisScores"]) == 2
    assert payload["avgBaseline"] == 0.4
    assert payload["avgCurrent"] == 0.6
    assert payload["avgProjected"] == 1.0
