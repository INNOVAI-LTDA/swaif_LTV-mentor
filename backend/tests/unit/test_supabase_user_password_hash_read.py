from __future__ import annotations

from typing import Any

from app.storage import contact_user_repository as contact_user_repository_module
from app.storage import user_repository as user_repository_module


class _FakeCursor:
    def __init__(self, state: dict[str, Any]) -> None:
        self._state = state
        self._last_query = ""
        self.description: list[tuple[str]] | None = None

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, query: str, params: tuple[Any, ...] | None = None) -> None:
        normalized = " ".join(query.split())
        self._state["queries"].append(normalized)
        self._last_query = normalized
        _ = params

        if "SELECT id, email, role, is_active, COALESCE(password_hash, '') AS password_hash" in normalized:
            self.description = [
                ("id",),
                ("email",),
                ("role",),
                ("is_active",),
                ("password_hash",),
            ]
            return

        if (
            "SELECT id, full_name, email, role, is_active, organization_id, created_at, updated_at, "
            "COALESCE(password_hash, '') AS password_hash" in normalized
        ):
            self.description = [
                ("id",),
                ("full_name",),
                ("email",),
                ("role",),
                ("is_active",),
                ("organization_id",),
                ("created_at",),
                ("updated_at",),
                ("password_hash",),
            ]
            return

        self.description = [("exists",)]

    def fetchone(self) -> tuple[int] | None:
        if "information_schema.columns" in self._last_query:
            return (1,)
        return None

    def fetchall(self) -> list[tuple[Any, ...]]:
        if "SELECT id, email, role, is_active" in self._last_query:
            return list(self._state["user_rows"])
        if "SELECT id, full_name, email, role, is_active, organization_id, created_at, updated_at" in self._last_query:
            return list(self._state["contact_rows"])
        return []


class _FakeConnection:
    def __init__(self, state: dict[str, Any]) -> None:
        self._state = state

    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self._state)


class _FakePsycopg:
    def __init__(self, state: dict[str, Any]) -> None:
        self._state = state

    def connect(self, database_url: str) -> _FakeConnection:
        self._state["connect_urls"].append(database_url)
        return _FakeConnection(self._state)


def _fake_state() -> dict[str, Any]:
    return {
        "queries": [],
        "connect_urls": [],
        "user_rows": [
            ("usr_provider", "provider@accmed.com.br", "provider", True, "pbkdf2_sha256$demo_hash"),
        ],
        "contact_rows": [
            (
                "usr_provider",
                "Nome Provider",
                "provider@accmed.com.br",
                "provider",
                True,
                "1",
                "2026-01-01T00:00:00Z",
                "2026-01-02T00:00:00Z",
                "pbkdf2_sha256$demo_hash",
            ),
        ],
    }


def test_user_repository_reads_password_hash_from_supabase_when_column_exists(monkeypatch) -> None:
    state = _fake_state()
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://runtime-db")
    monkeypatch.setattr(user_repository_module, "psycopg", _FakePsycopg(state))

    repository = user_repository_module.UserRepository()
    user = repository.get_by_email("provider@accmed.com.br")

    assert user is not None
    assert user["password_hash"] == "pbkdf2_sha256$demo_hash"
    assert any("COALESCE(password_hash, '') AS password_hash" in query for query in state["queries"])


def test_contact_user_repository_reads_password_hash_from_supabase_when_column_exists(monkeypatch) -> None:
    state = _fake_state()
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://runtime-db")
    monkeypatch.setattr(contact_user_repository_module, "psycopg", _FakePsycopg(state))

    repository = contact_user_repository_module.ContactUserRepository()
    user = repository.get_by_email("provider@accmed.com.br")

    assert user is not None
    assert user["password_hash"] == "pbkdf2_sha256$demo_hash"
    assert any("COALESCE(password_hash, '') AS password_hash" in query for query in state["queries"])
