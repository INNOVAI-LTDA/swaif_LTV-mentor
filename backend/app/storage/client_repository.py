from __future__ import annotations

import json
import os
from pathlib import Path

from datetime import datetime, timezone
from typing import Any
from app.config.runtime import get_supabase_db_url

try:
    import psycopg
except ImportError:
    psycopg = None





def _slugify(value: str) -> str:
    compact = "-".join(value.strip().lower().split())
    return compact or "cliente"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_client_id(value: str | int | None) -> str:
    raw = str(value or "").strip()
    if raw.startswith("cli_"):
        return raw[4:]
    return raw



class ClientRepository:
    def __init__(self) -> None:
        self._database_url = get_supabase_db_url()
        self._use_postgres = bool(self._database_url)
        configured_store = os.getenv("CLIENT_STORE_PATH")
        if configured_store:
            self._client_store_path = Path(configured_store)
        else:
            self._client_store_path = Path(__file__).resolve().parents[2] / "data" / "clients.json"
        if self._use_postgres and psycopg is None:
            raise RuntimeError("SUPABASE_DB_URL is configured but psycopg is not installed.")

    def _list_from_snapshot(self) -> list[dict[str, Any]]:
        if not self._client_store_path.exists():
            return []
        try:
            payload = json.loads(self._client_store_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        items = payload.get("items", []) if isinstance(payload, dict) else []
        return [dict(item) for item in items if isinstance(item, dict)]

    def _list_from_postgres(self) -> list[dict[str, Any]]:
        assert self._database_url
        with psycopg.connect(self._database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, brand_name, cnpj, slug, status, is_active, timezone, currency, notes, created_at, updated_at
                    FROM deva_accmed_organizations
                    """
                )
                columns = [column[0] for column in (cur.description or ())]
                rows = [dict(zip(columns, row)) for row in cur.fetchall()]

        mapped: list[dict[str, Any]] = []
        for row in rows:
            raw_id = str(row.get("id") or "").strip()
            if not raw_id:
                continue
            mapped.append(
                {
                    "id": f"cli_{raw_id}",
                    "name": str(row.get("name") or "").strip() or f"Cliente {raw_id}",
                    "brand_name": str(row.get("brand_name") or row.get("name") or "").strip() or f"Cliente {raw_id}",
                    "cnpj": str(row.get("cnpj") or ""),
                    "slug": str(row.get("slug") or "").strip() or f"cliente-{raw_id}",
                    "status": str(row.get("status") or "active"),
                    "is_active": bool(row.get("is_active", True)),
                    "timezone": str(row.get("timezone") or "America/Sao_Paulo"),
                    "currency": str(row.get("currency") or "BRL"),
                    "notes": row.get("notes"),
                    "created_at": str(row.get("created_at") or _now_iso()),
                    "updated_at": str(row.get("updated_at") or _now_iso()),
                }
            )

        return mapped

    def _read_items(self) -> list[dict[str, Any]]:
        if self._use_postgres:
            snapshot = self._list_from_snapshot()
            if snapshot:
                return snapshot
            return self._list_from_postgres()
        raise RuntimeError("JSON client storage is disabled. Configure Supabase.")

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
        now = _now_iso()
        candidate_slug = _slugify(slug or name)
        if self._use_postgres:
            assert self._database_url
            with psycopg.connect(self._database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO deva_accmed_organizations (
                            name, cnpj, slug, brand_name, timezone, currency, notes, status, is_active, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, name, brand_name, cnpj, slug, status, is_active, timezone, currency, notes, created_at, updated_at
                        """,
                        (
                            name,
                            cnpj,
                            candidate_slug,
                            brand_name or name,
                            timezone_name,
                            currency,
                            notes,
                            "active",
                            True,
                            now,
                            now,
                        ),
                    )
                    row = cur.fetchone()
                    columns = [desc[0] for desc in cur.description]
                    record = dict(zip(columns, row))
                    raw_id = str(record.get("id") or "").strip()
                    return {
                        "id": f"cli_{raw_id}" if raw_id else "",
                        "name": str(record.get("name") or "").strip(),
                        "brand_name": str(record.get("brand_name") or record.get("name") or "").strip(),
                        "cnpj": str(record.get("cnpj") or ""),
                        "slug": str(record.get("slug") or "").strip(),
                        "status": str(record.get("status") or "active"),
                        "is_active": bool(record.get("is_active", True)),
                        "timezone": str(record.get("timezone") or "America/Sao_Paulo"),
                        "currency": str(record.get("currency") or "BRL"),
                        "notes": record.get("notes"),
                        "created_at": str(record.get("created_at") or now),
                        "updated_at": str(record.get("updated_at") or now),
                    }
        raise RuntimeError("JSON client storage is disabled. Configure Supabase.")

    def get_by_id(self, client_id: str) -> dict[str, Any] | None:
        if self._use_postgres:
            normalized = _normalize_client_id(client_id)
            for client in self._read_items():
                if _normalize_client_id(client.get("id")) == normalized:
                    return client
            return None
        raise RuntimeError("JSON client storage is disabled. Configure Supabase.")
