from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.storage.json_repository import JsonRepository


def default_measurement_history_store_path() -> Path:
    configured = os.getenv("MEASUREMENT_HISTORY_STORE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "measurement_history.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class MeasurementHistoryRepository:
    def __init__(self, file_path: str | Path | None = None) -> None:
        self._store = JsonRepository(file_path or default_measurement_history_store_path())
        if not self._store.file_path.exists():
            self._store.write({"version": 1, "items": []})

    def _read_items(self) -> list[dict[str, Any]]:
        payload = self._store.read()
        items = payload.get("items", [])
        return [item for item in items if isinstance(item, dict)]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        self._store.write({"version": 1, "items": items})

    def list_events(self) -> list[dict[str, Any]]:
        return self._read_items()

    def list_by_measurement(self, measurement_id: str) -> list[dict[str, Any]]:
        return [
            item
            for item in self._read_items()
            if str(item.get("measurement_id") or "") == measurement_id
        ]

    def append_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        items = self._read_items()
        record = {
            "id": str(payload.get("id") or f"meh_{len(items) + 1}"),
            "measurement_id": str(payload.get("measurement_id") or ""),
            "enrollment_id": str(payload.get("enrollment_id") or ""),
            "metric_id": str(payload.get("metric_id") or ""),
            "actor_user_id": str(payload.get("actor_user_id") or "") or None,
            "actor_role": str(payload.get("actor_role") or "") or None,
            "value_absolute_before": None
            if payload.get("value_absolute_before") is None
            else float(payload.get("value_absolute_before")),
            "value_absolute_after": None
            if payload.get("value_absolute_after") is None
            else float(payload.get("value_absolute_after")),
            "value_relative_before": None
            if payload.get("value_relative_before") is None
            else float(payload.get("value_relative_before")),
            "value_relative_after": None
            if payload.get("value_relative_after") is None
            else float(payload.get("value_relative_after")),
            "rule_version": str(payload.get("rule_version") or "") or None,
            "created_at": str(payload.get("created_at") or _now_iso()),
        }
        items.append(record)
        self._write_items(items)
        return record
