from __future__ import annotations

from typing import Any

from app.storage import supabase_provider_hierarchy_repository as repository_module


class _FakeCursor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self._result_rows: list[dict[str, Any]] = []
        self.description = [
            ("enrollment_id",),
            ("enrollment_status",),
            ("start_day",),
            ("days_left",),
            ("investment",),
            ("decision_matrix_status",),
            ("provider_id",),
            ("provider_name",),
            ("provider_email",),
            ("provider_organization_id",),
            ("client_id",),
            ("client_name",),
            ("client_email",),
            ("product_id",),
            ("product_name",),
            ("product_slug",),
            ("product_category",),
            ("organization_id",),
            ("organization_name",),
            ("organization_slug",),
        ]

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, query: str, params: tuple[Any, ...] | None = None) -> None:
        provider_user_id = str((params or ("",))[0])
        _ = query
        self._result_rows = [
            row
            for row in self._rows
            if str(row["provider_id"]) == provider_user_id and str(row["enrollment_status"]) == "active"
        ]

    def fetchall(self) -> list[tuple[Any, ...]]:
        return [
            (
                row["enrollment_id"],
                row["enrollment_status"],
                row["start_day"],
                row["days_left"],
                row["investment"],
                row["decision_matrix_status"],
                row["provider_id"],
                row["provider_name"],
                row["provider_email"],
                row["provider_organization_id"],
                row["client_id"],
                row["client_name"],
                row["client_email"],
                row["product_id"],
                row["product_name"],
                row["product_slug"],
                row["product_category"],
                row["organization_id"],
                row["organization_name"],
                row["organization_slug"],
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


def test_list_active_provider_hierarchy_is_scoped_by_provider(monkeypatch) -> None:
    rows = [
        {
            "enrollment_id": "enr-1",
            "enrollment_status": "active",
            "start_day": "2026-01-01",
            "days_left": 20,
            "investment": 10000.0,
            "decision_matrix_status": "rescue",
            "provider_id": "10",
            "provider_name": "Provider A",
            "provider_email": "provider.a@example.com",
            "provider_organization_id": "1",
            "client_id": "100",
            "client_name": "Client A",
            "client_email": "client.a@example.com",
            "product_id": "1000",
            "product_name": "Produto A",
            "product_slug": "produto-a",
            "product_category": "mentoria",
            "organization_id": "1",
            "organization_name": "Org A",
            "organization_slug": "org-a",
        },
        {
            "enrollment_id": "enr-2",
            "enrollment_status": "active",
            "start_day": "2026-01-02",
            "days_left": 25,
            "investment": 12000.0,
            "decision_matrix_status": "topRight",
            "provider_id": "99",
            "provider_name": "Provider B",
            "provider_email": "provider.b@example.com",
            "provider_organization_id": "2",
            "client_id": "200",
            "client_name": "Client B",
            "client_email": "client.b@example.com",
            "product_id": "2000",
            "product_name": "Produto B",
            "product_slug": "produto-b",
            "product_category": "mentoria",
            "organization_id": "2",
            "organization_name": "Org B",
            "organization_slug": "org-b",
        },
    ]
    monkeypatch.setattr(repository_module, "psycopg", _FakePsycopg(rows))

    repository = repository_module.SupabaseProviderHierarchyRepository(database_url="postgresql://runtime-db")
    result = repository.list_active_provider_hierarchy("10")

    assert len(result) == 1
    assert result[0]["provider_id"] == "10"
    assert result[0]["client_id"] == "100"
    assert result[0]["enrollment_id"] == "enr-1"
