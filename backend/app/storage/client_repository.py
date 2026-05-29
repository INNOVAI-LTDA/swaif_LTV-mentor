from __future__ import annotations


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



class ClientRepository:
    def __init__(self) -> None:
        self._database_url = get_supabase_db_url()
        self._use_postgres = bool(self._database_url)
        if self._use_postgres and psycopg is None:
            raise RuntimeError("SUPABASE_DB_URL is configured but psycopg is not installed.")

    def _list_from_postgres(self) -> list[dict[str, Any]]:
        assert self._database_url
        with psycopg.connect(self._database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, brand_name, cnpj, slug, status, is_active, timezone, currency, notes, created_at, updated_at
                    FROM deva_accmed_clients
                    WHERE deleted_at IS NULL
                    """
                )
                columns = [column[0] for column in (cur.description or ())]
                rows = [dict(zip(columns, row)) for row in cur.fetchall()]
        return rows

    def _read_items(self) -> list[dict[str, Any]]:
        if self._use_postgres:
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
                        INSERT INTO deva_accmed_clients (
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
                    client = dict(zip(columns, row))
                    return client
        raise RuntimeError("JSON client storage is disabled. Configure Supabase.")

    def get_by_id(self, client_id: str) -> dict[str, Any] | None:
        if self._use_postgres:
            assert self._database_url
            with psycopg.connect(self._database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, name, brand_name, cnpj, slug, status, is_active, timezone, currency, notes, created_at, updated_at
                        FROM deva_accmed_clients
                        WHERE id = %s AND deleted_at IS NULL
                        """,
                        (client_id,)
                    )
                    row = cur.fetchone()
                    if not row:
                        return None
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, row))
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
