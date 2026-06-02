from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.main import app
from app.storage.contact_user_repository import ContactUserRepository


def test_provider_me_returns_authenticated_provider_payload(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")

    contacts = ContactUserRepository(contacts_file)
    contacts.create(
        id="101",
        full_name="Nome Provider",
        email="provider@accmed.com.br",
        role="provider",
        is_active=True,
        organization_id="1",
        password_hash=hash_password("provider123"),
    )

    client = TestClient(app)
    login_response = client.post(
        "/auth/login",
        json={"email": "provider@accmed.com.br", "password": "provider123"},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    response = client.get("/provider/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "id": "101",
        "email": "provider@accmed.com.br",
        "fullName": "Nome Provider",
        "role": "provider",
        "organizationId": "1",
    }
