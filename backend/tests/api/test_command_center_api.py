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


def _prepare_center_data(client: TestClient, headers: dict[str, str]) -> tuple[str, str, str]:
    mentoria_response = client.post(
        "/admin/mentorias",
        json={"name": "Mentoria Centro"},
        headers=headers,
    )
    assert mentoria_response.status_code == 201
    organization_id = mentoria_response.json()["id"]

    protocol_response = client.post(
        "/admin/protocolos",
        json={"organization_id": organization_id, "name": "Metodo Centro"},
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
    metric_id = metric_response.json()["id"]

    student_a = client.post("/admin/alunos", json={"full_name": "Aluno A"}, headers=headers).json()
    student_b = client.post("/admin/alunos", json={"full_name": "Aluno B"}, headers=headers).json()

    link_a = client.post(
        f"/admin/alunos/{student_a['id']}/vincular-mentoria",
        json={
            "organization_id": organization_id,
            "progress_score": 0.2,
            "engagement_score": 0.0,
            "day": 45,
            "total_days": 90,
            "days_left": 45,
        },
        headers=headers,
    )
    assert link_a.status_code == 200

    link_b = client.post(
        f"/admin/alunos/{student_b['id']}/vincular-mentoria",
        json={
            "organization_id": organization_id,
            "progress_score": 0.4,
            "engagement_score": 0.7,
            "day": 0,
            "total_days": 0,
            "days_left": 80,
        },
        headers=headers,
    )
    assert link_b.status_code == 200

    load_a = client.post(
        f"/admin/alunos/{student_a['id']}/indicadores/carga-inicial",
        json={
            "metric_values": [{"metric_id": metric_id, "value_baseline": 55, "value_current": 60}],
            "checkpoints": [{"week": 1, "status": "green", "label": "Inicio"}],
        },
        headers=headers,
    )
    assert load_a.status_code == 200
    return student_a["id"], student_b["id"], metric_id


def test_center_endpoints_require_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/admin/centro-comando/alunos")
    assert response.status_code == 401


def test_center_list_and_detail_contracts(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    student_a, student_b, _ = _prepare_center_data(client, headers)

    list_response = client.get("/admin/centro-comando/alunos", headers=headers)
    assert list_response.status_code == 200
    payload = list_response.json()
    items = payload["items"]
    assert len(items) == 2
    assert payload["rankingMode"] == "full"
    assert payload["totalStudents"] == 2
    required = {"id", "name", "programName", "urgency", "daysLeft", "day", "totalDays", "engagement", "progress", "hormoziScore"}
    assert required.issubset(set(items[0].keys()))

    by_id = {item["id"]: item for item in items}
    assert by_id[student_a]["d45"] is True
    assert by_id[student_a]["daysLeft"] == 45
    assert by_id[student_a]["urgency"] in {"critical", "rescue"}
    assert by_id[student_b]["totalDays"] == 0
    assert by_id[student_b]["progress"] == 0.4

    detail_response = client.get(f"/admin/centro-comando/alunos/{student_a}", headers=headers)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == student_a
    assert "metricValues" in detail
    assert "checkpoints" in detail
    assert detail["progress"] == 0.5


def test_center_timeline_anomalies_contract(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    student_a, _, metric_id = _prepare_center_data(client, headers)

    reload_with_anomaly = client.post(
        f"/admin/alunos/{student_a}/indicadores/carga-inicial",
        json={
            "metric_values": [
                {
                    "metric_id": metric_id,
                    "value_baseline": 80,
                    "value_current": 52,
                    "value_projected": 65,
                    "improving_trend": False,
                }
            ],
            "checkpoints": [
                {"week": 2, "status": "yellow", "label": "Oscilacao detectada"},
                {"week": 4, "status": "red", "label": "Bloqueio de execucao"},
            ],
        },
        headers=headers,
    )
    assert reload_with_anomaly.status_code == 200

    response = client.get(
        f"/admin/centro-comando/alunos/{student_a}/timeline-anomalias",
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()

    assert body["studentId"] == student_a
    assert isinstance(body["timeline"], list)
    assert isinstance(body["anomalies"], list)
    assert {"anomalyCount", "hasAnomalies"}.issubset(set(body["summary"].keys()))
    assert body["summary"]["hasAnomalies"] is True
    assert body["summary"]["anomalyCount"] >= 1

    timeline_entry = body["timeline"][0]
    assert {"week", "label", "status", "anomaly"}.issubset(set(timeline_entry.keys()))
    anomaly = body["anomalies"][0]
    assert {"marker", "value", "ref", "cause", "action"}.issubset(set(anomaly.keys()))


def test_center_returns_top_and_bottom_10_when_over_20_students(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    org_response = client.post("/admin/mentorias", json={"name": "Mentoria Ranking"}, headers=headers)
    assert org_response.status_code == 201
    organization_id = org_response.json()["id"]

    student_ids: list[str] = []
    for idx in range(22):
        student = client.post(
            "/admin/alunos",
            json={"full_name": f"Aluno {idx:02d}"},
            headers=headers,
        ).json()
        student_ids.append(student["id"])
        link = client.post(
            f"/admin/alunos/{student['id']}/vincular-mentoria",
            json={
                "organization_id": organization_id,
                "progress_score": 0.4,
                "engagement_score": 0.4,
                "day": 10,
                "total_days": 100,
                "days_left": 90,
            },
            headers=headers,
        )
        assert link.status_code == 200

    enrollments_payload = json.loads((tmp_path / "enrollments.json").read_text(encoding="utf-8"))
    enrollments = enrollments_payload.get("items", [])
    by_student_id = {str(row.get("student_id")): str(row.get("id")) for row in enrollments}

    overalls_items = []
    for idx, student_id in enumerate(student_ids):
        enrollment_id = by_student_id[student_id]
        score = idx / 21
        overalls_items.append(
            {
                "enrollment_id": enrollment_id,
                "protocol_id": "prt_test",
                "metrics": [],
                "pillars": [
                    {
                        "pillar_id": "plr_test",
                        "metric_average": {"goal": 1.0, "base": score, "real": score},
                    }
                ],
                "decision_matrix": {
                    "product_score": score,
                    "engagement_score": score,
                    "thresholds": {"prd_thr": 0.7, "eng_thr": 0.7},
                },
            }
        )

    (tmp_path / "measurement_overalls.json").write_text(
        json.dumps({"version": 1, "items": overalls_items}),
        encoding="utf-8",
    )

    response = client.get("/admin/centro-comando/alunos", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    items = payload["items"]
    assert len(items) == 20
    assert payload["rankingMode"] == "top_bottom"
    assert payload["totalStudents"] == 22
    assert len(payload["topItems"]) == 10
    assert len(payload["bottomItems"]) == 10

    returned_ids = [str(item["id"]) for item in items]
    excluded_ids = {student_ids[10], student_ids[11]}
    assert excluded_ids.isdisjoint(set(returned_ids))
    assert student_ids[21] in returned_ids
    assert student_ids[0] in returned_ids
