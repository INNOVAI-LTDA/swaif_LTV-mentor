from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.storage.json_repository import JsonRepository


def default_client_store_path() -> Path:
    configured = os.getenv("CLIENT_STORE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "clients.json"


def _slugify(value: str) -> str:
    compact = "-".join(value.strip().lower().split())
    return compact or "cliente"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ClientRepository:
    def update(self, **kwargs) -> dict[str, Any]:
        client_id = kwargs.get("id")
        if not client_id:
            raise ValueError("Client id is required for update")
        items = self._read_items()
        for idx, client in enumerate(items):
            if str(client.get("id")) == client_id:
                updated = {**client, **kwargs, "updated_at": _now_iso()}
                items[idx] = updated
                self._write_items(items)
                return updated
        raise ValueError(f"Client with id {client_id} not found")

    def delete(self, client_id: str) -> bool:
        items = self._read_items()
        new_items = [client for client in items if str(client.get("id")) != client_id]
        if len(new_items) == len(items):
            return False
        self._write_items(new_items)
        return True
    def __init__(self, file_path: str | Path | None = None) -> None:
        self._store = JsonRepository(file_path or default_client_store_path())
        if not self._store.file_path.exists():
            self._store.write({"version": 1, "items": []})

    def _read_items(self) -> list[dict[str, Any]]:
        payload = self._store.read()
        items = payload.get("items", [])
        return [item for item in items if isinstance(item, dict)]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        self._store.write({"version": 1, "items": items})

    def list_clients(self) -> list[dict[str, Any]]:
        return self._read_items()

    def create(
        self,
        *,
        name: str,
        cnpj: str,
        slug: str | None = None,
        brand_name: str | None = None,
        timezone_name: str = "America/Sao_Paulo",
        currency: str = "BRL",
        notes: str | None = None,
    ) -> dict[str, Any]:
        items = self._read_items()
        candidate_slug = _slugify(slug or name)

        if any(str(item.get("cnpj")) == cnpj for item in items):
            raise ValueError("client cnpj already exists")
        if any(str(item.get("slug")) == candidate_slug for item in items):
            raise ValueError("client slug already exists")

        now = _now_iso()
        client = {
            "id": f"cli_{len(items) + 1}",
            "name": name,
            "brand_name": brand_name or name,
            "cnpj": cnpj,
            "slug": candidate_slug,
            "status": "active",
            "is_active": True,
            "timezone": timezone_name,
            "currency": currency,
            "notes": notes,
            "created_at": now,
            "updated_at": now,
        }
        items.append(client)
        self._write_items(items)
        return client

    def get_by_id(self, client_id: str) -> dict[str, Any] | None:
        for client in self._read_items():
            if str(client.get("id")) == client_id:
                return client
        return None
