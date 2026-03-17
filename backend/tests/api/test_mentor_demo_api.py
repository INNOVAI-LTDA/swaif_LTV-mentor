from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _configure_stores(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("USER_STORE_PATH", str(tmp_path / "users.json"))


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_mentor_demo_requires_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/mentor/matriz-renovacao")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_MISSING_TOKEN"


def test_mentor_demo_is_visible_only_for_demo_mentor_login(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    admin_headers = {"Authorization": f"Bearer {_login(client, 'admin@swaif.local', 'admin123')}"}
    mentor_headers = {"Authorization": f"Bearer {_login(client, 'mentor@swaif.local', 'mentor123')}"}

    admin_response = client.get("/mentor/matriz-renovacao", headers=admin_headers)
    assert admin_response.status_code == 403
    assert admin_response.json()["error"]["code"] == "AUTH_FORBIDDEN"

    mentor_response = client.get("/mentor/matriz-renovacao", headers=mentor_headers)
    assert mentor_response.status_code == 200
    payload = mentor_response.json()
    assert payload["filter"] == "all"
    assert len(payload["items"]) == 10
    assert sum(1 for item in payload["items"] if item["quadrant"] == "topRight") == 3
    assert sum(1 for item in payload["items"] if item["quadrant"] == "topLeft") == 2
    assert sum(1 for item in payload["items"] if item["quadrant"] == "bottomRight") == 2
    assert sum(1 for item in payload["items"] if item["quadrant"] == "bottomLeft") == 3
    assert payload["kpis"]["rescueCount"] == 1
    assert all(item["programName"] == "Mentoria Acelerador M\u00e9dico" for item in payload["items"])


def test_mentor_demo_returns_student_detail_timeline_and_radar(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_login(client, 'mentor@swaif.local', 'mentor123')}"}

    students_response = client.get("/mentor/centro-comando/alunos", headers=headers)
    assert students_response.status_code == 200
    students = students_response.json()
    assert len(students) == 10

    student_id = students[0]["id"]

    detail_response = client.get(f"/mentor/centro-comando/alunos/{student_id}", headers=headers)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["programName"] == "Mentoria Acelerador M\u00e9dico"
    assert len(detail["metricValues"]) == 12
    assert len(detail["checkpoints"]) == 4

    timeline_response = client.get(f"/mentor/centro-comando/alunos/{student_id}/timeline-anomalias", headers=headers)
    assert timeline_response.status_code == 200
    timeline = timeline_response.json()
    assert timeline["studentId"] == student_id
    assert len(timeline["timeline"]) == 4

    radar_response = client.get(f"/mentor/radar/alunos/{student_id}", headers=headers)
    assert radar_response.status_code == 200
    radar = radar_response.json()
    assert radar["studentId"] == student_id
    assert len(radar["axisScores"]) == 5
    assert {axis["axisLabel"] for axis in radar["axisScores"]} == {
        "Posicionamento de Autoridade",
        "Conversao Comercial",
        "Operacao de Agenda",
        "Experiencia e Prova",
        "Escala e Recorrencia",
    }
