from __future__ import annotations

from typing import Any

from app.storage import supabase_runtime_checkpoint_repository as repository_module


class _FakeCursor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self._result_rows: list[dict[str, Any]] = []
        self.description = [
            ("id",),
            ("enrollment_id",),
            ("week",),
            ("status",),
            ("label",),
            ("created_at",),
            ("updated_at",),
        ]

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, query: str, params: tuple[Any, ...] | None = None) -> None:
        _ = query
        enrollment_id = str((params or ("",))[0])
        filtered = [row for row in self._rows if str(row["enrollment_id"]) == enrollment_id]
        self._result_rows = sorted(filtered, key=lambda row: int(row["week"]))

    def fetchall(self) -> list[tuple[Any, ...]]:
        return [
            (
                row["id"],
                row["enrollment_id"],
                row["week"],
                row["status"],
                row["label"],
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


def test_list_by_enrollment_orders_by_week_ascending(monkeypatch) -> None:
    rows = [
        {"id": 3, "enrollment_id": 100, "week": 4, "status": "done", "label": "W4", "created_at": "", "updated_at": ""},
        {"id": 2, "enrollment_id": 100, "week": 2, "status": "done", "label": "W2", "created_at": "", "updated_at": ""},
        {"id": 1, "enrollment_id": 100, "week": 1, "status": "done", "label": "W1", "created_at": "", "updated_at": ""},
    ]
    monkeypatch.setattr(repository_module, "psycopg", _FakePsycopg(rows))

    repository = repository_module.SupabaseRuntimeCheckpointRepository(database_url="postgresql://runtime-db")
    result = repository.list_by_enrollment("100")

    assert [item["week"] for item in result] == [1, 2, 4]
    assert all(item["enrollment_id"] == "100" for item in result)
