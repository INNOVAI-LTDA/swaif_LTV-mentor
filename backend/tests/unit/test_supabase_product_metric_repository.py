from __future__ import annotations

from typing import Any

from app.storage import supabase_product_metric_repository as repository_module


class _FakeCursor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.description = [
            ("pillar_id",),
            ("pillar_name",),
            ("pillar_slug",),
            ("pillar_order_index",),
            ("metric_id",),
            ("metric_name",),
            ("metric_slug",),
            ("direction",),
            ("unit",),
            ("scoring_rules",),
            ("score_type",),
            ("min_score",),
            ("max_score",),
            ("max_score_basis",),
            ("mcv",),
        ]
        self._result_rows: list[dict[str, Any]] = []

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, query: str, params: tuple[Any, ...] | None = None) -> None:
        _ = query
        product_id = str((params or ("",))[0])
        self._result_rows = [row for row in self._rows if str(row["product_id"]) == product_id]

    def fetchall(self) -> list[tuple[Any, ...]]:
        return [
            (
                row["pillar_id"],
                row["pillar_name"],
                row["pillar_slug"],
                row["pillar_order_index"],
                row["metric_id"],
                row["metric_name"],
                row["metric_slug"],
                row["direction"],
                row["unit"],
                row["scoring_rules"],
                row["score_type"],
                row["min_score"],
                row["max_score"],
                row["max_score_basis"],
                row["mcv"],
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


def test_list_metric_tree_by_product_groups_metrics_by_pillar(monkeypatch) -> None:
    rows = [
        {
            "product_id": "1000",
            "pillar_id": "p1",
            "pillar_name": "Pilar 1",
            "pillar_slug": "pilar-1",
            "pillar_order_index": 1,
            "metric_id": "m1",
            "metric_name": "Metrica 1",
            "metric_slug": "metrica-1",
            "direction": "up",
            "unit": "pct",
            "scoring_rules": {},
            "score_type": "range",
            "min_score": 0,
            "max_score": 100,
            "max_score_basis": "percent",
            "mcv": None,
        },
        {
            "product_id": "1000",
            "pillar_id": "p1",
            "pillar_name": "Pilar 1",
            "pillar_slug": "pilar-1",
            "pillar_order_index": 1,
            "metric_id": "m2",
            "metric_name": "Metrica 2",
            "metric_slug": "metrica-2",
            "direction": "down",
            "unit": "abs",
            "scoring_rules": {},
            "score_type": "range",
            "min_score": 0,
            "max_score": 10,
            "max_score_basis": "absolute",
            "mcv": None,
        },
        {
            "product_id": "2000",
            "pillar_id": "p2",
            "pillar_name": "Pilar 2",
            "pillar_slug": "pilar-2",
            "pillar_order_index": 1,
            "metric_id": "m3",
            "metric_name": "Metrica 3",
            "metric_slug": "metrica-3",
            "direction": "up",
            "unit": "pct",
            "scoring_rules": {},
            "score_type": "range",
            "min_score": 0,
            "max_score": 100,
            "max_score_basis": "percent",
            "mcv": None,
        },
    ]
    monkeypatch.setattr(repository_module, "psycopg", _FakePsycopg(rows))

    repository = repository_module.SupabaseProductMetricRepository(database_url="postgresql://runtime-db")
    tree = repository.list_metric_tree_by_product("1000")

    assert len(tree) == 1
    assert tree[0]["id"] == "p1"
    assert len(tree[0]["metrics"]) == 2
    assert [metric["id"] for metric in tree[0]["metrics"]] == ["m1", "m2"]
