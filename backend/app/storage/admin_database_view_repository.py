from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.operations.sync_runtime_stores_from_supabase import (
    SupabaseSyncConfig,
    _build_runtime_payloads,
    _fetch_source_rows,
)


@dataclass(frozen=True)
class TableRef:
    name: str
    items: list[dict[str, Any]]


class SupabaseDatabaseViewUnavailableError(RuntimeError):
    pass


class AdminDatabaseViewRepository:
    def __init__(
        self,
        *,
        database_url: str,
        default_admin_password: str,
        default_provider_password: str,
        default_client_password: str,
    ) -> None:
        self._database_url = database_url.strip()
        self._default_admin_password = default_admin_password
        self._default_provider_password = default_provider_password
        self._default_client_password = default_client_password

    def _runtime_payloads(self) -> dict[str, dict[str, Any]]:
        if not self._database_url:
            raise SupabaseDatabaseViewUnavailableError("supabase_db_url_required")
        try:
            source_rows = _fetch_source_rows(self._database_url)
        except Exception as exc:  # pragma: no cover - runtime DB availability/auth issues
            raise SupabaseDatabaseViewUnavailableError("supabase_connection_failed") from exc
        return _build_runtime_payloads(
            source_rows,
            SupabaseSyncConfig(
                database_url=self._database_url,
                default_admin_password=self._default_admin_password,
                default_provider_password=self._default_provider_password,
                default_client_password=self._default_client_password,
            ),
        )

    def _tables(self) -> list[TableRef]:
        payloads = self._runtime_payloads()
        tables: list[TableRef] = []
        for name, payload in payloads.items():
            if not isinstance(payload, dict):
                continue
            items = payload.get("items")
            if not isinstance(items, list):
                continue
            normalized_items = [item for item in items if isinstance(item, dict)]
            tables.append(TableRef(name=name, items=normalized_items))
        return tables

    def snapshot_payloads(self) -> dict[str, dict[str, Any]]:
        return self._runtime_payloads()

    def list_tables(self) -> list[str]:
        return [table.name for table in self._tables()]

    def list_records(self, *, table: str, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
        table_ref = next((item for item in self._tables() if item.name == table), None)
        if table_ref is None:
            raise KeyError("table_not_allowed")
        total = len(table_ref.items)
        chunk = table_ref.items[offset : offset + limit]
        result = [item for item in chunk if isinstance(item, dict)]
        return result, total

    def update_record(self, *, table: str, record_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        # Database View now loads strictly from Supabase-derived runtime payloads.
        # Direct mutation from this endpoint is intentionally disabled.
        raise KeyError("record_not_found")
