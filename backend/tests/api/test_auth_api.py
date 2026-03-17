from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
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
    _prepare_user_store(users_file)
    monkeypatch.setenv("USER_STORE_PATH", str(users_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")

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
    assert me_body["email"] == "admin@swaif.local"
    assert me_body["role"] == "admin"
