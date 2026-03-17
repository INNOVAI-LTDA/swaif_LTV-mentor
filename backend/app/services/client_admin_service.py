from __future__ import annotations

import re
from typing import Any

from app.storage.client_repository import ClientRepository


class EntityNotFoundError(Exception):
    pass


class ValidationError(Exception):
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
        items = [item for item in self._clients.list_clients() if bool(item.get("is_active", True))]
        return sorted(items, key=lambda item: str(item.get("brand_name") or item.get("name") or "").lower())

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
        client = self._clients.get_by_id(client_id)
        if not client or not bool(client.get("is_active", True)):
            raise EntityNotFoundError("client not found")
        return client
