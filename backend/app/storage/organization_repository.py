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
    _memory_stores: dict[str, list[dict[str, Any]]] = {}
    _memory_lock = RLock()
    _mentor_overrides: dict[str, str] = {}
    _mentor_overrides_lock = RLock()

    def __init__(self, file_path: str | Path | None = None) -> None:
        self._namespace = str((Path(file_path) if file_path is not None else default_organization_store_path()).resolve())
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

    def _list_from_postgres(self) -> list[dict[str, Any]]:
        assert self._database_url
        with psycopg.connect(self._database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        p.id,
                        p.organization_id,
                        p.name,
                        p.slug,
                        p.status,
                        p.created_at,
                        p.updated_at,
                        o.name AS organization_name,
                        o.brand_name
                    FROM deva_accmed_products p
                    LEFT JOIN deva_accmed_organizations o ON o.id = p.organization_id
                    """
                )
                columns = [column[0] for column in (cur.description or ())]
                rows = [dict(zip(columns, row)) for row in cur.fetchall()]

        with self._mentor_overrides_lock:
            mentor_overrides = dict(self._mentor_overrides)

        mapped: list[dict[str, Any]] = []
        for row in rows:
            product_id = str(row.get("id") or "")
            organization_id = str(row.get("organization_id") or "")
            if not product_id:
                continue
            slug = _slugify(str(row.get("slug") or row.get("name") or f"produto-{product_id}"))
            mapped.append(
                {
                    "id": f"org_{product_id}",
                    "name": str(row.get("name") or row.get("organization_name") or f"Produto {product_id}"),
                    "slug": slug,
                    "code": _normalize_code(slug),
                    "client_id": f"cli_{organization_id}" if organization_id else None,
                    "mentor_id": mentor_overrides.get(f"org_{product_id}"),
                    "description": None,
                    "delivery_model": "live",
                    "status": str(row.get("status") or "active"),
                    "is_active": str(row.get("status") or "active").lower() == "active",
                    "created_at": str(row.get("created_at") or _now_iso()),
                    "updated_at": str(row.get("updated_at") or _now_iso()),
                }
            )
        return mapped

    def update(self, **kwargs) -> dict[str, Any]:
        organization_id = kwargs.get("id")
        if not organization_id:
            raise ValueError("Organization id is required for update")
        if self._use_postgres:
            raise RuntimeError("Organization update is not supported in Supabase runtime store mode.")
        items = self._read_items()
        for idx, organization in enumerate(items):
            if str(organization.get("id")) == organization_id:
                updated = {**organization, **kwargs, "updated_at": _now_iso()}
                items[idx] = updated
                self._write_items(items)
                return updated
        raise ValueError(f"Organization with id {organization_id} not found")

    def delete(self, organization_id: str) -> bool:
        if self._use_postgres:
            raise RuntimeError("Organization delete is not supported in Supabase runtime store mode.")
        items = self._read_items()
        new_items = [organization for organization in items if str(organization.get("id")) != organization_id]
        if len(new_items) == len(items):
            return False
        self._write_items(new_items)
        return True

    def _read_items(self) -> list[dict[str, Any]]:
        if self._use_postgres:
            return self._list_from_postgres()
        return [dict(item) for item in self._memory_items() if isinstance(item, dict)]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        if self._use_postgres:
            raise RuntimeError("Organization write is not supported in Supabase runtime store mode.")
        with self._memory_lock:
            self._memory_stores[self._namespace] = [dict(item) for item in items]

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
        if self._use_postgres:
            raise RuntimeError("Organization create is not supported in Supabase runtime store mode.")
        items = self._read_items()
        candidate_slug = _slugify(slug or name)
        candidate_code = _normalize_code(code or candidate_slug or name)

        def _same_scope(item: dict[str, Any]) -> bool:
            return str(item.get("client_id") or "") == str(client_id or "")

        if any(_same_scope(item) and str(item.get("slug")) == candidate_slug for item in items):
            raise ValueError("organization slug already exists")
        if any(_same_scope(item) and str(item.get("code")) == candidate_code for item in items):
            raise ValueError("organization code already exists")
        if any(_same_scope(item) and str(item.get("name")) == name for item in items):
            raise ValueError("organization name already exists")

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
        if self._use_postgres:
            with self._mentor_overrides_lock:
                self._mentor_overrides[organization_id] = mentor_id
            return self.get_by_id(organization_id)

        items = self._read_items()
        for idx, organization in enumerate(items):
            if str(organization.get("id")) == organization_id:
                organization["mentor_id"] = mentor_id
                organization["updated_at"] = _now_iso()
                items[idx] = organization
                self._write_items(items)
                return organization
        return None
