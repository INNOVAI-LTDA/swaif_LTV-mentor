from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.errors import http_exception_handler, request_validation_exception_handler
from app.api.routes.provider import require_provider_user
from app.core.security import create_access_token, hash_password
from app.storage.contact_user_repository import ContactUserRepository
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)

    @app.get("/_provider/probe")
    def provider_probe(user: dict[str, Any] = Depends(require_provider_user)) -> dict[str, Any]:
        return {"id": str(user["id"]), "role": str(user["role"])}

    return app


def _seed_user(repo: ContactUserRepository, *, id: str, email: str, role: str, is_active: bool = True) -> None:
    repo.create(
        id=id,
        full_name=email,
        email=email,
        role=role,
        is_active=is_active,
        password_hash=hash_password("senha123"),
    )


def _token(user_id: str, role: str, secret: str = "test-secret") -> str:
    return create_access_token(user_id=user_id, role=role, secret=secret)


def test_require_provider_user_returns_401_without_token(monkeypatch, tmp_path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")

    client = TestClient(_build_app())
    response = client.get("/_provider/probe")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_MISSING_TOKEN"


def test_require_provider_user_returns_403_for_admin_token(monkeypatch, tmp_path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")

    repo = ContactUserRepository(contacts_file)
    _seed_user(repo, id="10", email="admin@example.com", role="admin")

    client = TestClient(_build_app())
    response = client.get(
        "/_provider/probe",
        headers={"Authorization": f"Bearer {_token('10', 'admin')}"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "AUTH_FORBIDDEN"


def test_require_provider_user_returns_403_for_client_token(monkeypatch, tmp_path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")

    repo = ContactUserRepository(contacts_file)
    _seed_user(repo, id="20", email="client@example.com", role="client")

    client = TestClient(_build_app())
    response = client.get(
        "/_provider/probe",
        headers={"Authorization": f"Bearer {_token('20', 'client')}"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "AUTH_FORBIDDEN"


def test_require_provider_user_returns_200_for_provider_token(monkeypatch, tmp_path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")

    repo = ContactUserRepository(contacts_file)
    _seed_user(repo, id="30", email="provider@example.com", role="provider")

    client = TestClient(_build_app())
    response = client.get(
        "/_provider/probe",
        headers={"Authorization": f"Bearer {_token('30', 'provider')}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "30"
    assert payload["role"] == "provider"
