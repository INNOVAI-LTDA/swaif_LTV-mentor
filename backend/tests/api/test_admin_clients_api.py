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
    monkeypatch.setenv("CLIENT_STORE_PATH", str(tmp_path / "clients.json"))
    monkeypatch.setenv("ORG_STORE_PATH", str(tmp_path / "organizations.json"))
    monkeypatch.setenv("MENTOR_STORE_PATH", str(tmp_path / "mentors.json"))
    monkeypatch.setenv("PROTOCOL_STORE_PATH", str(tmp_path / "protocols.json"))
    monkeypatch.setenv("PILLAR_STORE_PATH", str(tmp_path / "pillars.json"))
    monkeypatch.setenv("METRIC_STORE_PATH", str(tmp_path / "metrics.json"))
    monkeypatch.setenv("STUDENT_STORE_PATH", str(tmp_path / "students.json"))
    monkeypatch.setenv("ENROLLMENT_STORE_PATH", str(tmp_path / "enrollments.json"))
    monkeypatch.setenv("MEASUREMENT_STORE_PATH", str(tmp_path / "measurements.json"))
    monkeypatch.setenv("CHECKPOINT_STORE_PATH", str(tmp_path / "checkpoints.json"))


def test_admin_client_endpoints_require_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/admin/clientes")
    assert response.status_code == 401


def test_admin_lists_creates_and_reads_clients(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    empty_response = client.get("/admin/clientes", headers=headers)
    assert empty_response.status_code == 200
    assert empty_response.json() == []

    create_response = client.post(
        "/admin/clientes",
        json={
            "name": "Clinica Horizonte",
            "brand_name": "Horizonte",
            "cnpj": "12.345.678/0001-99",
            "slug": "clinica-horizonte",
            "timezone": "America/Sao_Paulo",
            "currency": "BRL",
            "notes": "Cliente prioritario do bloco 1",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] == "cli_1"
    assert created["cnpj"] == "12345678000199"

    list_response = client.get("/admin/clientes", headers=headers)
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["brand_name"] == "Horizonte"

    detail_response = client.get(f"/admin/clientes/{created['id']}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["notes"] == "Cliente prioritario do bloco 1"


def test_admin_client_create_rejects_duplicate_cnpj(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    first = client.post(
        "/admin/clientes",
        json={"name": "Clinica Horizonte", "cnpj": "12345678000199"},
        headers=headers,
    )
    assert first.status_code == 201

    duplicate = client.post(
        "/admin/clientes",
        json={"name": "Clinica Horizonte 2", "cnpj": "12345678000199"},
        headers=headers,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "CLIENTE_CONFLICT"
