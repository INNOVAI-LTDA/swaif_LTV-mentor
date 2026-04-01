from fastapi.testclient import TestClient

from app.config.runtime import (
    get_client_code,
    get_storage_backup_dir,
    mentor_routes_enabled,
    resolve_mentor_route_policy,
)
from app.main import create_app
from app.storage.catalog import resolve_storage_root


def test_mentor_routes_enabled_by_default_in_local(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.delenv("ENABLE_MENTOR_ROUTES", raising=False)

    assert mentor_routes_enabled() is True


def test_mentor_routes_disabled_by_default_in_production_like_env(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("ENABLE_MENTOR_ROUTES", raising=False)

    assert mentor_routes_enabled() is False


def test_mentor_routes_can_be_forced_on(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("ENABLE_MENTOR_ROUTES", "true")

    assert mentor_routes_enabled() is True


def test_production_like_mentor_enablement_requires_explicit_remote_approval(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ENABLE_MENTOR_ROUTES", "true")
    monkeypatch.delenv("ALLOW_REMOTE_MENTOR_ROUTES", raising=False)

    try:
        resolve_mentor_route_policy()
    except RuntimeError as error:
        assert str(error) == (
            "ENABLE_MENTOR_ROUTES=true requires ALLOW_REMOTE_MENTOR_ROUTES=true when APP_ENV is production-like."
        )
    else:
        raise AssertionError("Expected remote mentor enablement to require explicit approval.")


def test_production_like_mentor_can_be_enabled_with_explicit_remote_approval(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ENABLE_MENTOR_ROUTES", "true")
    monkeypatch.setenv("ALLOW_REMOTE_MENTOR_ROUTES", "true")

    policy = resolve_mentor_route_policy()

    assert policy.enabled is True
    assert policy.policy_source == "explicit-remote-approval"


def test_get_storage_backup_dir_accepts_explicit_env(monkeypatch, tmp_path) -> None:
    backup_dir = tmp_path / "backups"
    monkeypatch.setenv("STORAGE_BACKUP_DIR", str(backup_dir))

    assert get_storage_backup_dir() == backup_dir


def test_get_client_code_required_in_production_like_env(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("CLIENT_CODE", raising=False)

    try:
        get_client_code()
    except RuntimeError as error:
        assert str(error) == "CLIENT_CODE is required."
    else:
        raise AssertionError("Expected CLIENT_CODE to be required in production-like environments.")


def test_get_client_code_validates_characters(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CLIENT_CODE", "cliente x")

    try:
        get_client_code()
    except RuntimeError as error:
        assert str(error) == "CLIENT_CODE must contain only letters, numbers, hyphen, or underscore."
    else:
        raise AssertionError("Expected invalid CLIENT_CODE to fail validation.")


def test_get_client_code_required_in_local_env(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.delenv("CLIENT_CODE", raising=False)

    try:
        get_client_code()
    except RuntimeError as error:
        assert str(error) == "CLIENT_CODE is required."
    else:
        raise AssertionError("Expected CLIENT_CODE to be required in local environments.")


def test_get_client_code_returns_valid_value(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CLIENT_CODE", "accmed-client")

    assert get_client_code() == "accmed-client"


def test_create_app_disables_mentor_routes_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://cliente.example.com")
    monkeypatch.setenv("CLIENT_CODE", "test-client")
    monkeypatch.setenv("ENABLE_MENTOR_ROUTES", "false")
    monkeypatch.delenv("ALLOW_REMOTE_MENTOR_ROUTES", raising=False)

    app = create_app()
    client = TestClient(app)

    response = client.get("/mentor/matriz-renovacao")
    assert response.status_code == 404


def test_create_app_keeps_mentor_routes_in_local(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("CLIENT_CODE", "test-local")
    monkeypatch.delenv("ENABLE_MENTOR_ROUTES", raising=False)
    monkeypatch.delenv("ALLOW_REMOTE_MENTOR_ROUTES", raising=False)
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)

    app = create_app()
    client = TestClient(app)

    response = client.get("/mentor/matriz-renovacao")
    assert response.status_code == 401
    assert app.state.runtime_summary["mentor_route_policy_source"] == "local-default-enabled"


def test_create_app_exposes_runtime_policy_summary_for_remote_approval(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://cliente.example.com")
    monkeypatch.setenv("CLIENT_CODE", "test-client")
    monkeypatch.setenv("ENABLE_MENTOR_ROUTES", "true")
    monkeypatch.setenv("ALLOW_REMOTE_MENTOR_ROUTES", "true")

    app = create_app()

    assert app.state.runtime_summary["mentor_routes_enabled"] is True
    assert app.state.runtime_summary["mentor_route_policy_source"] == "explicit-remote-approval"


def test_create_app_configures_allow_origin_regex_when_present(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://cliente.example.com")
    monkeypatch.setenv("CORS_ALLOW_ORIGIN_REGEX", r"^https://.*\\.vercel\\.app$")
    monkeypatch.setenv("CLIENT_CODE", "test-client")

    app = create_app()

    cors_middleware = next(
        mw for mw in app.user_middleware if mw.cls.__name__ == "CORSMiddleware"
    )
    assert cors_middleware.kwargs["allow_origin_regex"] == r"^https://.*\\.vercel\\.app$"
    assert app.state.runtime_summary["cors_origin_regex"] == r"^https://.*\\.vercel\\.app$"


def test_resolve_storage_root_requires_common_filesystem_root(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("USER_STORE_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("CLIENT_STORE_PATH", str(tmp_path / "clients.json"))
    monkeypatch.setenv("ORG_STORE_PATH", str(tmp_path / "organizations.json"))
    monkeypatch.setenv("MENTOR_STORE_PATH", str(tmp_path / "mentors.json"))
    monkeypatch.setenv("PROTOCOL_STORE_PATH", str(tmp_path / "protocols.json"))
    monkeypatch.setenv("PILLAR_STORE_PATH", str(tmp_path / "pillars.json"))
    monkeypatch.setenv("METRIC_STORE_PATH", str(tmp_path / "metrics.json"))
    monkeypatch.setenv("STUDENT_STORE_PATH", str(tmp_path / "students.json"))
    monkeypatch.setenv("ENROLLMENT_STORE_PATH", str(tmp_path / "enrollments.json"))
    monkeypatch.setenv("MEASUREMENT_STORE_PATH", str(tmp_path / "measurements.json"))
    monkeypatch.setenv("CHECKPOINT_STORE_PATH", "D:\\backup\\checkpoints.json")

    try:
        resolve_storage_root()
    except RuntimeError as error:
        assert str(error) == "Storage paths must share a common filesystem root."
    else:
        raise AssertionError("Expected mixed filesystem roots to fail.")
