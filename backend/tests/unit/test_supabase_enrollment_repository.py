from __future__ import annotations

from typing import Any

from app.storage import supabase_enrollment_repository as repository_module


class _FakeCursor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self._result_rows: list[dict[str, Any]] = []
        self.description = [
            ("id",),
            ("provider_user_id",),
            ("client_user_id",),
            ("product_id",),
            ("start_day",),
            ("days_left",),
            ("investment",),
            ("decision_matrix_status",),
            ("status",),
            ("created_at",),
            ("updated_at",),
        ]

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, query: str, params: tuple[Any, ...] | None = None) -> None:
        provider_user_id = str((params or ("",))[0])
        _ = query
        filtered = [
            row
            for row in self._rows
            if str(row["provider_user_id"]) == provider_user_id and str(row["status"]) == "active"
        ]
        self._result_rows = sorted(
            filtered,
            key=lambda row: (row["updated_at"], row["id"]),
            reverse=True,
        )

    def fetchall(self) -> list[tuple[Any, ...]]:
        return [
            (
                row["id"],
                row["provider_user_id"],
                row["client_user_id"],
                row["product_id"],
                row["start_day"],
                row["days_left"],
                row["investment"],
                row["decision_matrix_status"],
                row["status"],
                row["created_at"],
                row["updated_at"],
            )
            for row in self._result_rows
        ]


class _FakeConnection:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self._rows)


class _FakePsycopg:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def connect(self, database_url: str) -> _FakeConnection:
        _ = database_url
        return _FakeConnection(self._rows)


def test_list_active_by_provider_returns_only_active_rows_with_string_ids(monkeypatch) -> None:
    rows = [
        {
            "id": 100,
            "provider_user_id": 10,
            "client_user_id": 1000,
            "product_id": 5000,
            "start_day": "2026-01-01",
            "days_left": 20,
            "investment": 10000.0,
            "decision_matrix_status": "rescue",
            "status": "active",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-10T00:00:00Z",
        },
        {
            "id": 101,
            "provider_user_id": 10,
            "client_user_id": 1001,
            "product_id": 5001,
            "start_day": "2026-01-02",
            "days_left": 15,
            "investment": 12000.0,
            "decision_matrix_status": "topRight",
            "status": "active",
            "created_at": "2026-01-02T00:00:00Z",
            "updated_at": "2026-01-11T00:00:00Z",
        },
        {
            "id": 102,
            "provider_user_id": 10,
            "client_user_id": 1002,
            "product_id": 5002,
            "start_day": "2026-01-03",
            "days_left": 8,
            "investment": 13000.0,
            "decision_matrix_status": "critical",
            "status": "inactive",
            "created_at": "2026-01-03T00:00:00Z",
            "updated_at": "2026-01-12T00:00:00Z",
        },
        {
            "id": 103,
            "provider_user_id": 99,
            "client_user_id": 1003,
            "product_id": 5003,
            "start_day": "2026-01-04",
            "days_left": 5,
            "investment": 14000.0,
            "decision_matrix_status": "critical",
            "status": "active",
            "created_at": "2026-01-04T00:00:00Z",
            "updated_at": "2026-01-13T00:00:00Z",
        },
    ]
    monkeypatch.setattr(repository_module, "psycopg", _FakePsycopg(rows))

    repository = repository_module.SupabaseEnrollmentRepository(database_url="postgresql://runtime-db")
    result = repository.list_active_by_provider("10")

    assert len(result) == 2
    assert [item["id"] for item in result] == ["101", "100"]
    assert all(item["status"] == "active" for item in result)
    assert all(isinstance(item["id"], str) for item in result)
    assert all(isinstance(item["provider_user_id"], str) for item in result)
    assert all(isinstance(item["client_user_id"], str) for item in result)
    assert all(isinstance(item["product_id"], str) for item in result)
