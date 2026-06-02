from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.provider import get_provider_hierarchy_service
from app.core.security import hash_password
from app.main import app
from app.storage.contact_user_repository import ContactUserRepository


class _FakeProviderHierarchyService:
    def get_provider_hierarchy(self, provider_user_id: str):
        return {
            "provider": {"id": provider_user_id},
            "organization": {"id": "1"},
            "products": [],
            "enrollments": [],
            "clients": [],
        }


def _seed_contact(
    repo: ContactUserRepository,
    *,
    id: str,
    email: str,
    role: str,
    password: str,
    is_active: bool = True,
) -> None:
    repo.create(
        id=id,
        full_name=email,
        email=email,
        role=role,
        is_active=is_active,
        password_hash=hash_password(password),
    )


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_provider_hierarchy_requires_token(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    app.dependency_overrides[get_provider_hierarchy_service] = lambda: _FakeProviderHierarchyService()

    try:
        client = TestClient(app)
        response = client.get("/provider/me/hierarchy")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(get_provider_hierarchy_service, None)


def test_provider_hierarchy_forbids_admin_and_client(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    repo = ContactUserRepository(contacts_file)
    _seed_contact(repo, id="1", email="admin@example.com", role="admin", password="admin123")
    _seed_contact(repo, id="2", email="client@example.com", role="client", password="client123")
    app.dependency_overrides[get_provider_hierarchy_service] = lambda: _FakeProviderHierarchyService()

    try:
        client = TestClient(app)
        admin_token = _login(client, "admin@example.com", "admin123")
        client_token = _login(client, "client@example.com", "client123")

        admin_response = client.get("/provider/me/hierarchy", headers={"Authorization": f"Bearer {admin_token}"})
        client_response = client.get("/provider/me/hierarchy", headers={"Authorization": f"Bearer {client_token}"})

        assert admin_response.status_code == 403
        assert client_response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_provider_hierarchy_service, None)


def test_provider_hierarchy_returns_provider_payload(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    repo = ContactUserRepository(contacts_file)
    _seed_contact(repo, id="101", email="provider@example.com", role="provider", password="provider123")
    app.dependency_overrides[get_provider_hierarchy_service] = lambda: _FakeProviderHierarchyService()

    try:
        client = TestClient(app)
        token = _login(client, "provider@example.com", "provider123")
        response = client.get("/provider/me/hierarchy", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["provider"]["id"] == "101"
        assert payload["organization"]["id"] == "1"
    finally:
        app.dependency_overrides.pop(get_provider_hierarchy_service, None)


def test_provider_hierarchy_requires_supabase_db_url(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)

    repo = ContactUserRepository(contacts_file)
    _seed_contact(repo, id="101", email="provider@example.com", role="provider", password="provider123")

    client = TestClient(app)
    token = _login(client, "provider@example.com", "provider123")
    response = client.get("/provider/me/hierarchy", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SUPABASE_DB_URL_REQUIRED"
