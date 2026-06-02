from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.mentor import get_provider_workspace_service
from app.core.security import hash_password
from app.main import app
from app.storage.contact_user_repository import ContactUserRepository


class _FakeProviderWorkspaceService:
    def get_renewal_matrix(self, *, filter_mode: str, provider_user_id: str):
        return {
            "filter": filter_mode,
            "items": [],
            "kpis": {"totalLTV": 0, "criticalRenewals": 0, "rescueCount": 0, "avgEngagement": 0},
            "context": {"mentorId": provider_user_id},
        }


def _seed_contact(repo: ContactUserRepository, *, id: str, email: str, role: str, password: str) -> None:
    repo.create(
        id=id,
        full_name=email,
        email=email,
        role=role,
        is_active=True,
        password_hash=hash_password(password),
    )


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_mentor_routes_use_provider_auth_without_mentor_repository(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("MENTOR_STORE_PATH", str(tmp_path / "missing_mentors.json"))

    repo = ContactUserRepository(contacts_file)
    _seed_contact(repo, id="usr_mentor_1", email="mentor@example.com", role="provider", password="mentor123")

    app.dependency_overrides[get_provider_workspace_service] = lambda: _FakeProviderWorkspaceService()
    try:
        client = TestClient(app)
        token = _login(client, "mentor@example.com", "mentor123")
        response = client.get("/mentor/matriz-renovacao", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["context"]["mentorId"] == "mentor_1"
    finally:
        app.dependency_overrides.pop(get_provider_workspace_service, None)


def test_mentor_routes_forbid_non_provider_roles(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")

    repo = ContactUserRepository(contacts_file)
    _seed_contact(repo, id="1", email="admin@example.com", role="admin", password="admin123")

    app.dependency_overrides[get_provider_workspace_service] = lambda: _FakeProviderWorkspaceService()
    try:
        client = TestClient(app)
        token = _login(client, "admin@example.com", "admin123")
        response = client.get("/mentor/matriz-renovacao", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "AUTH_FORBIDDEN"
    finally:
        app.dependency_overrides.pop(get_provider_workspace_service, None)
