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
        rows = {
            "provider_a": [
                {
                    "client_id": "c-1",
                    "client_name": "Client A",
                    "product_name": "Programa A",
                    "days_left": 20,
                    "investment": 10000,
                }
            ],
            "provider_b": [
                {
                    "client_id": "c-2",
                    "client_name": "Client B",
                    "product_name": "Programa B",
                    "days_left": 10,
                    "investment": 9000,
                }
            ],
        }
        return rows.get(provider_user_id, [])


def _seed_provider(repo: ContactUserRepository, *, id: str, email: str, password: str) -> None:
    repo.create(
        id=id,
        full_name=email,
        email=email,
        role="provider",
        is_active=True,
        password_hash=hash_password(password),
    )


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_command_center_lists_only_provider_clients_from_supabase_hierarchy(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")

    repo = ContactUserRepository(contacts_file)
    _seed_provider(repo, id="usr_provider_a", email="provider.a@example.com", password="provider123")
    _seed_provider(repo, id="usr_provider_b", email="provider.b@example.com", password="provider456")

    app.dependency_overrides[get_provider_workspace_service] = lambda: ProviderWorkspaceService(_FakeHierarchyRepository())
    try:
        client = TestClient(app)
        token = _login(client, "provider.a@example.com", "provider123")
        response = client.get("/mentor/centro-comando/alunos", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        payload = response.json()
        assert len(payload["items"]) == 1
        assert payload["items"][0]["id"] == "c-1"
        assert payload["items"][0]["name"] == "Client A"
    finally:
        app.dependency_overrides.pop(get_provider_workspace_service, None)
