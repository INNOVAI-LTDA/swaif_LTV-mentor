from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.storage.json_repository import JsonRepository


def default_analytical_history_store_path() -> Path:
    configured = os.getenv("ANALYTICAL_HISTORY_STORE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "analytical_history.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class AnalyticalHistoryRepository:
    def __init__(self, file_path: str | Path | None = None) -> None:
        self._store = JsonRepository(file_path or default_analytical_history_store_path())
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

    def list_by_enrollment(self, enrollment_id: str) -> list[dict[str, Any]]:
        return [
            item
            for item in self._read_items()
            if str(item.get("enrollment_id") or "") == enrollment_id
        ]

    def list_by_product(self, product_id: str) -> list[dict[str, Any]]:
        return [
            item
            for item in self._read_items()
            if str(item.get("product_id") or "") == product_id
        ]

    def append_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        items = self._read_items()
        record = {
            "id": str(payload.get("id") or f"anh_{len(items) + 1}"),
            "event_type": str(payload.get("event_type") or "unknown"),
            "enrollment_id": str(payload.get("enrollment_id") or "") or None,
            "product_id": str(payload.get("product_id") or "") or None,
            "pillar_id": str(payload.get("pillar_id") or "") or None,
            "scoring_rule_version": str(payload.get("scoring_rule_version") or "") or None,
            "projection_formula_version": str(payload.get("projection_formula_version") or "") or None,
            "source_effective_at": str(payload.get("source_effective_at") or "") or None,
            "payload": payload.get("payload") if isinstance(payload.get("payload"), dict) else {},
            "created_at": str(payload.get("created_at") or _now_iso()),
        }
        items.append(record)
        self._write_items(items)
        return record