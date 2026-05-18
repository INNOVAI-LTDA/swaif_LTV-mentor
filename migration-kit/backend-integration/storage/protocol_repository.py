from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.storage.json_repository import JsonRepository


def default_protocol_store_path() -> Path:
    configured = os.getenv("PROTOCOL_STORE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "protocols.json"


def _slugify(value: str) -> str:
    return "-".join(value.strip().lower().split())


class ProtocolRepository:
    def __init__(self, file_path: str | Path | None = None) -> None:
        self._store = JsonRepository(file_path or default_protocol_store_path())
        if not self._store.file_path.exists():
            self._store.write({"version": 1, "items": []})

    def _read_items(self) -> list[dict[str, Any]]:
        payload = self._store.read()
        items = payload.get("items", [])
        return [item for item in items if isinstance(item, dict)]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        self._store.write({"version": 1, "items": items})

    def list_protocols(self) -> list[dict[str, Any]]:
        return self._read_items()

    def list_by_organization(self, organization_id: str) -> list[dict[str, Any]]:
        return [
            protocol
            for protocol in self._read_items()
            if str(protocol.get("organization_id") or "") == organization_id
        ]

    def create(self, *, organization_id: str, name: str, code: str | None = None, metadata: dict | None = None) -> dict[str, Any]:
        items = self._read_items()
        final_code = _slugify(code or name)
        if any(str(item.get("code")) == final_code for item in items):
            raise ValueError("protocol code already exists")

        protocol = {
            "id": f"prt_{len(items) + 1}",
            "organization_id": organization_id,
            "name": name,
            "code": final_code,
            "metadata": metadata or {},
            "is_active": True,
        }
        items.append(protocol)
        self._write_items(items)
        return protocol

    def get_by_id(self, protocol_id: str) -> dict[str, Any] | None:
        for protocol in self._read_items():
            if str(protocol.get("id")) == protocol_id:
                return protocol
        return None
