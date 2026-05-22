from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.storage.admin_database_view_repository import AdminDatabaseViewRepository

logger = logging.getLogger("swaif.runtime")


@dataclass(frozen=True)
class TablePage:
    table: str
    items: list[dict[str, Any]]
    total: int
    limit: int
    offset: int


class AdminDatabaseViewService:
    def __init__(self, repository: AdminDatabaseViewRepository) -> None:
        self._repository = repository

    def list_tables(self) -> list[str]:
        return self._repository.list_tables()

    def list_records(self, *, table: str, limit: int, offset: int) -> TablePage:
        items, total = self._repository.list_records(table=table, limit=limit, offset=offset)
        return TablePage(table=table, items=items, total=total, limit=limit, offset=offset)

    def update_record(self, *, admin_id: str, table: str, record_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        updated = self._repository.update_record(table=table, record_id=record_id, changes=changes)
        logger.critical(
            "admin_database_view_data_changed urgency=critical admin_id=%s table=%s record_id=%s changed_fields=%s",
            admin_id,
            table,
            record_id,
            ",".join(sorted(changes.keys())),
        )
        return updated
