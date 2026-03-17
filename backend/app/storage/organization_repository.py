from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.storage.json_repository import JsonRepository


def default_organization_store_path() -> Path:
    configured = os.getenv("ORG_STORE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "organizations.json"


def _slugify(value: str) -> str:
    return "-".join(value.strip().lower().split())


def _normalize_code(value: str) -> str:
    compact = "-".join(part for part in value.strip().upper().replace("_", " ").split() if part)
    return compact or "PRODUTO"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class OrganizationRepository:
    def __init__(self, file_path: str | Path | None = None) -> None:
        self._store = JsonRepository(file_path or default_organization_store_path())
        if not self._store.file_path.exists():
            self._store.write({"version": 1, "items": []})

    def _read_items(self) -> list[dict[str, Any]]:
        payload = self._store.read()
        items = payload.get("items", [])
        return [item for item in items if isinstance(item, dict)]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        self._store.write({"version": 1, "items": items})

    def list_organizations(self) -> list[dict[str, Any]]:
        return self._read_items()

    def list_by_client(self, client_id: str) -> list[dict[str, Any]]:
        return [
            item
            for item in self._read_items()
            if str(item.get("client_id") or "") == client_id
        ]

    def create(
        self,
        *,
        name: str,
        slug: str | None = None,
        client_id: str | None = None,
        code: str | None = None,
        description: str | None = None,
        delivery_model: str | None = None,
    ) -> dict[str, Any]:
        items = self._read_items()
        candidate_slug = _slugify(slug or name)
        candidate_code = _normalize_code(code or candidate_slug or name)

        def _same_scope(item: dict[str, Any]) -> bool:
            return str(item.get("client_id") or "") == str(client_id or "")

        if any(_same_scope(item) and str(item.get("slug")) == candidate_slug for item in items):
            raise ValueError("organization slug already exists")
        if any(_same_scope(item) and str(item.get("code")) == candidate_code for item in items):
            raise ValueError("organization code already exists")

        now = _now_iso()

        organization = {
            "id": f"org_{len(items) + 1}",
            "name": name,
            "slug": candidate_slug,
            "code": candidate_code,
            "client_id": client_id,
            "mentor_id": None,
            "description": description,
            "delivery_model": delivery_model or "live",
            "status": "active",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        items.append(organization)
        self._write_items(items)
        return organization

    def get_by_id(self, organization_id: str) -> dict[str, Any] | None:
        for organization in self._read_items():
            if str(organization.get("id")) == organization_id:
                return organization
        return None

    def set_mentor(self, organization_id: str, mentor_id: str) -> dict[str, Any] | None:
        items = self._read_items()
        for idx, organization in enumerate(items):
            if str(organization.get("id")) == organization_id:
                organization["mentor_id"] = mentor_id
                items[idx] = organization
                self._write_items(items)
                return organization
        return None
