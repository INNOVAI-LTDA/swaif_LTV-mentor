from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.api.routes.admin_database_view import get_service
from app.core.security import hash_password
from app.main import app
from app.services.admin_database_view_service import AdminDatabaseViewService
from app.storage.contact_user_repository import ContactUserRepository


class _FakeAdminDatabaseViewRepository:
    def snapshot_payloads(self) -> dict[str, dict[str, Any]]:
        return {
            "organizations": {"items": [{"id": "org-1"}]},
            "products": {"items": [{"id": "prd-1"}]},
            "enrollments": {"items": [{"id": "enr-1"}]},
            "pillars": {"items": [{"id": "plr-1"}]},
            "metrics": {"items": [{"id": "met-1"}]},
            "measurements": {"items": [{"id": "mea-1"}]},
            "checkpoints": {"items": [{"id": "chk-1"}]},
            "contacts_users_v2": {
                "items": [
                    {"id": "u-admin", "email": "admin@example.com", "role": "admin", "password_hash": "secret"},
                    {"id": "u-provider", "email": "provider@example.com", "role": "provider", "password_hash": "secret"},
                    {"id": "u-client", "email": "client@example.com", "role": "client", "password_hash": "secret"},
                ]
            },
        }


def _seed_users(contacts_file: Path) -> None:
    repo = ContactUserRepository(contacts_file)
    repo.create(
        id="1",
        full_name="Admin",
        email="admin@example.com",
        role="admin",
        is_active=True,
        password_hash=hash_password("admin123"),
    )
    repo.create(
        id="2",
        full_name="Provider",
        email="provider@example.com",
        role="provider",
        is_active=True,
        password_hash=hash_password("provider123"),
    )


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_admin_database_view_requires_auth(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")

    app.dependency_overrides[get_service] = lambda: AdminDatabaseViewService(_FakeAdminDatabaseViewRepository())
    try:
        client = TestClient(app)
        response = client.get("/admin/database-view")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(get_service, None)


def test_admin_database_view_forbids_provider(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    _seed_users(contacts_file)

    app.dependency_overrides[get_service] = lambda: AdminDatabaseViewService(_FakeAdminDatabaseViewRepository())
    try:
        client = TestClient(app)
        provider_token = _login(client, "provider@example.com", "provider123")
        response = client.get("/admin/database-view", headers={"Authorization": f"Bearer {provider_token}"})
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_service, None)


def test_admin_database_view_returns_snapshot_without_password_hash(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    _seed_users(contacts_file)

    app.dependency_overrides[get_service] = lambda: AdminDatabaseViewService(_FakeAdminDatabaseViewRepository())
    try:
        client = TestClient(app)
        admin_token = _login(client, "admin@example.com", "admin123")
        response = client.get("/admin/database-view", headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 200
        payload = response.json()
        assert "password_hash" not in payload["users"]["admins"][0]
        assert "password_hash" not in payload["users"]["providers"][0]
        assert "password_hash" not in payload["users"]["clients"][0]
        assert payload["integrity"] == {}
    finally:
        app.dependency_overrides.pop(get_service, None)
