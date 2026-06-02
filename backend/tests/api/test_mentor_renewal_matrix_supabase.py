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
                "client_id": "c-1",
                "client_name": "Client One",
                "product_name": "Programa 1",
                "days_left": 10,
                "investment": 10000,
                "decision_matrix_status": "rescue",
            },
            {
                "client_id": "c-2",
                "client_name": "Client Two",
                "product_name": "Programa 2",
                "days_left": 30,
                "investment": 8000,
                "decision_matrix_status": "critical",
            },
            {
                "client_id": "c-3",
                "client_name": "Client Three",
                "product_name": "Programa 3",
                "days_left": 60,
                "investment": 7000,
                "decision_matrix_status": "topRight",
            },
        ]


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
    return ProviderWorkspaceService(_FakeHierarchyRepository())


def test_renewal_matrix_returns_only_provider_clients(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    _seed_provider(contacts_file)

    app.dependency_overrides[get_provider_workspace_service] = _override_service
    try:
        client = TestClient(app)
        token = _login(client)
        response = client.get("/mentor/matriz-renovacao?filter=all", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        payload = response.json()
        assert len(payload["items"]) == 3
        assert {item["id"] for item in payload["items"]} == {"c-1", "c-2", "c-3"}
        assert {item["quadrant"] for item in payload["items"]}.issubset(
            {"topRight", "topLeft", "bottomRight", "bottomLeft"}
        )
    finally:
        app.dependency_overrides.pop(get_provider_workspace_service, None)


def test_renewal_matrix_filters_critical_and_rescue(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    _seed_provider(contacts_file)

    app.dependency_overrides[get_provider_workspace_service] = _override_service
    try:
        client = TestClient(app)
        token = _login(client)
        critical = client.get("/mentor/matriz-renovacao?filter=critical", headers={"Authorization": f"Bearer {token}"})
        rescue = client.get("/mentor/matriz-renovacao?filter=rescue", headers={"Authorization": f"Bearer {token}"})

        assert critical.status_code == 200
        assert rescue.status_code == 200
        assert [item["id"] for item in critical.json()["items"]] == ["c-2"]
        assert [item["id"] for item in rescue.json()["items"]] == ["c-1"]
    finally:
        app.dependency_overrides.pop(get_provider_workspace_service, None)
