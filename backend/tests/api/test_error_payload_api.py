from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _configure_stores(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("USER_STORE_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("ORG_STORE_PATH", str(tmp_path / "organizations.json"))
    monkeypatch.setenv("MENTOR_STORE_PATH", str(tmp_path / "mentors.json"))
    monkeypatch.setenv("PROTOCOL_STORE_PATH", str(tmp_path / "protocols.json"))
    monkeypatch.setenv("PILLAR_STORE_PATH", str(tmp_path / "pillars.json"))
    monkeypatch.setenv("METRIC_STORE_PATH", str(tmp_path / "metrics.json"))
    monkeypatch.setenv("STUDENT_STORE_PATH", str(tmp_path / "students.json"))
    monkeypatch.setenv("ENROLLMENT_STORE_PATH", str(tmp_path / "enrollments.json"))
    monkeypatch.setenv("MEASUREMENT_STORE_PATH", str(tmp_path / "measurements.json"))
    monkeypatch.setenv("CHECKPOINT_STORE_PATH", str(tmp_path / "checkpoints.json"))


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _assert_error_shape(
    response,
    *,
    status_code: int,
    expected_code: str,
    expected_message: str | None = None,
) -> None:
    assert response.status_code == status_code
    body = response.json()
    assert "error" in body
    error = body["error"]
    assert error["status"] == status_code
    assert error["code"] == expected_code
    assert isinstance(error["message"], str)
    if expected_message is not None:
        assert error["message"] == expected_message


def test_standard_error_payload_for_401(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={"email": "admin@swaif.local", "password": "wrong"},
    )
    _assert_error_shape(
        response,
        status_code=401,
        expected_code="AUTH_INVALID_CREDENTIALS",
        expected_message="Credenciais invalidas.",
    )


def test_standard_error_payload_for_404(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/admin/mentorias/org_missing", headers=headers)
    _assert_error_shape(
        response,
        status_code=404,
        expected_code="MENTORIA_NOT_FOUND",
        expected_message="Mentoria nao encontrada.",
    )


def test_standard_error_payload_for_409(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {token}"}

    first = client.post(
        "/admin/mentorias",
        json={"name": "Mentoria Nove", "slug": "mentoria-nove"},
        headers=headers,
    )
    assert first.status_code == 201

    duplicate = client.post(
        "/admin/mentorias",
        json={"name": "Mentoria Nove 2", "slug": "mentoria-nove"},
        headers=headers,
    )
    _assert_error_shape(
        duplicate,
        status_code=409,
        expected_code="MENTORIA_CONFLICT",
        expected_message="Ja existe mentoria com este slug.",
    )


def test_standard_error_payload_for_422(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.post("/auth/login", json={"email": "admin@swaif.local"})
    _assert_error_shape(
        response,
        status_code=422,
        expected_code="VALIDATION_ERROR",
    )
    assert isinstance(response.json()["error"]["details"], list)
