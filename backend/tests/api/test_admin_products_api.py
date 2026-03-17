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


def test_admin_product_endpoints_require_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/admin/clientes/cli_1/produtos")
    assert response.status_code == 401


def test_admin_lists_creates_and_reads_products_by_client(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    client_response = client.post(
        "/admin/clientes",
        json={"name": "Clinica Horizonte", "cnpj": "12345678000199"},
        headers=headers,
    )
    assert client_response.status_code == 201
    client_id = client_response.json()["id"]

    empty_response = client.get(f"/admin/clientes/{client_id}/produtos", headers=headers)
    assert empty_response.status_code == 200
    assert empty_response.json() == []

    create_response = client.post(
        f"/admin/clientes/{client_id}/produtos",
        json={
            "name": "Acelerador Medico Premium",
            "code": "AMP-PREMIUM",
            "slug": "acelerador-medico-premium",
            "description": "Produto premium do cliente",
            "delivery_model": "live",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["client_id"] == client_id
    assert created["code"] == "AMP-PREMIUM"

    list_response = client.get(f"/admin/clientes/{client_id}/produtos", headers=headers)
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["name"] == "Acelerador Medico Premium"

    detail_response = client.get(f"/admin/clientes/{client_id}/produtos/{created['id']}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["description"] == "Produto premium do cliente"


def test_admin_product_create_rejects_duplicate_code_per_client(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    client_response = client.post(
        "/admin/clientes",
        json={"name": "Clinica Horizonte", "cnpj": "12345678000199"},
        headers=headers,
    )
    assert client_response.status_code == 201
    client_id = client_response.json()["id"]

    first = client.post(
        f"/admin/clientes/{client_id}/produtos",
        json={"name": "Acelerador Medico Premium", "code": "AMP-PREMIUM"},
        headers=headers,
    )
    assert first.status_code == 201

    duplicate = client.post(
        f"/admin/clientes/{client_id}/produtos",
        json={"name": "Outro Produto", "code": "AMP-PREMIUM"},
        headers=headers,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "PRODUTO_CONFLICT"
