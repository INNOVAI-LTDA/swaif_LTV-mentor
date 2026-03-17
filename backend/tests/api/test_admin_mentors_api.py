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


def test_admin_mentor_endpoints_require_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/admin/produtos/org_1/mentores")
    assert response.status_code == 401


def test_admin_lists_and_creates_mentors_by_product(monkeypatch, tmp_path: Path) -> None:
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

    empty_response = client.get(f"/admin/produtos/{product_id}/mentores", headers=headers)
    assert empty_response.status_code == 200
    assert empty_response.json() == []

    create_response = client.post(
        f"/admin/produtos/{product_id}/mentores",
        json={
            "full_name": "Ana Mentora",
            "cpf": "123.456.789-00",
            "email": "ana@swaif.local",
            "phone": "11999999999",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["organization_id"] == product_id
    assert created["cpf"] == "12345678900"

    list_response = client.get(f"/admin/produtos/{product_id}/mentores", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["full_name"] == "Ana Mentora"

    product_detail = client.get(f"/admin/clientes/{client_id}/produtos/{product_id}", headers=headers)
    assert product_detail.status_code == 200
    assert product_detail.json()["mentor_id"] == created["id"]


def test_admin_mentor_create_rejects_duplicate_cpf(monkeypatch, tmp_path: Path) -> None:
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
        f"/admin/produtos/{product_id}/mentores",
        json={"full_name": "Ana Mentora", "cpf": "12345678900", "email": "ana@swaif.local"},
        headers=headers,
    )
    assert first.status_code == 201

    duplicate = client.post(
        f"/admin/produtos/{product_id}/mentores",
        json={"full_name": "Bea Mentora", "cpf": "123.456.789-00", "email": "bea@swaif.local"},
        headers=headers,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "MENTOR_CONFLICT"
