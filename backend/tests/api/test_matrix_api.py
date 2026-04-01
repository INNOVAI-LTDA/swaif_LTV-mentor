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


def _prepare_matrix_data(client: TestClient, headers: dict[str, str]) -> None:
    org = client.post("/admin/mentorias", json={"name": "Mentoria Matriz"}, headers=headers).json()
    org_id = org["id"]

    protocol = client.post("/admin/protocolos", json={"organization_id": org_id, "name": "Metodo Matriz"}, headers=headers).json()
    protocol_id = protocol["id"]
    pillar = client.post("/admin/pilares", json={"protocol_id": protocol_id, "name": "Compromisso"}, headers=headers).json()
    metric = client.post(
        "/admin/metricas",
        json={"protocol_id": protocol_id, "pillar_id": pillar["id"], "name": "Frequencia"},
        headers=headers,
    ).json()

    def create_student(name: str, progress: float, engagement: float, day: int, total_days: int, days_left: int, ltv_cents: int):
        student = client.post("/admin/alunos", json={"full_name": name}, headers=headers).json()
        link = client.post(
            f"/admin/alunos/{student['id']}/vincular-mentoria",
            json={
                "organization_id": org_id,
                "progress_score": progress,
                "engagement_score": engagement,
                "day": day,
                "total_days": total_days,
                "days_left": days_left,
                "ltv_cents": ltv_cents,
            },
            headers=headers,
        )
        assert link.status_code == 200
        load = client.post(
            f"/admin/alunos/{student['id']}/indicadores/carga-inicial",
            json={"metric_values": [{"metric_id": metric["id"], "value_baseline": 50, "value_current": 60}], "checkpoints": []},
            headers=headers,
        )
        assert load.status_code == 200

    create_student("Aluno TopRight", progress=0.7, engagement=0.8, day=70, total_days=100, days_left=40, ltv_cents=100000)
    create_student("Aluno TopLeft", progress=0.4, engagement=0.7, day=40, total_days=100, days_left=80, ltv_cents=50000)
    create_student("Aluno Rescue", progress=0.7, engagement=0.05, day=70, total_days=100, days_left=30, ltv_cents=70000)
    create_student("Aluno TopRight 2", progress=0.8, engagement=0.65, day=80, total_days=100, days_left=20, ltv_cents=30000)


def test_matrix_endpoint_requires_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/admin/matriz-renovacao")
    assert response.status_code == 401


def test_matrix_contract_kpis_and_filters(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    _prepare_matrix_data(client, headers)

    all_response = client.get("/admin/matriz-renovacao?filter=all", headers=headers)
    assert all_response.status_code == 200
    payload = all_response.json()
    assert payload["filter"] == "all"
    assert len(payload["items"]) == 4
    required = {
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
    assert required.issubset(set(payload["items"][0].keys()))
    assert {"totalLTV", "criticalRenewals", "rescueCount", "avgEngagement"}.issubset(set(payload["kpis"].keys()))

    top_right = client.get("/admin/matriz-renovacao?filter=topRight", headers=headers).json()
    assert len(top_right["items"]) == 1
    assert all(item["quadrant"] == "topRight" for item in top_right["items"])

    critical = client.get("/admin/matriz-renovacao?filter=critical", headers=headers).json()
    assert len(critical["items"]) == 1
    assert all(item["daysLeft"] <= 45 and item["quadrant"] == "topRight" for item in critical["items"])

    rescue = client.get("/admin/matriz-renovacao?filter=rescue", headers=headers).json()
    assert len(rescue["items"]) == 1
    assert rescue["items"][0]["urgency"] == "rescue"


def test_matrix_uses_measurement_overall_decision_matrix(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    _prepare_matrix_data(client, headers)

    enrollments_payload = json.loads((tmp_path / "enrollments.json").read_text(encoding="utf-8"))
    first_enrollment = enrollments_payload["items"][0]
    enrollment_id = first_enrollment["id"]

    overalls_payload = {
        "version": 1,
        "items": [
            {
                "enrollment_id": enrollment_id,
                "protocol_id": "prt_test",
                "metrics": [],
                "pillars": [],
                "decision_matrix": {
                    "product_score": 0.71,
                    "engagement_score": 0.69,
                    "thresholds": {"prd_thr": 0.7, "eng_thr": 0.7},
                },
            }
        ],
    }
    (tmp_path / "measurement_overalls.json").write_text(json.dumps(overalls_payload), encoding="utf-8")

    response = client.get("/admin/matriz-renovacao?filter=all", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    by_id = {item["id"]: item for item in payload["items"]}
    student_id = first_enrollment["student_id"]
    assert by_id[student_id]["progress"] == 0.71
    assert by_id[student_id]["engagement"] == 0.69
    assert by_id[student_id]["quadrant"] == "bottomRight"
