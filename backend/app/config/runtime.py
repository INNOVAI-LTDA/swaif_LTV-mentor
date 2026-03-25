import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


LOCAL_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

LOCAL_ENV_NAMES = {"local", "development", "dev", "test"}


@dataclass(frozen=True)
class MentorDemoRoutePolicy:
    enabled: bool
    policy_source: str


def get_app_env() -> str:
    app_env = os.getenv("APP_ENV", "").strip().lower()
    if not app_env:
        raise RuntimeError("APP_ENV is required. Use 'local' for local development or a production-like value for deployment.")
    return app_env


def is_production_like_environment(app_env: str | None = None) -> bool:
    normalized = app_env or get_app_env()
    return normalized not in LOCAL_ENV_NAMES


def _parse_optional_bool(value: str, *, env_name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{env_name} must be a boolean value.")


def _get_optional_bool_env(env_name: str) -> bool | None:
    configured = os.getenv(env_name, "")
    if not configured.strip():
        return None
    return _parse_optional_bool(configured, env_name=env_name)


def resolve_mentor_demo_route_policy(app_env: str | None = None) -> MentorDemoRoutePolicy:
    normalized_env = app_env or get_app_env()
    explicit_enablement = _get_optional_bool_env("ENABLE_MENTOR_DEMO_ROUTES")
    remote_approval = _get_optional_bool_env("ALLOW_REMOTE_MENTOR_DEMO_ROUTES")
    production_like = is_production_like_environment(normalized_env)

    if explicit_enablement is None:
        if production_like:
            return MentorDemoRoutePolicy(enabled=False, policy_source="production-default-disabled")
        return MentorDemoRoutePolicy(enabled=True, policy_source="local-default-enabled")

    if explicit_enablement is False:
        return MentorDemoRoutePolicy(enabled=False, policy_source="explicit-disable")

    if production_like and remote_approval is not True:
        raise RuntimeError(
            "ENABLE_MENTOR_DEMO_ROUTES=true requires ALLOW_REMOTE_MENTOR_DEMO_ROUTES=true when APP_ENV is production-like."
        )

    if production_like:
        return MentorDemoRoutePolicy(enabled=True, policy_source="explicit-remote-approval")
    return MentorDemoRoutePolicy(enabled=True, policy_source="explicit-local-enable")


def mentor_demo_routes_enabled(app_env: str | None = None) -> bool:
    return resolve_mentor_demo_route_policy(app_env).enabled


def get_storage_backup_dir() -> Path:
    configured = os.getenv("STORAGE_BACKUP_DIR", "").strip()
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "backups"


def normalize_cors_origin(origin: str) -> str:
    stripped = origin.strip()
    if stripped == "*":
        return stripped

    parsed = urlparse(stripped)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError("CORS_ALLOW_ORIGINS entries must be absolute http(s) origins.")
    if parsed.username or parsed.password:
        raise RuntimeError("CORS_ALLOW_ORIGINS entries must not include credentials.")
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise RuntimeError("CORS_ALLOW_ORIGINS entries must be bare origins without paths, query strings, or fragments.")
    return f"{parsed.scheme}://{parsed.netloc}"


def resolve_cors_origins() -> list[str]:
    app_env = get_app_env()
    cors_env = os.getenv("CORS_ALLOW_ORIGINS", "")
    cors_origins = [normalize_cors_origin(origin) for origin in cors_env.split(",") if origin.strip()]
    if cors_origins:
        return cors_origins
    if is_production_like_environment(app_env):
        raise RuntimeError("CORS_ALLOW_ORIGINS is required when APP_ENV is production-like.")
    return LOCAL_CORS_ORIGINS


def _normalize_client_code(raw: str) -> str:
    trimmed = raw.strip()
    if not trimmed:
        raise RuntimeError("CLIENT_CODE is required.")
    if not all(char.isalnum() or char in {"-", "_"} for char in trimmed):
        raise RuntimeError("CLIENT_CODE must contain only letters, numbers, hyphen, or underscore.")
    return trimmed


def get_client_code(app_env: str | None = None) -> str:
    """
    Returns the configured client code for the current runtime.
    CLIENT_CODE is required in all startup modes.
    """
    _ = app_env
    raw_client_code = os.getenv("CLIENT_CODE", "")
    return _normalize_client_code(raw_client_code)
