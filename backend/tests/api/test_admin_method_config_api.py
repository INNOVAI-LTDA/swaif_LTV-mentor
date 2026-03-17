from pathlib import Path

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


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_admin_method_endpoints_require_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.post(
        "/admin/protocolos",
        json={"organization_id": "org_1", "name": "Metodo Sem Auth"},
    )
    assert response.status_code == 401


def test_admin_can_configure_protocol_pillar_metric(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    protocol_response = client.post(
        "/admin/protocolos",
        json={"organization_id": "org_1", "name": "Metodo Premium", "code": "metodo-premium"},
        headers=headers,
    )
    assert protocol_response.status_code == 201
    protocol_id = protocol_response.json()["id"]

    pillar_response = client.post(
        "/admin/pilares",
        json={"protocol_id": protocol_id, "name": "Frequencia", "code": "frequencia", "order_index": 1},
        headers=headers,
    )
    assert pillar_response.status_code == 201
    pillar_id = pillar_response.json()["id"]

    metric_response = client.post(
        "/admin/metricas",
        json={
            "protocol_id": protocol_id,
            "pillar_id": pillar_id,
            "name": "Comparecimento",
            "code": "comparecimento",
            "direction": "higher_better",
            "unit": "%",
        },
        headers=headers,
    )
    assert metric_response.status_code == 201
    assert metric_response.json()["pillar_id"] == pillar_id


def test_admin_metric_consistency_error(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    protocol_a = client.post(
        "/admin/protocolos",
        json={"organization_id": "org_1", "name": "Metodo A", "code": "metodo-a"},
        headers=headers,
    ).json()
    protocol_b = client.post(
        "/admin/protocolos",
        json={"organization_id": "org_1", "name": "Metodo B", "code": "metodo-b"},
        headers=headers,
    ).json()
    pillar = client.post(
        "/admin/pilares",
        json={"protocol_id": protocol_a["id"], "name": "Rotina", "code": "rotina", "order_index": 2},
        headers=headers,
    ).json()

    inconsistent_metric = client.post(
        "/admin/metricas",
        json={
            "protocol_id": protocol_b["id"],
            "pillar_id": pillar["id"],
            "name": "Consistencia",
            "code": "consistencia",
            "direction": "higher_better",
        },
        headers=headers,
    )
    assert inconsistent_metric.status_code == 409


def test_admin_can_read_method_structure(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    protocol_response = client.post(
        "/admin/protocolos",
        json={"organization_id": "org_1", "name": "Metodo Estrutura", "code": "metodo-estrutura"},
        headers=headers,
    )
    assert protocol_response.status_code == 201
    protocol_id = protocol_response.json()["id"]

    pillar_b = client.post(
        "/admin/pilares",
        json={"protocol_id": protocol_id, "name": "Resultados", "code": "resultados", "order_index": 2},
        headers=headers,
    )
    assert pillar_b.status_code == 201

    pillar_a = client.post(
        "/admin/pilares",
        json={"protocol_id": protocol_id, "name": "Consistencia", "code": "consistencia", "order_index": 1},
        headers=headers,
    )
    assert pillar_a.status_code == 201

    metric_a = client.post(
        "/admin/metricas",
        json={
            "protocol_id": protocol_id,
            "pillar_id": pillar_a.json()["id"],
            "name": "Frequencia",
            "code": "frequencia",
        },
        headers=headers,
    )
    assert metric_a.status_code == 201

    metric_b = client.post(
        "/admin/metricas",
        json={
            "protocol_id": protocol_id,
            "pillar_id": pillar_b.json()["id"],
            "name": "Entrega",
            "code": "entrega",
        },
        headers=headers,
    )
    assert metric_b.status_code == 201

    response = client.get(f"/admin/protocolos/{protocol_id}/estrutura", headers=headers)
    assert response.status_code == 200
    body = response.json()

    assert body["protocol"]["id"] == protocol_id
    assert len(body["pillars"]) == 2
    assert body["pillars"][0]["order_index"] == 1
    assert body["pillars"][1]["order_index"] == 2
    assert len(body["pillars"][0]["metrics"]) == 1
    assert len(body["pillars"][1]["metrics"]) == 1
