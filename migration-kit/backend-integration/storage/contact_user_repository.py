from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.storage.json_repository import JsonRepository


def default_contact_user_store_path() -> Path:
    configured = os.getenv("CONTACT_USER_STORE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "contacts_users_v2.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ContactUserRepository:
    def __init__(self, file_path: str | Path | None = None) -> None:
        self._store = JsonRepository(file_path or default_contact_user_store_path())
        if not self._store.file_path.exists():
            self._store.write({"version": 2, "items": []})

    def _read_items(self) -> list[dict[str, Any]]:
        payload = self._store.read()
        items = payload.get("items", [])
        return [item for item in items if isinstance(item, dict)]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        self._store.write({"version": 2, "items": items})

    def _assert_unique(self, items: list[dict[str, Any]], *, id: str, email: str, skip_id: str | None = None) -> None:
        normalized_email = email.strip().lower()
        for item in items:
            item_id = str(item.get("id") or "")
            if skip_id and item_id == skip_id:
                continue
            if item_id == id:
                raise ValueError("contact user id already exists")
            if str(item.get("email") or "").strip().lower() == normalized_email:
                raise ValueError("contact user email already exists")

    def list_items(self) -> list[dict[str, Any]]:
        return self._read_items()

    def get_by_id(self, item_id: str) -> dict[str, Any] | None:
        for item in self._read_items():
            if str(item.get("id") or "") == item_id:
                return item
        return None

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        normalized = email.strip().lower()
        for item in self._read_items():
            if str(item.get("email") or "").strip().lower() == normalized:
                return item
        return None

    def create(self, **item_data: Any) -> dict[str, Any]:
        items = self._read_items()
        item_id = str(item_data.get("id") or "").strip()
        full_name = str(item_data.get("full_name") or "").strip()
        email = str(item_data.get("email") or "").strip().lower()
        role = str(item_data.get("role") or "").strip()
        if not item_id or not full_name or not email or not role:
            raise ValueError("id, full_name, email and role are required")
        self._assert_unique(items, id=item_id, email=email)
        now = _now_iso()
        item = {"id": item_id, "full_name": full_name, "email": email, "role": role, "is_active": bool(item_data.get("is_active", True)), "created_at": item_data.get("created_at") or now, "updated_at": item_data.get("updated_at") or now}
        for key in ["cpf", "phone", "organization_id", "notes", "password_hash"]:
            if key in item_data:
                item[key] = item_data.get(key)
        items.append(item)
        self._write_items(items)
        return item

    def update(self, item_id: str, **fields: Any) -> dict[str, Any]:
        items = self._read_items()
        for idx, item in enumerate(items):
            if str(item.get("id") or "") != item_id:
                continue
            updated = {**item, **fields}
            updated_email = str(updated.get("email") or "").strip().lower()
            updated["email"] = updated_email
            self._assert_unique(items, id=str(updated.get("id") or ""), email=updated_email, skip_id=item_id)
            updated["updated_at"] = _now_iso()
            items[idx] = updated
            self._write_items(items)
            return updated
        raise ValueError("contact user not found")
