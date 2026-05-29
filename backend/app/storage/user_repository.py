from __future__ import annotations

import os
from pathlib import Path
from threading import RLock
from typing import Any

from app.config.runtime import get_supabase_db_url
from app.core.security import hash_password

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


def default_user_store_path() -> Path:
    configured = os.getenv("USER_STORE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "users.json"


class UserRepository:
    _memory_stores: dict[str, list[dict[str, Any]]] = {}
    _memory_lock = RLock()

    def __init__(self, file_path: str | Path | None = None) -> None:
        self._namespace = str((Path(file_path) if file_path is not None else default_user_store_path()).resolve())
        self._database_url = get_supabase_db_url()
        self._use_postgres = bool(self._database_url)
        if self._use_postgres and psycopg is None:
            raise RuntimeError("SUPABASE_DB_URL is configured but psycopg is not installed.")
        self._bootstrap_seed_users()

    def _memory_items(self) -> list[dict[str, Any]]:
        with self._memory_lock:
            items = self._memory_stores.get(self._namespace)
            if items is None:
                items = []
                self._memory_stores[self._namespace] = items
            return items

    def _has_password_hash_column(self) -> bool:
        if not self._use_postgres:
            return False
        assert self._database_url
        with psycopg.connect(self._database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'deva_accmed_users' AND column_name = 'password_hash'
                    LIMIT 1
                    """
                )
                return cur.fetchone() is not None

    def _bootstrap_seed_users(self) -> None:
        if self._use_postgres:
            return
        users = self._memory_items()
        if users:
            return
        users.extend(
            [
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
        )

    def create(self, *, email: str, password_hash: str, role: str, is_active: bool = True) -> dict[str, Any]:
        users = self.list_users()
        normalized_email = email.strip().lower()
        if any(str(u.get("email", "")).strip().lower() == normalized_email for u in users):
            raise ValueError("user email already exists")
        user = {
            "email": normalized_email,
            "password_hash": password_hash,
            "role": role,
            "is_active": is_active,
            "deleted_at": None,
        }
        if self._use_postgres:
            assert self._database_url
            has_password_hash = self._has_password_hash_column()
            with psycopg.connect(self._database_url) as conn:
                with conn.cursor() as cur:
                    if has_password_hash:
                        cur.execute(
                            """
                            INSERT INTO deva_accmed_users (email, role, is_active, password_hash)
                            VALUES (%s, %s, %s, %s)
                            RETURNING id
                            """,
                            (normalized_email, role, bool(is_active), password_hash),
                        )
                    else:
                        cur.execute(
                            """
                            INSERT INTO deva_accmed_users (email, role, is_active)
                            VALUES (%s, %s, %s)
                            RETURNING id
                            """,
                            (normalized_email, role, bool(is_active)),
                        )
                    new_id = cur.fetchone()[0]
                conn.commit()
            user["id"] = new_id
        else:
            # Simula autoincremento para memória
            items = self._memory_items()
            user["id"] = max([u["id"] for u in items if "id" in u and isinstance(u["id"], int)] + [0]) + 1
            items.append(user)
        return user

    def update(self, **kwargs) -> dict[str, Any]:
        """
        Update a user by id. Accepts any user fields as kwargs (must include 'id').
        """
        user_id = kwargs.get("id")
        if not user_id:
            raise ValueError("User id is required for update")
        users = self.list_users()
        updated = False
        for user in users:
            if int(user.get("id")) == int(user_id):
                user.update({k: v for k, v in kwargs.items() if k != "id"})
                updated = True
                break
        if not updated:
            raise ValueError(f"User with id {user_id} not found")
        if self._use_postgres:
            assert self._database_url
            fields = {k: v for k, v in kwargs.items() if k != "id"}
            if fields:
                set_fragments: list[str] = []
                params: list[Any] = []
                for field_name, field_value in fields.items():
                    set_fragments.append(f"{field_name} = %s")
                    params.append(field_value)
                params.append(str(user_id))
                query = f"UPDATE deva_accmed_users SET {', '.join(set_fragments)} WHERE id = %s"
                with psycopg.connect(self._database_url) as conn:
                    with conn.cursor() as cur:
                        cur.execute(query, tuple(params))
                    conn.commit()
        return user

    def list_users(self) -> list[dict[str, Any]]:
        if self._use_postgres:
            assert self._database_url
            has_password_hash = self._has_password_hash_column()
            if has_password_hash:
                query = """
                    SELECT id, email, role, is_active, COALESCE(password_hash, '') AS password_hash
                    FROM deva_accmed_users
                    WHERE deleted_at IS NULL
                """
            else:
                query = """
                    SELECT id, email, role, is_active, ''::text AS password_hash
                    FROM deva_accmed_users
                    WHERE deleted_at IS NULL
                """
            with psycopg.connect(self._database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    columns = [column[0] for column in (cur.description or ())]
                    return [dict(zip(columns, row)) for row in cur.fetchall()]

        return [dict(item) for item in self._memory_items() if isinstance(item, dict) and item.get("deleted_at") is None]

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        normalized = email.strip().lower()
        for user in self.list_users():
            if str(user.get("email", "")).strip().lower() == normalized:
                return user
        return None

    def get_by_id(self, user_id: int) -> dict[str, Any] | None:
        for user in self.list_users():
            if int(user.get("id")) == int(user_id):
                return user
        return None

    def soft_delete(self, user_id: int) -> bool:
        """Soft delete a user by setting deleted_at."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if self._use_postgres:
            assert self._database_url
            with psycopg.connect(self._database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE deva_accmed_users SET deleted_at = %s WHERE id = %s",
                        (now, user_id),
                    )
                conn.commit()
            return True
        else:
            users = self._memory_items()
            for user in users:
                if int(user.get("id")) == int(user_id):
                    user["deleted_at"] = now
                    return True
        return False
