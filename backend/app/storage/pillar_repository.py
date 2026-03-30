from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.storage.json_repository import JsonRepository


def default_pillar_store_path() -> Path:
    configured = os.getenv("PILLAR_STORE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "pillars.json"


def _slugify(value: str) -> str:
    return "-".join(value.strip().lower().split())


class PillarRepository:
    def update(self, **kwargs) -> dict[str, Any]:
        pillar_id = kwargs.get("id")
        if not pillar_id:
            raise ValueError("Pillar id is required for update")
        items = self._read_items()
        for idx, pillar in enumerate(items):
            if str(pillar.get("id")) == pillar_id:
                updated = {**pillar, **kwargs}
                items[idx] = updated
                self._write_items(items)
                return updated
        raise ValueError(f"Pillar with id {pillar_id} not found")

    def delete(self, pillar_id: str) -> bool:
        items = self._read_items()
        new_items = [pillar for pillar in items if str(pillar.get("id")) != pillar_id]
        if len(new_items) == len(items):
            return False
        self._write_items(new_items)
        return True
    def __init__(self, file_path: str | Path | None = None) -> None:
        self._store = JsonRepository(file_path or default_pillar_store_path())
        if not self._store.file_path.exists():
            self._store.write({"version": 1, "items": []})

    def _read_items(self) -> list[dict[str, Any]]:
        payload = self._store.read()
        items = payload.get("items", [])
        return [item for item in items if isinstance(item, dict)]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        self._store.write({"version": 1, "items": items})

    def list_pillars(self) -> list[dict[str, Any]]:
        return self._read_items()

    def create(
        self,
        *,
        protocol_id: str,
        name: str,
        code: str | None = None,
        order_index: int = 0,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        items = self._read_items()
        final_code = _slugify(code or name)
        if any(str(item.get("protocol_id")) == protocol_id and str(item.get("code")) == final_code for item in items):
            raise ValueError("pillar code already exists in protocol")
        if any(str(item.get("protocol_id")) == protocol_id and str(item.get("name")) == name for item in items):
            raise ValueError("pillar name already exists in protocol")
        pillar = {
            "id": f"plr_{len(items) + 1}",
            "protocol_id": protocol_id,
            "name": name,
            "code": final_code,
            "order_index": int(order_index),
            "metadata": metadata or {},
            "is_active": True,
        }
        items.append(pillar)
        self._write_items(items)
        return pillar

    def get_by_id(self, pillar_id: str) -> dict[str, Any] | None:
        for pillar in self._read_items():
            if str(pillar.get("id")) == pillar_id:
                return pillar
        return None
