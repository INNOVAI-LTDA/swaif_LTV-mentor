from app.config.runtime import (
    LOCAL_CORS_ORIGINS,
    get_app_env,
    get_cors_allow_origin_regex,
    resolve_cors_origins,
)


def test_get_app_env_requires_explicit_value(monkeypatch) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)

    try:
        get_app_env()
    except RuntimeError as error:
        assert str(error) == "APP_ENV is required. Use 'local' for local development or a production-like value for deployment."
    else:
        raise AssertionError("Expected missing APP_ENV to fail fast.")


def test_resolve_cors_origins_uses_local_defaults_when_app_env_is_local(monkeypatch) -> None:
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    monkeypatch.setenv("APP_ENV", "local")

    assert resolve_cors_origins() == LOCAL_CORS_ORIGINS


def test_local_defaults_include_vite_preview_port(monkeypatch) -> None:
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    monkeypatch.setenv("APP_ENV", "local")

    origins = resolve_cors_origins()

    assert "http://localhost:4173" in origins
    assert "http://127.0.0.1:4173" in origins


def test_local_defaults_include_active_vite_dev_ports(monkeypatch) -> None:
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    monkeypatch.setenv("APP_ENV", "local")

    origins = resolve_cors_origins()

    assert "http://localhost:5175" in origins
    assert "http://127.0.0.1:5175" in origins
    assert "http://localhost:5176" in origins
    assert "http://127.0.0.1:5176" in origins


def test_resolve_cors_origins_requires_explicit_origins_in_production_like_env(monkeypatch) -> None:
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    monkeypatch.setenv("APP_ENV", "prod")

    try:
        resolve_cors_origins()
    except RuntimeError as error:
        assert str(error) == "CORS_ALLOW_ORIGINS is required when APP_ENV is production-like."
    else:
        raise AssertionError("Expected production-like CORS configuration to fail without explicit origins.")


def test_resolve_cors_origins_accepts_comma_separated_origins(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://cliente.example.com/, https://app.example.com/")

    assert resolve_cors_origins() == ["https://cliente.example.com", "https://app.example.com"]


def test_resolve_cors_origins_rejects_wildcard_in_production_like_env(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "*")

    try:
        resolve_cors_origins()
    except RuntimeError as error:
        assert str(error) == "CORS_ALLOW_ORIGINS must not include '*' when APP_ENV is production-like."
    else:
        raise AssertionError("Expected wildcard CORS to be rejected in production-like envs.")


def test_resolve_cors_origins_rejects_entries_with_paths_or_query_strings(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://cliente.example.com/app?demo=true")

    try:
        resolve_cors_origins()
    except RuntimeError as error:
        assert str(error) == "CORS_ALLOW_ORIGINS entries must be bare origins without paths, query strings, or fragments."
    else:
        raise AssertionError("Expected malformed CORS origin to fail.")


def test_resolve_cors_origins_rejects_entries_with_credentials(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://user:secret@cliente.example.com")

    try:
        resolve_cors_origins()
    except RuntimeError as error:
        assert str(error) == "CORS_ALLOW_ORIGINS entries must not include credentials."
    else:
        raise AssertionError("Expected credential-bearing CORS origin to fail.")


def test_cors_allow_origin_regex_must_be_valid(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ALLOW_ORIGIN_REGEX", "*[")

    try:
        get_cors_allow_origin_regex()
    except RuntimeError as error:
        assert str(error) == "CORS_ALLOW_ORIGIN_REGEX must be a valid regex pattern."
    else:
        raise AssertionError("Expected invalid regex pattern to fail fast.")
