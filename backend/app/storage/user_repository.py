from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.core.security import hash_password
from app.storage.json_repository import JsonRepository


def default_user_store_path() -> Path:
    configured = os.getenv("USER_STORE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "users.json"


class UserRepository:
    def __init__(self, file_path: str | Path | None = None) -> None:
        self._store = JsonRepository(file_path or default_user_store_path())
        self._bootstrap_seed_users()

    def _bootstrap_seed_users(self) -> None:
        payload = self._store.read()
        items = payload.get("items", [])
        if items:
            return

        seed = [
            {
                "id": "usr_admin",
                "email": "admin@swaif.local",
                "password_hash": hash_password("admin123"),
                "role": "admin",
                "is_active": True,
            },
            {
                "id": "usr_mentor",
                "email": "mentor@swaif.local",
                "password_hash": hash_password("mentor123"),
                "role": "mentor",
                "is_active": True,
            },
        ]
        self._store.write({"version": 1, "items": seed})

    def list_users(self) -> list[dict[str, Any]]:
        payload = self._store.read()
        items = payload.get("items", [])
        return [item for item in items if isinstance(item, dict)]

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        normalized = email.strip().lower()
        for user in self.list_users():
            if str(user.get("email", "")).strip().lower() == normalized:
                return user
        return None

    def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        for user in self.list_users():
            if str(user.get("id")) == user_id:
                return user
        return None
