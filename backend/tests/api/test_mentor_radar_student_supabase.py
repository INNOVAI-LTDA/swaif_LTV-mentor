from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.mentor import get_provider_workspace_service
from app.core.security import hash_password
from app.main import app
from app.services.provider_workspace_service import ProviderWorkspaceService
from app.storage.contact_user_repository import ContactUserRepository


class _FakeHierarchyRepository:
    def list_active_provider_hierarchy(self, provider_user_id: str):
        if provider_user_id != "provider_a":
            return []
        return [
            {
                "enrollment_id": "enr-1",
                "client_id": "client-1",
                "client_name": "Client One",
                "product_id": "product-1",
                "product_name": "Programa",
                "days_left": 20,
            }
        ]


class _FakeProductMetricRepository:
    def list_metric_tree_by_product(self, product_id: str):
        if product_id != "product-1":
            return []
        return [
            {"id": "pillar-1", "name": "Pilar 1", "slug": "pilar-1", "metrics": [{"id": "metric-1"}]},
        ]


class _FakeMeasurementRepository:
    def list_by_enrollment(self, enrollment_id: str):
        if enrollment_id != "enr-1":
            return []
        return [{"metric_id": "metric-1", "value_baseline": 1.0, "value_current": 2.0, "value_projected": 3.0}]


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


def _override_service() -> ProviderWorkspaceService:
    return ProviderWorkspaceService(
        _FakeHierarchyRepository(),
        product_metric_repository=_FakeProductMetricRepository(),
        runtime_measurement_repository=_FakeMeasurementRepository(),
    )


def test_radar_student_returns_200_for_owned_client(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    _seed_provider(contacts_file)

    app.dependency_overrides[get_provider_workspace_service] = _override_service
    try:
        client = TestClient(app)
        token = _login(client)
        response = client.get("/mentor/radar/alunos/client-1", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["studentId"] == "client-1"
        assert payload["avgCurrent"] == 2.0
    finally:
        app.dependency_overrides.pop(get_provider_workspace_service, None)


def test_radar_student_returns_404_for_other_provider_client(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    _seed_provider(contacts_file)

    app.dependency_overrides[get_provider_workspace_service] = _override_service
    try:
        client = TestClient(app)
        token = _login(client)
        response = client.get("/mentor/radar/alunos/client-2", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "ALUNO_NOT_FOUND"
    finally:
        app.dependency_overrides.pop(get_provider_workspace_service, None)


def test_radar_student_returns_404_for_nonexistent_client(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    _seed_provider(contacts_file)

    app.dependency_overrides[get_provider_workspace_service] = _override_service
    try:
        client = TestClient(app)
        token = _login(client)
        response = client.get("/mentor/radar/alunos/client-x", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "ALUNO_NOT_FOUND"
    finally:
        app.dependency_overrides.pop(get_provider_workspace_service, None)
