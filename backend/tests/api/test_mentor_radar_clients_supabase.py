from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.mentor import get_provider_workspace_service
from app.core.security import hash_password
from app.main import app
from app.services.provider_workspace_service import ProviderWorkspaceService
from app.storage.contact_user_repository import ContactUserRepository


class _FakeHierarchyRepository:
    def __init__(self, rows):
        self._rows = rows

    def list_active_provider_hierarchy(self, provider_user_id: str):
        return list(self._rows.get(provider_user_id, []))


class _FakeProductMetricRepository:
    def list_metric_tree_by_product(self, product_id: str):
        return [
            {
                "id": "pillar-1",
                "name": "Pilar 1",
                "slug": "pilar-1",
                "metrics": [{"id": "metric-1"}],
            }
        ] if product_id else []


class _FakeMeasurementRepository:
    def __init__(self, by_enrollment):
        self._by_enrollment = by_enrollment

    def list_by_enrollment(self, enrollment_id: str):
        return list(self._by_enrollment.get(enrollment_id, []))


def _seed_provider(contacts_file: Path) -> None:
    repo = ContactUserRepository(contacts_file)
    repo.create(
        id="usr_provider_a",
        full_name="Provider A",
        email="provider.a@example.com",
        role="provider",
        is_active=True,
        password_hash=hash_password("provider123"),
    )


def _login(client: TestClient) -> str:
    response = client.post("/auth/login", json={"email": "provider.a@example.com", "password": "provider123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_radar_clients_aggregates_two_provider_clients(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    _seed_provider(contacts_file)

    hierarchy_rows = {
        "provider_a": [
            {
                "enrollment_id": "enr-1",
                "client_id": "c-1",
                "client_name": "Client A",
                "product_id": "p-1",
                "product_name": "Programa A",
                "days_left": 20,
            },
            {
                "enrollment_id": "enr-2",
                "client_id": "c-2",
                "client_name": "Client B",
                "product_id": "p-2",
                "product_name": "Programa B",
                "days_left": 30,
            },
        ]
    }
    measurements = {
        "enr-1": [{"metric_id": "metric-1", "value_baseline": 1.0, "value_current": 2.0, "value_projected": 3.0}],
        "enr-2": [{"metric_id": "metric-1", "value_baseline": 2.0, "value_current": 4.0, "value_projected": 6.0}],
    }
    service = ProviderWorkspaceService(
        _FakeHierarchyRepository(hierarchy_rows),
        product_metric_repository=_FakeProductMetricRepository(),
        runtime_measurement_repository=_FakeMeasurementRepository(measurements),
    )
    app.dependency_overrides[get_provider_workspace_service] = lambda: service
    try:
        client = TestClient(app)
        token = _login(client)
        response = client.get("/mentor/radar/clientes", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        payload = response.json()
        assert len(payload["clients"]) == 2
        assert payload["avgCurrent"] == 3.0
    finally:
        app.dependency_overrides.pop(get_provider_workspace_service, None)


def test_radar_clients_handles_missing_measurements_without_500(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    _seed_provider(contacts_file)

    hierarchy_rows = {
        "provider_a": [
            {
                "enrollment_id": "enr-1",
                "client_id": "c-1",
                "client_name": "Client A",
                "product_id": "p-1",
                "product_name": "Programa A",
                "days_left": 20,
            }
        ]
    }
    service = ProviderWorkspaceService(
        _FakeHierarchyRepository(hierarchy_rows),
        product_metric_repository=_FakeProductMetricRepository(),
        runtime_measurement_repository=_FakeMeasurementRepository({}),
    )
    app.dependency_overrides[get_provider_workspace_service] = lambda: service
    try:
        client = TestClient(app)
        token = _login(client)
        response = client.get("/mentor/radar/clientes", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["axisScores"] == []
        assert payload["avgCurrent"] == 0.0
    finally:
        app.dependency_overrides.pop(get_provider_workspace_service, None)
