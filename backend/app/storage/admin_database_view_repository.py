from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.storage.json_repository import JsonRepository
from app.storage.store_registry import resolve_registered_store_paths


@dataclass(frozen=True)
class TableRef:
    name: str
    repo: JsonRepository


class AdminDatabaseViewRepository:
    def _tables(self) -> list[TableRef]:
        return [TableRef(name=name, repo=JsonRepository(path)) for name, path in resolve_registered_store_paths()]

    def list_tables(self) -> list[str]:
        return [table.name for table in self._tables()]

    def list_records(self, *, table: str, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        table_ref = next((item for item in self._tables() if item.name == table), None)
        if table_ref is None:
            raise KeyError("table_not_allowed")
        payload = table_ref.repo.read()
        items = payload.get("items")
        if not isinstance(items, list):
            return [], 0
        total = len(items)
        chunk = items[offset : offset + limit]
        result = [item for item in chunk if isinstance(item, dict)]
        return result, total

    def update_record(self, *, table: str, record_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        table_ref = next((item for item in self._tables() if item.name == table), None)
        if table_ref is None:
            raise KeyError("table_not_allowed")
        payload = table_ref.repo.read()
        items = payload.get("items")
        if not isinstance(items, list):
            raise KeyError("record_not_found")
        for idx, item in enumerate(items):
            if isinstance(item, dict) and str(item.get("id")) == record_id:
                updated = {**item, **changes}
                items[idx] = updated
                table_ref.repo.write(payload)
                return updated
        raise KeyError("record_not_found")
