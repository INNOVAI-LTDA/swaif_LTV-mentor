from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _configure_stores(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("USER_STORE_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("ORG_STORE_PATH", str(tmp_path / "organizations.json"))
    monkeypatch.setenv("MENTOR_STORE_PATH", str(tmp_path / "mentors.json"))


def test_admin_endpoints_require_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.post("/admin/mentorias", json={"name": "Mentoria Sem Auth"})
    assert response.status_code == 401


def test_only_admin_can_create_mentoria(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    mentor_token = _login(client, "mentor@swaif.local", "mentor123")

    response = client.post(
        "/admin/mentorias",
        json={"name": "Mentoria Restrita"},
        headers={"Authorization": f"Bearer {mentor_token}"},
    )
    assert response.status_code == 403


def test_admin_creates_mentor_and_links_to_mentoria(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    mentoria_response = client.post(
        "/admin/mentorias",
        json={"name": "Mentoria Gamma", "slug": "mentoria-gamma"},
        headers=headers,
    )
    assert mentoria_response.status_code == 201
    mentoria_id = mentoria_response.json()["id"]

    mentor_response = client.post(
        "/admin/mentores",
        json={"full_name": "Carla Mentora", "email": "carla@swaif.local"},
        headers=headers,
    )
    assert mentor_response.status_code == 201
    mentor_id = mentor_response.json()["id"]

    link_response = client.post(
        f"/admin/mentorias/{mentoria_id}/vincular-mentor",
        json={"mentor_id": mentor_id},
        headers=headers,
    )
    assert link_response.status_code == 200
    assert link_response.json()["mentor_id"] == mentor_id

    detail_response = client.get(f"/admin/mentorias/{mentoria_id}", headers=headers)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["mentor_id"] == mentor_id
    assert detail["mentor"]["id"] == mentor_id
