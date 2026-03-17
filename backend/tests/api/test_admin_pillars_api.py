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
    monkeypatch.setenv("PROTOCOL_STORE_PATH", str(tmp_path / "protocols.json"))
    monkeypatch.setenv("PILLAR_STORE_PATH", str(tmp_path / "pillars.json"))


def test_admin_pillar_endpoints_require_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/admin/produtos/org_1/pilares")
    assert response.status_code == 401


def test_admin_lists_and_creates_pillars_by_product(monkeypatch, tmp_path: Path) -> None:
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

    product_response = client.post(
        f"/admin/clientes/{client_id}/produtos",
        json={"name": "Acelerador Medico Premium", "code": "AMP-PREMIUM"},
        headers=headers,
    )
    assert product_response.status_code == 201
    product_id = product_response.json()["id"]

    empty_response = client.get(f"/admin/produtos/{product_id}/pilares", headers=headers)
    assert empty_response.status_code == 200
    assert empty_response.json() == []

    create_response = client.post(
        f"/admin/produtos/{product_id}/pilares",
        json={"name": "Performance", "order_index": 1},
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "Performance"
    assert created["protocol_id"] == "prt_1"

    second_response = client.post(
        f"/admin/produtos/{product_id}/pilares",
        json={"name": "Retencao", "order_index": 2},
        headers=headers,
    )
    assert second_response.status_code == 201
    assert second_response.json()["protocol_id"] == "prt_1"

    list_response = client.get(f"/admin/produtos/{product_id}/pilares", headers=headers)
    assert list_response.status_code == 200
    assert [item["name"] for item in list_response.json()] == ["Performance", "Retencao"]


def test_admin_pillar_create_rejects_duplicate_code(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    client_response = client.post(
        "/admin/clientes",
        json={"name": "Clinica Horizonte", "cnpj": "12345678000199"},
        headers=headers,
    )
    client_id = client_response.json()["id"]

    product_response = client.post(
        f"/admin/clientes/{client_id}/produtos",
        json={"name": "Acelerador Medico Premium", "code": "AMP-PREMIUM"},
        headers=headers,
    )
    product_id = product_response.json()["id"]

    first = client.post(
        f"/admin/produtos/{product_id}/pilares",
        json={"name": "Performance"},
        headers=headers,
    )
    assert first.status_code == 201

    duplicate = client.post(
        f"/admin/produtos/{product_id}/pilares",
        json={"name": "Performance"},
        headers=headers,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "PILAR_CONFLICT"
