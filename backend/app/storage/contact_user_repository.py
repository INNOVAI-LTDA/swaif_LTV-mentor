from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from app.config.runtime import get_supabase_db_url

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


def default_contact_user_store_path() -> Path:
    configured = os.getenv("CONTACT_USER_STORE_PATH")
    if configured:
        return Path(configured)
    user_store = os.getenv("USER_STORE_PATH")
    if user_store:
        return Path(user_store).with_name("contacts_users_v2.json")
    return Path(__file__).resolve().parents[2] / "data" / "contacts_users_v2.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ContactUserRepository:
    _memory_stores: dict[str, list[dict[str, Any]]] = {}
    _memory_lock = RLock()

    def __init__(self, file_path: str | Path | None = None) -> None:
        self._namespace = str((Path(file_path) if file_path is not None else default_contact_user_store_path()).resolve())
        self._database_url = get_supabase_db_url()
        self._use_postgres = bool(self._database_url)
        if self._use_postgres and psycopg is None:
            raise RuntimeError("SUPABASE_DB_URL is configured but psycopg is not installed.")
        if not self._use_postgres:
            self._memory_items()

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

    def _read_items(self) -> list[dict[str, Any]]:
        if self._use_postgres:
            assert self._database_url
            has_password_hash = self._has_password_hash_column()
            if has_password_hash:
                query = """
                    SELECT id, full_name, email, role, is_active, organization_id, created_at, updated_at, COALESCE(password_hash, '') AS password_hash
                    FROM deva_accmed_users
                """
            else:
                query = """
                    SELECT id, full_name, email, role, is_active, organization_id, created_at, updated_at, ''::text AS password_hash
                    FROM deva_accmed_users
                """
            with psycopg.connect(self._database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    columns = [column[0] for column in (cur.description or ())]
                    return [dict(zip(columns, row)) for row in cur.fetchall()]

        return [dict(item) for item in self._memory_items() if isinstance(item, dict)]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        if self._use_postgres:
            raise RuntimeError("Direct contact store writes are not supported in Supabase runtime store mode.")
        with self._memory_lock:
            self._memory_stores[self._namespace] = [dict(item) for item in items]

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
        if self._use_postgres:
            assert self._database_url
            has_password_hash = self._has_password_hash_column()
            with psycopg.connect(self._database_url) as conn:
                with conn.cursor() as cur:
                    if has_password_hash:
                        cur.execute(
                            """
                            INSERT INTO deva_accmed_users (id, full_name, email, role, is_active, organization_id, password_hash)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                item_id,
                                full_name,
                                email,
                                role,
                                bool(item.get("is_active", True)),
                                item.get("organization_id"),
                                item.get("password_hash"),
                            ),
                        )
                    else:
                        cur.execute(
                            """
                            INSERT INTO deva_accmed_users (id, full_name, email, role, is_active, organization_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            (
                                item_id,
                                full_name,
                                email,
                                role,
                                bool(item.get("is_active", True)),
                                item.get("organization_id"),
                            ),
                        )
                conn.commit()
        else:
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
            if self._use_postgres:
                assert self._database_url
                mutable_fields = {
                    key: value
                    for key, value in updated.items()
                    if key in {"full_name", "email", "role", "is_active", "organization_id", "password_hash"}
                }
                if mutable_fields:
                    set_fragments: list[str] = []
                    params: list[Any] = []
                    for field_name, field_value in mutable_fields.items():
                        if field_name == "password_hash" and not self._has_password_hash_column():
                            continue
                        set_fragments.append(f"{field_name} = %s")
                        params.append(field_value)
                    if set_fragments:
                        params.append(item_id)
                        query = f"UPDATE deva_accmed_users SET {', '.join(set_fragments)} WHERE id = %s"
                        with psycopg.connect(self._database_url) as conn:
                            with conn.cursor() as cur:
                                cur.execute(query, tuple(params))
                            conn.commit()
            else:
                items[idx] = updated
                self._write_items(items)
            return updated
        raise ValueError("contact user not found")
