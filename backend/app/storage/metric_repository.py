from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.storage.json_repository import JsonRepository


def default_metric_store_path() -> Path:
    configured = os.getenv("METRIC_STORE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "metrics.json"


def _slugify(value: str) -> str:
    return "-".join(value.strip().lower().split())


class MetricRepository:
    def update(self, **kwargs) -> dict[str, Any]:
        metric_id = kwargs.get("id")
        if not metric_id:
            raise ValueError("Metric id is required for update")
        items = self._read_items()
        for idx, metric in enumerate(items):
            if str(metric.get("id")) == metric_id:
                updated = {**metric, **kwargs}
                items[idx] = updated
                self._write_items(items)
                return updated
        raise ValueError(f"Metric with id {metric_id} not found")

    def delete(self, metric_id: str) -> bool:
        items = self._read_items()
        new_items = [metric for metric in items if str(metric.get("id")) != metric_id]
        if len(new_items) == len(items):
            return False
        self._write_items(new_items)
        return True
    def __init__(self, file_path: str | Path | None = None) -> None:
        self._store = JsonRepository(file_path or default_metric_store_path())
        if not self._store.file_path.exists():
            self._store.write({"version": 1, "items": []})

    def _read_items(self) -> list[dict[str, Any]]:
        payload = self._store.read()
        items = payload.get("items", [])
        return [item for item in items if isinstance(item, dict)]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        self._store.write({"version": 1, "items": items})

    def list_metrics(self) -> list[dict[str, Any]]:
        return self._read_items()

    def list_by_pillar(self, pillar_id: str) -> list[dict[str, Any]]:
        return [
            item
            for item in self._read_items()
            if str(item.get("pillar_id") or "") == pillar_id
        ]

    def create(
        self,
        *,
        protocol_id: str,
        pillar_id: str,
        name: str,
        code: str | None = None,
        direction: str = "higher_better",
        unit: str | None = None,
        scoring_rules: list[dict] | None = None,
        score_type: str | None = None,
        min_score: int | None = None,
        max_score: int | None = None,
        mcv_score: int | None = None,
        max_basis_score: str | None = None,
    ) -> dict[str, Any]:
        items = self._read_items()
        final_code = _slugify(code or name)
        if any(str(item.get("pillar_id")) == pillar_id and str(item.get("code")) == final_code for item in items):
            raise ValueError("metric code already exists in pillar")
        if any(str(item.get("pillar_id")) == pillar_id and str(item.get("name")) == name for item in items):
            raise ValueError("metric name already exists in pillar")
        metric = {
            "id": f"met_{len(items) + 1}",
            "protocol_id": protocol_id,
            "pillar_id": pillar_id,
            "name": name,
            "code": final_code,
            "direction": direction,
            "unit": unit,
            "scoring_rules": scoring_rules or [],
            "score_type": score_type,
            "min_score": min_score,
            "max_score": max_score,
            "mcv_score": mcv_score,
            "max_basis_score": max_basis_score,
            "is_active": True,
        }
        items.append(metric)
        self._write_items(items)
        return metric

    def get_by_id(self, metric_id: str) -> dict[str, Any] | None:
        for metric in self._read_items():
            if str(metric.get("id")) == metric_id:
                return metric
        return None
