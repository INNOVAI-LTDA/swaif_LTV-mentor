
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

def default_metric_store_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "metrics.json"


def _slugify(value: str) -> str:
    return "-".join(value.strip().lower().split())


def _default_scoring_rules_v2() -> dict[str, Any]:
    return {
        "version": 2,
        "input": {"kind": "number"},
        "scoring": {
            "mode": "first_match",
            "rules": [],
            "fallback": {"assign": 0},
        },
        "normalization": {
            "basis": "max_score",
            "value": 1,
        },
    }


class MetricRepository:
    _memory_stores: dict[str, list[dict[str, Any]]] = {}
    _memory_lock = RLock()

    def __init__(self, file_path: str | Path | None = None) -> None:
        self._namespace = str((file_path or default_metric_store_path()).resolve())
        if self._namespace not in self._memory_stores:
            self._memory_stores[self._namespace] = []

    def _memory_items(self) -> list[dict[str, Any]]:
        with self._memory_lock:
            return self._memory_stores.get(self._namespace, [])

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        with self._memory_lock:
            self._memory_stores[self._namespace] = [dict(item) for item in items]

    def _read_items(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._memory_items() if isinstance(item, dict) and item.get("deleted_at") is None]

    def list_metrics(self) -> list[dict[str, Any]]:
        return self._read_items()

    def list_by_pillar(self, pillar_id: int) -> list[dict[str, Any]]:
        return [
            item
            for item in self._read_items()
            if int(item.get("pillar_id") or 0) == int(pillar_id)
        ]

    def create(
        self,
        *,
        protocol_id: int,
        pillar_id: int,
        name: str,
        code: str | None = None,
        direction: str = "higher_better",
        unit: str | None = None,
        scoring_rules: list[dict[str, Any]] | dict[str, Any] | None = None,
        score_type: str | None = None,
        min_score: int | None = None,
        max_score: int | None = None,
        mcv_score: int | None = None,
        max_basis_score: str | None = None,
    ) -> dict[str, Any]:
        items = self._read_items()
        final_code = _slugify(code or name)
        if any(int(item.get("pillar_id") or 0) == int(pillar_id) and str(item.get("code")) == final_code for item in items):
            raise ValueError("metric code already exists in pillar")
        if any(int(item.get("pillar_id") or 0) == int(pillar_id) and str(item.get("name")) == name for item in items):
            raise ValueError("metric name already exists in pillar")
        new_id = max([m["id"] for m in items if "id" in m and isinstance(m["id"], int)] + [0]) + 1
        metric = {
            "id": new_id,
            "protocol_id": protocol_id,
            "pillar_id": pillar_id,
            "name": name,
            "code": final_code,
            "direction": direction,
            "unit": unit,
            "scoring_rules": _default_scoring_rules_v2() if scoring_rules is None else scoring_rules,
            "score_type": score_type or "static",
            "min_score": 0 if min_score is None else min_score,
            "max_score": 1 if max_score is None else max_score,
            "mcv_score": 1 if mcv_score is None else mcv_score,
            "max_basis_score": max_basis_score or "MAX_VALUE",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "deleted_at": None,
        }
        items.append(metric)
        self._write_items(items)
        return metric

    def get_by_id(self, metric_id: int) -> dict[str, Any] | None:
        for metric in self._read_items():
            if int(metric.get("id") or 0) == int(metric_id):
                return metric
        return None

    def update(self, **kwargs) -> dict[str, Any]:
        metric_id = kwargs.get("id")
        if not metric_id:
            raise ValueError("Metric id is required for update")
        items = self._read_items()
        for idx, metric in enumerate(items):
            if int(metric.get("id") or 0) == int(metric_id):
                updated = {**metric, **kwargs}
                items[idx] = updated
                self._write_items(items)
                return updated
        raise ValueError(f"Metric with id {metric_id} not found")

    def soft_delete(self, metric_id: int) -> bool:
        items = self._read_items()
        for metric in items:
            if int(metric.get("id") or 0) == int(metric_id):
                metric["deleted_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                self._write_items(items)
                return True
        return False
