from __future__ import annotations

from typing import Any

from app.storage import supabase_runtime_measurement_repository as repository_module


class _FakeCursor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self._result_rows: list[dict[str, Any]] = []
        self.description = [
            ("id",),
            ("enrollment_id",),
            ("metric_id",),
            ("value_baseline",),
            ("value_current",),
            ("value_projected",),
            ("improving_trend",),
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
        self._result_rows = sorted(filtered, key=lambda row: str(row["metric_id"]))

    def fetchall(self) -> list[tuple[Any, ...]]:
        return [
            (
                row["id"],
                row["enrollment_id"],
                row["metric_id"],
                row["value_baseline"],
                row["value_current"],
                row["value_projected"],
                row["improving_trend"],
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


def test_list_by_enrollment_normalizes_ids_as_string(monkeypatch) -> None:
    rows = [
        {
            "id": 1,
            "enrollment_id": 100,
            "metric_id": 2,
            "value_baseline": 1.0,
            "value_current": 2.0,
            "value_projected": 3.0,
            "improving_trend": True,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T01:00:00Z",
        },
        {
            "id": 2,
            "enrollment_id": 100,
            "metric_id": 1,
            "value_baseline": 4.0,
            "value_current": 5.0,
            "value_projected": 6.0,
            "improving_trend": False,
            "created_at": "2026-01-02T00:00:00Z",
            "updated_at": "2026-01-02T01:00:00Z",
        },
    ]
    monkeypatch.setattr(repository_module, "psycopg", _FakePsycopg(rows))

    repository = repository_module.SupabaseRuntimeMeasurementRepository(database_url="postgresql://runtime-db")
    result = repository.list_by_enrollment("100")

    assert len(result) == 2
    assert [item["metric_id"] for item in result] == ["1", "2"]
    assert all(isinstance(item["id"], str) for item in result)
    assert all(item["enrollment_id"] == "100" for item in result)
