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
    monkeypatch.setenv("METRIC_STORE_PATH", str(tmp_path / "metrics.json"))


def test_admin_metric_endpoints_require_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/admin/pilares/plr_1/metricas")
    assert response.status_code == 401


def test_admin_lists_and_creates_metrics_by_pillar(monkeypatch, tmp_path: Path) -> None:
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

    pillar_response = client.post(
        f"/admin/produtos/{product_id}/pilares",
        json={"name": "Performance", "order_index": 1},
        headers=headers,
    )
    pillar_id = pillar_response.json()["id"]

    empty_response = client.get(f"/admin/pilares/{pillar_id}/metricas", headers=headers)
    assert empty_response.status_code == 200
    assert empty_response.json() == []

    create_response = client.post(
        f"/admin/pilares/{pillar_id}/metricas",
        json={"name": "Comparecimento", "code": "comparecimento", "direction": "higher_better", "unit": "%"},
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["pillar_id"] == pillar_id
    assert created["unit"] == "%"

    list_response = client.get(f"/admin/pilares/{pillar_id}/metricas", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["name"] == "Comparecimento"

    product_list = client.get(f"/admin/produtos/{product_id}/metricas", headers=headers)
    assert product_list.status_code == 200
    assert len(product_list.json()) == 1
    assert product_list.json()[0]["name"] == "Comparecimento"


def test_admin_metric_create_rejects_duplicate_code_in_same_pillar(monkeypatch, tmp_path: Path) -> None:
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

    pillar_response = client.post(
        f"/admin/produtos/{product_id}/pilares",
        json={"name": "Performance", "order_index": 1},
        headers=headers,
    )
    pillar_id = pillar_response.json()["id"]

    first = client.post(
        f"/admin/pilares/{pillar_id}/metricas",
        json={"name": "Comparecimento", "code": "comparecimento"},
        headers=headers,
    )
    assert first.status_code == 201

    duplicate = client.post(
        f"/admin/pilares/{pillar_id}/metricas",
        json={"name": "Presenca", "code": "comparecimento"},
        headers=headers,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "METRICA_CONFLICT"
