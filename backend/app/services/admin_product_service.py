from __future__ import annotations

from typing import Any

from app.storage.client_repository import ClientRepository
from app.storage.organization_repository import OrganizationRepository


class EntityNotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


class AdminProductService:
    def __init__(self, clients: ClientRepository, organizations: OrganizationRepository) -> None:
        self._clients = clients
        self._organizations = organizations

    def _get_active_client(self, client_id: str) -> dict[str, Any]:
        client = self._clients.get_by_id(client_id)
        if not client or not bool(client.get("is_active", True)):
            raise EntityNotFoundError("client not found")
        return client

    def list_products_by_client(self, client_id: str) -> list[dict[str, Any]]:
        self._get_active_client(client_id)
        items = [
            item
            for item in self._organizations.list_by_client(client_id)
            if bool(item.get("is_active", True))
        ]
        return sorted(items, key=lambda item: (str(item.get("name") or "").lower(), str(item.get("code") or "").lower()))

    def create_product(
        self,
        *,
        client_id: str,
        name: str,
        code: str,
        slug: str | None = None,
        description: str | None = None,
        delivery_model: str | None = None,
    ) -> dict[str, Any]:
        self._get_active_client(client_id)
        normalized_name = name.strip()
        normalized_code = code.strip()
        if not normalized_name or not normalized_code:
            raise ValidationError("name and code are required")

        return self._organizations.create(
            name=normalized_name,
            slug=slug.strip() if slug else None,
            client_id=client_id,
            code=normalized_code,
            description=description.strip() if description else None,
            delivery_model=(delivery_model or "live").strip() or "live",
        )

    def get_product_detail(self, client_id: str, product_id: str) -> dict[str, Any]:
        self._get_active_client(client_id)
        product = self._organizations.get_by_id(product_id)
        if not product or not bool(product.get("is_active", True)):
            raise EntityNotFoundError("product not found")
        if str(product.get("client_id") or "") != client_id:
            raise EntityNotFoundError("product not found")
        return product
