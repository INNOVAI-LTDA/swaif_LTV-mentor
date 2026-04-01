from __future__ import annotations

from typing import Any

from app.storage.metric_repository import MetricRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository


class EntityNotFoundError(Exception):
    pass


class ConsistencyError(Exception):
    pass


class MethodConfigService:
    def __init__(self, protocols: ProtocolRepository, pillars: PillarRepository, metrics: MetricRepository) -> None:
        self._protocols = protocols
        self._pillars = pillars
        self._metrics = metrics

    def create_protocol(
        self,
        *,
        organization_id: str,
        name: str,
        code: str | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        return self._protocols.create(
            organization_id=organization_id,
            name=name,
            code=code,
            metadata=metadata,
        )

    def create_pillar(
        self,
        *,
        protocol_id: str,
        name: str,
        code: str | None = None,
        order_index: int = 0,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        protocol = self._protocols.get_by_id(protocol_id)
        if not protocol:
            raise EntityNotFoundError("protocol not found")

        return self._pillars.create(
            protocol_id=protocol_id,
            name=name,
            code=code,
            order_index=order_index,
            metadata=metadata,
        )

    def create_metric(
        self,
        *,
        protocol_id: str,
        pillar_id: str,
        name: str,
        code: str | None = None,
        direction: str = "higher_better",
        unit: str | None = None,
        scoring_rules: list[dict] | None = None,
        score_type: str | None = None,
        min_score: int | None = None,
        max_score: int | None = None,
        mcv_score: int | None = None,
        max_basis_score: str | None = None,
    ) -> dict[str, Any]:
        protocol = self._protocols.get_by_id(protocol_id)
        if not protocol:
            raise EntityNotFoundError("protocol not found")

        pillar = self._pillars.get_by_id(pillar_id)
        if not pillar:
            raise EntityNotFoundError("pillar not found")

        if str(pillar.get("protocol_id")) != protocol_id:
            raise ConsistencyError("pillar does not belong to protocol")

        return self._metrics.create(
            protocol_id=protocol_id,
            pillar_id=pillar_id,
            name=name,
            code=code,
            direction=direction,
            unit=unit,
            scoring_rules=scoring_rules,
            score_type=score_type or "static",
            min_score=min_score if min_score is not None else 0,
            max_score=max_score if max_score is not None else 1,
            mcv_score=mcv_score if mcv_score is not None else 1,
            max_basis_score=max_basis_score or "1",
        )

    def get_protocol_structure(self, *, protocol_id: str) -> dict[str, Any]:
        protocol = self._protocols.get_by_id(protocol_id)
        if not protocol:
            raise EntityNotFoundError("protocol not found")

        pillars = [
            pillar
            for pillar in self._pillars.list_pillars()
            if str(pillar.get("protocol_id")) == protocol_id and bool(pillar.get("is_active", True))
        ]
        pillars.sort(key=lambda item: int(item.get("order_index", 0)))

        metrics = [
            metric
            for metric in self._metrics.list_metrics()
            if str(metric.get("protocol_id")) == protocol_id and bool(metric.get("is_active", True))
        ]

        metrics_by_pillar: dict[str, list[dict[str, Any]]] = {}
        for metric in metrics:
            pillar_id = str(metric.get("pillar_id"))
            metrics_by_pillar.setdefault(pillar_id, []).append(metric)

        structured_pillars: list[dict[str, Any]] = []
        for pillar in pillars:
            pillar_id = str(pillar.get("id"))
            structured_pillars.append({**pillar, "metrics": metrics_by_pillar.get(pillar_id, [])})

        return {"protocol": protocol, "pillars": structured_pillars}
