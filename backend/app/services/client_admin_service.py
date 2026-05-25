from __future__ import annotations

import re
from typing import Any

from app.config.runtime import get_supabase_db_url
from app.operations.sync_runtime_stores_from_supabase import _fetch_source_rows
from app.storage.client_repository import ClientRepository


class EntityNotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


class RuntimeDependencyError(Exception):
    pass


def _normalize_cnpj(value: str) -> str:
    digits = re.sub(r"\D+", "", value or "")
    if len(digits) != 14:
        raise ValidationError("cnpj must contain 14 digits")
    return digits


class ClientAdminService:
    def __init__(self, clients: ClientRepository) -> None:
        self._clients = clients

    def list_clients(self) -> list[dict[str, Any]]:
        supabase_clients = self._list_clients_from_supabase()
        if supabase_clients is not None:
            return sorted(supabase_clients, key=lambda item: str(item.get("brand_name") or item.get("name") or "").lower())
        items = [item for item in self._clients.list_clients() if bool(item.get("is_active", True))]
        return sorted(items, key=lambda item: str(item.get("brand_name") or item.get("name") or "").lower())

    def _list_clients_from_supabase(self) -> list[dict[str, Any]] | None:
        database_url = get_supabase_db_url()
        if not database_url:
            return None
        try:
            source_rows = _fetch_source_rows(database_url)
        except Exception as exc:  # pragma: no cover - runtime integration path
            raise RuntimeDependencyError("supabase_clients_unavailable") from exc

        organizations = source_rows.get("organizations", [])
        result: list[dict[str, Any]] = []
        for organization in organizations:
            organization_id = str(organization.get("id") or "").strip()
            if not organization_id:
                continue
            name = str(organization.get("name") or "").strip() or organization_id
            brand_name = str(organization.get("brand_name") or "").strip() or name
            slug = str(organization.get("slug") or "").strip() or f"cliente-{organization_id}"
            status = str(organization.get("status") or "active")
            is_active = bool(organization.get("is_active", True))
            created_at = str(organization.get("created_at") or "")
            updated_at = str(organization.get("updated_at") or "")

            result.append(
                {
                    "id": f"cli_{organization_id}",
                    "name": name,
                    "brand_name": brand_name,
                    "cnpj": "",
                    "slug": slug,
                    "status": status,
                    "is_active": is_active,
                    "timezone": "America/Sao_Paulo",
                    "currency": "BRL",
                    "notes": None,
                    "created_at": created_at,
                    "updated_at": updated_at,
                }
            )

        return [item for item in result if bool(item.get("is_active", True))]

    def create_client(
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
        normalized_cnpj = _normalize_cnpj(cnpj)
        normalized_currency = (currency or "BRL").strip().upper() or "BRL"
        normalized_timezone = (timezone_name or "America/Sao_Paulo").strip() or "America/Sao_Paulo"
        return self._clients.create(
            name=name.strip(),
            cnpj=normalized_cnpj,
            slug=slug,
            brand_name=brand_name.strip() if brand_name else None,
            timezone_name=normalized_timezone,
            currency=normalized_currency,
            notes=notes.strip() if notes else None,
        )

    def get_client_detail(self, client_id: str) -> dict[str, Any]:
        supabase_clients = self._list_clients_from_supabase()
        if supabase_clients is not None:
            for client in supabase_clients:
                if str(client.get("id")) == client_id:
                    return client
            raise EntityNotFoundError("client not found")
        client = self._clients.get_by_id(client_id)
        if not client or not bool(client.get("is_active", True)):
            raise EntityNotFoundError("client not found")
        return client
