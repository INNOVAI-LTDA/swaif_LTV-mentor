from pathlib import Path

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.main import app
from app.storage.contact_user_repository import ContactUserRepository
from app.storage.user_repository import UserRepository


def _prepare_user_store(path: Path) -> None:
    repo = UserRepository(path)
    repo.list_users()


def test_login_invalid_credentials_returns_401(monkeypatch, tmp_path: Path) -> None:
    users_file = tmp_path / "users.json"
    _prepare_user_store(users_file)
    monkeypatch.setenv("USER_STORE_PATH", str(users_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")

    client = TestClient(app)
    response = client.post(
        "/auth/login",
        json={"email": "admin@swaif.local", "password": "wrong"},
    )

    assert response.status_code == 401


def test_login_success_and_me_flow(monkeypatch, tmp_path: Path) -> None:
    users_file = tmp_path / "users.json"
    contacts_file = tmp_path / "contacts_users_v2.json"
    _prepare_user_store(users_file)
    monkeypatch.setenv("USER_STORE_PATH", str(users_file))
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    contacts = ContactUserRepository(contacts_file)
    contacts.create(
        id="1",
        full_name="Admin",
        email="admin@swaif.local",
        role="admin",
        is_active=True,
        password_hash=hash_password("admin123"),
    )

    client = TestClient(app)
    login_response = client.post(
        "/auth/login",
        json={"email": "admin@swaif.local", "password": "admin123"},
    )

    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)

    unauthorized_me = client.get("/me")
    assert unauthorized_me.status_code == 401

    authorized_me = client.get(
        "/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert authorized_me.status_code == 200
    me_body = authorized_me.json()
    assert me_body["id"] == "1"
    assert me_body["email"] == "admin@swaif.local"
    assert me_body["role"] == "admin"


def test_me_accepts_string_user_ids(monkeypatch, tmp_path: Path) -> None:
    users_file = tmp_path / "users.json"
    contacts_file = tmp_path / "contacts_users_v2.json"
    _prepare_user_store(users_file)
    monkeypatch.setenv("USER_STORE_PATH", str(users_file))
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    contacts = ContactUserRepository(contacts_file)
    contacts.create(
        id="usr_admin_runtime",
        full_name="Admin",
        email="admin.runtime@swaif.local",
        role="admin",
        is_active=True,
        password_hash=hash_password("admin123"),
    )

    client = TestClient(app)
    login_response = client.post(
        "/auth/login",
        json={"email": "admin.runtime@swaif.local", "password": "admin123"},
    )
    assert login_response.status_code == 200

    me_response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["id"] == "usr_admin_runtime"


def test_me_normalizes_legacy_aluno_and_student_roles_to_client(monkeypatch, tmp_path: Path) -> None:
    users_file = tmp_path / "users.json"
    _prepare_user_store(users_file)
    monkeypatch.setenv("USER_STORE_PATH", str(users_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")

    repo = UserRepository(users_file)
    repo.create(
        email="legacy.client@swaif.local",
        password_hash=hash_password("legacy123"),
        role="aluno",
        is_active=True,
    )

    client = TestClient(app)
    login_response = client.post(
        "/auth/login",
        json={"email": "legacy.client@swaif.local", "password": "legacy123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["role"] == "client"


def test_login_does_not_provision_client_with_default_password(monkeypatch, tmp_path: Path) -> None:
    users_file = tmp_path / "users.json"
    _prepare_user_store(users_file)
    monkeypatch.setenv("USER_STORE_PATH", str(users_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")

    client = TestClient(app)
    login_response = client.post(
        "/auth/login",
        json={"email": "aluno.provisionado@swaif.local", "password": "aluno_accmed"},
    )

    assert login_response.status_code == 401
    payload = login_response.json()
    assert payload["error"]["code"] == "AUTH_INVALID_CREDENTIALS"


def test_login_returns_password_not_configured_for_existing_user_without_hash(monkeypatch, tmp_path: Path) -> None:
    users_file = tmp_path / "users.json"
    _prepare_user_store(users_file)
    monkeypatch.setenv("USER_STORE_PATH", str(users_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")

    repo = UserRepository(users_file)
    repo.create(
        email="sem.hash@swaif.local",
        password_hash="",
        role="provider",
        is_active=True,
    )

    client = TestClient(app)
    response = client.post(
        "/auth/login",
        json={"email": "sem.hash@swaif.local", "password": "qualquer"},
    )

    assert response.status_code == 401
    payload = response.json()
    assert payload["error"]["code"] == "AUTH_PASSWORD_NOT_CONFIGURED"



def test_me_returns_provider_for_provider_and_mentor_alias(monkeypatch, tmp_path: Path) -> None:
    users_file = tmp_path / "users.json"
    _prepare_user_store(users_file)
    monkeypatch.setenv("USER_STORE_PATH", str(users_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")

    repo = UserRepository(users_file)
    repo.create(email="provider@swaif.local", password_hash=hash_password("provider123"), role="provider", is_active=True)
    repo.create(email="mentor.alias@swaif.local", password_hash=hash_password("mentor123"), role="mentor", is_active=True)

    client = TestClient(app)
    provider_token = client.post("/auth/login", json={"email": "provider@swaif.local", "password": "provider123"}).json()["access_token"]
    mentor_token = client.post("/auth/login", json={"email": "mentor.alias@swaif.local", "password": "mentor123"}).json()["access_token"]

    provider_me = client.get("/me", headers={"Authorization": f"Bearer {provider_token}"})
    mentor_me = client.get("/me", headers={"Authorization": f"Bearer {mentor_token}"})

    assert provider_me.status_code == 200
    assert provider_me.json()["role"] == "provider"
    assert mentor_me.status_code == 200
    assert mentor_me.json()["role"] == "provider"


def test_login_fails_fast_when_auth_secret_missing_in_production_like_env(monkeypatch, tmp_path: Path) -> None:
    users_file = tmp_path / "users.json"
    _prepare_user_store(users_file)
    monkeypatch.setenv("USER_STORE_PATH", str(users_file))
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("APP_AUTH_SECRET", raising=False)

    client = TestClient(app)
    response = client.post(
        "/auth/login",
        json={"email": "admin@swaif.local", "password": "admin123"},
    )

    assert response.status_code == 500
    payload = response.json()
    assert payload["error"]["code"] == "AUTH_SECRET_NOT_CONFIGURED"
    assert payload["error"]["message"] == "APP_AUTH_SECRET is required when APP_ENV is production-like."


def test_login_uses_dev_auth_secret_fallback_in_local_env(monkeypatch, tmp_path: Path) -> None:
    users_file = tmp_path / "users.json"
    contacts_file = tmp_path / "contacts_users_v2.json"
    _prepare_user_store(users_file)
    monkeypatch.setenv("USER_STORE_PATH", str(users_file))
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.delenv("APP_AUTH_SECRET", raising=False)

    contacts = ContactUserRepository(contacts_file)
    contacts.create(
        id="1",
        full_name="Admin",
        email="admin@swaif.local",
        role="admin",
        is_active=True,
        password_hash=hash_password("admin123"),
    )

    client = TestClient(app)
    response = client.post(
        "/auth/login",
        json={"email": "admin@swaif.local", "password": "admin123"},
    )

    assert response.status_code == 200
    assert isinstance(response.json()["access_token"], str)
