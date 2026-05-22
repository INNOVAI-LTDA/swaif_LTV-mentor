from __future__ import annotations

from typing import Any

from app.storage.organization_repository import OrganizationRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository


class EntityNotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


class AdminPillarService:
    def __init__(
        self,
        organizations: OrganizationRepository,
        protocols: ProtocolRepository,
        pillars: PillarRepository,
    ) -> None:
        self._organizations = organizations
        self._protocols = protocols
        self._pillars = pillars

    def _get_active_product(self, product_id: str) -> dict[str, Any]:
        product = self._organizations.get_by_id(product_id)
        if not product or not bool(product.get("is_active", True)):
            raise EntityNotFoundError("product not found")
        return product

    def _get_active_protocol(self, product_id: str) -> dict[str, Any] | None:
        for protocol in self._protocols.list_by_organization(product_id):
            if bool(protocol.get("is_active", True)):
                return protocol
        return None

    def _get_or_create_protocol(self, product: dict[str, Any]) -> dict[str, Any]:
        current = self._get_active_protocol(str(product.get("id")))
        if current:
            return current

        product_id = str(product.get("id"))
        product_name = str(product.get("name") or "Produto")
        return self._protocols.create(
            organization_id=product_id,
            name=f"Metodo {product_name}",
            code=f"{product_id}-metodo",
        )

    def list_pillars_by_product(self, product_id: str) -> list[dict[str, Any]]:
        self._get_active_product(product_id)
        protocol = self._get_active_protocol(product_id)
        if not protocol:
            return []

        items = [
            item
            for item in self._pillars.list_pillars()
            if str(item.get("protocol_id") or "") == str(protocol.get("id"))
            and bool(item.get("is_active", True))
        ]
        return sorted(
            items,
            key=lambda item: (
                int(item.get("order_index", 0)),
                str(item.get("name") or "").lower(),
            ),
        )

    def create_pillar(
        self,
        *,
        product_id: str,
        name: str,
        code: str | None = None,
        order_index: int = 0,
    ) -> dict[str, Any]:
        product = self._get_active_product(product_id)
        normalized_name = name.strip()
        if not normalized_name:
            raise ValidationError("name is required")

        protocol = self._get_or_create_protocol(product)
        return self._pillars.create(
            protocol_id=str(protocol.get("id")),
            name=normalized_name,
            code=code.strip() if code else None,
            order_index=order_index,
        )
