from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.storage.json_repository import JsonRepository


def default_checkpoint_store_path() -> Path:
    configured = os.getenv("CHECKPOINT_STORE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "checkpoints.json"


class CheckpointRepository:
    def __init__(self, file_path: str | Path | None = None) -> None:
        self._store = JsonRepository(file_path or default_checkpoint_store_path())
        if not self._store.file_path.exists():
            self._store.write({"version": 1, "items": []})

    def _read_items(self) -> list[dict[str, Any]]:
        payload = self._store.read()
        items = payload.get("items", [])
        return [item for item in items if isinstance(item, dict)]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        self._store.write({"version": 1, "items": items})

    def list_checkpoints(self) -> list[dict[str, Any]]:
        return self._read_items()

    def list_by_enrollment(self, enrollment_id: str) -> list[dict[str, Any]]:
        return [item for item in self._read_items() if str(item.get("enrollment_id")) == enrollment_id]

    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        items = [item for item in self._read_items() if str(item.get("enrollment_id")) != enrollment_id]
        created: list[dict[str, Any]] = []
        for row in rows:
            record = {
                "id": f"chk_{len(items) + len(created) + 1}",
                "enrollment_id": enrollment_id,
                "week": int(row["week"]),
                "status": str(row["status"]),
                "label": row.get("label"),
            }
            created.append(record)
        items.extend(created)
        self._write_items(items)
        return created
