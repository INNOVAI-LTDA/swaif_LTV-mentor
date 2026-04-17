from pathlib import Path

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.main import app
from app.storage.student_repository import StudentRepository
from app.storage.user_repository import UserRepository


def _prepare_user_store(path: Path) -> None:
    repo = UserRepository(path)
    repo.list_users()


def _prepare_student_store(path: Path) -> None:
    repo = StudentRepository(path)
    repo.list_students()


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


def test_me_normalizes_legacy_client_role_to_aluno(monkeypatch, tmp_path: Path) -> None:
    users_file = tmp_path / "users.json"
    _prepare_user_store(users_file)
    monkeypatch.setenv("USER_STORE_PATH", str(users_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")

    repo = UserRepository(users_file)
    repo.create(
        id="usr_legacy_client",
        email="legacy.client@swaif.local",
        password_hash=hash_password("legacy123"),
        role="client",
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
    assert me_response.json()["role"] == "aluno"


def test_login_provisions_active_student_with_default_password(monkeypatch, tmp_path: Path) -> None:
    users_file = tmp_path / "users.json"
    students_file = tmp_path / "students.json"
    _prepare_user_store(users_file)
    _prepare_student_store(students_file)
    monkeypatch.setenv("USER_STORE_PATH", str(users_file))
    monkeypatch.setenv("STUDENT_STORE_PATH", str(students_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_DEFAULT_STUDENT_PASSWORD", "aluno_accmed")

    students_repo = StudentRepository(students_file)
    students_repo.create(
        full_name="Aluno Provisionado",
        initials="AP",
        email="aluno.provisionado@swaif.local",
    )

    client = TestClient(app)
    login_response = client.post(
        "/auth/login",
        json={"email": "aluno.provisionado@swaif.local", "password": "aluno_accmed"},
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    me_response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    me_payload = me_response.json()
    assert me_payload["email"] == "aluno.provisionado@swaif.local"
    assert me_payload["role"] == "aluno"

    users_repo = UserRepository(users_file)
    provisioned_user = users_repo.get_by_email("aluno.provisionado@swaif.local")
    assert provisioned_user is not None
    assert provisioned_user["role"] == "aluno"
