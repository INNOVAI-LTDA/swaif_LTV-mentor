from __future__ import annotations

from typing import Any

from app.storage.metric_repository import MetricRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository


VALID_DIRECTIONS = {"higher_better", "lower_better", "target_range"}


class EntityNotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


class AdminMetricService:
    def __init__(
        self,
        protocols: ProtocolRepository,
        pillars: PillarRepository,
        metrics: MetricRepository,
    ) -> None:
        self._protocols = protocols
        self._pillars = pillars
        self._metrics = metrics

    def _get_active_pillar(self, pillar_id: str) -> dict[str, Any]:
        pillar = self._pillars.get_by_id(pillar_id)
        if not pillar or not bool(pillar.get("is_active", True)):
            raise EntityNotFoundError("pillar not found")
        return pillar

    def _get_active_protocol(self, protocol_id: str) -> dict[str, Any]:
        protocol = self._protocols.get_by_id(protocol_id)
        if not protocol or not bool(protocol.get("is_active", True)):
            raise EntityNotFoundError("protocol not found")
        return protocol

    def list_metrics_by_pillar(self, pillar_id: str) -> list[dict[str, Any]]:
        pillar = self._get_active_pillar(pillar_id)
        self._get_active_protocol(str(pillar.get("protocol_id")))
        items = [
            item
            for item in self._metrics.list_by_pillar(pillar_id)
            if bool(item.get("is_active", True))
        ]
        return sorted(items, key=lambda item: (str(item.get("name") or "").lower(), str(item.get("code") or "").lower()))

    def list_metrics_by_product(self, product_id: str) -> list[dict[str, Any]]:
        protocol_ids = {
            str(protocol.get("id"))
            for protocol in self._protocols.list_by_organization(product_id)
            if bool(protocol.get("is_active", True))
        }
        if not protocol_ids:
            return []

        active_pillars = {
            str(pillar.get("id")): pillar
            for pillar in self._pillars.list_pillars()
            if str(pillar.get("protocol_id") or "") in protocol_ids and bool(pillar.get("is_active", True))
        }
        if not active_pillars:
            return []

        items = [
            {**item, "pillar_name": str(active_pillars[str(item.get("pillar_id"))].get("name") or "")}
            for item in self._metrics.list_metrics()
            if str(item.get("pillar_id") or "") in active_pillars and bool(item.get("is_active", True))
        ]
        return sorted(
            items,
            key=lambda item: (
                str(item.get("pillar_name") or "").lower(),
                str(item.get("name") or "").lower(),
                str(item.get("code") or "").lower(),
            ),
        )

    def create_metric(
        self,
        *,
        pillar_id: str,
        name: str,
        code: str | None = None,
        direction: str = "higher_better",
        unit: str | None = None,
    ) -> dict[str, Any]:
        pillar = self._get_active_pillar(pillar_id)
        protocol_id = str(pillar.get("protocol_id"))
        self._get_active_protocol(protocol_id)

        normalized_name = name.strip()
        normalized_direction = direction.strip()
        normalized_unit = unit.strip() if unit else None
        if not normalized_name:
            raise ValidationError("name is required")
        if normalized_direction not in VALID_DIRECTIONS:
            raise ValidationError("direction is invalid")

        return self._metrics.create(
            protocol_id=protocol_id,
            pillar_id=pillar_id,
            name=normalized_name,
            code=code.strip() if code else None,
            direction=normalized_direction,
            unit=normalized_unit,
        )
