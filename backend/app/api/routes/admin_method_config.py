from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.errors import api_error
from app.api.routes.admin_mentoria import require_admin_user
from app.schemas.metric import MetricCreate, MetricOut
from app.schemas.pillar import PillarCreate, PillarOut
from app.schemas.protocol import ProtocolCreate, ProtocolOut
from app.services.method_config_service import ConsistencyError, EntityNotFoundError, MethodConfigService
from app.storage.metric_repository import MetricRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository


router = APIRouter(prefix="/admin", tags=["admin-metodo"])


def get_method_config_service() -> MethodConfigService:
    return MethodConfigService(
        protocols=ProtocolRepository(),
        pillars=PillarRepository(),
        metrics=MetricRepository(),
    )


def _map_method_not_found(exc: EntityNotFoundError) -> tuple[str, str]:
    detail = str(exc)
    if detail == "pillar not found":
        return "PILAR_NOT_FOUND", "Pilar do metodo nao encontrado."
    return "METODO_NOT_FOUND", "Metodo nao encontrado."


@router.post("/protocolos", response_model=ProtocolOut, status_code=status.HTTP_201_CREATED)
def create_protocol(
    payload: ProtocolCreate,
    _: dict[str, Any] = Depends(require_admin_user),
    service: MethodConfigService = Depends(get_method_config_service),
) -> ProtocolOut:
    try:
        protocol = service.create_protocol(
            organization_id=payload.organization_id,
            name=payload.name,
            code=payload.code,
            metadata=payload.metadata,
        )
    except ValueError as exc:
        raise api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="METODO_CONFLICT",
            message="Ja existe metodo com este codigo.",
        ) from exc
    return ProtocolOut(**protocol)


@router.post("/pilares", response_model=PillarOut, status_code=status.HTTP_201_CREATED)
def create_pillar(
    payload: PillarCreate,
    _: dict[str, Any] = Depends(require_admin_user),
    service: MethodConfigService = Depends(get_method_config_service),
) -> PillarOut:
    try:
        pillar = service.create_pillar(
            protocol_id=payload.protocol_id,
            name=payload.name,
            code=payload.code,
            order_index=payload.order_index,
            metadata=payload.metadata,
        )
    except EntityNotFoundError as exc:
        error_code, message = _map_method_not_found(exc)
        raise api_error(status_code=status.HTTP_404_NOT_FOUND, code=error_code, message=message) from exc
    except ValueError as exc:
        raise api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="PILAR_CONFLICT",
            message="Ja existe pilar com este codigo no metodo.",
        ) from exc
    return PillarOut(**pillar)


@router.post("/metricas", response_model=MetricOut, status_code=status.HTTP_201_CREATED)
def create_metric(
    payload: MetricCreate,
    _: dict[str, Any] = Depends(require_admin_user),
    service: MethodConfigService = Depends(get_method_config_service),
) -> MetricOut:
    try:
        metric = service.create_metric(
            protocol_id=payload.protocol_id,
            pillar_id=payload.pillar_id,
            name=payload.name,
            code=payload.code,
            direction=payload.direction,
            unit=payload.unit,
            metadata=payload.metadata,
        )
    except EntityNotFoundError as exc:
        error_code, message = _map_method_not_found(exc)
        raise api_error(status_code=status.HTTP_404_NOT_FOUND, code=error_code, message=message) from exc
    except ConsistencyError as exc:
        raise api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="METRICA_PROTOCOL_MISMATCH",
            message="Pilar nao pertence ao metodo informado.",
        ) from exc
    except ValueError as exc:
        raise api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="METRICA_CONFLICT",
            message="Ja existe metrica com este codigo no metodo.",
        ) from exc
    return MetricOut(**metric)


@router.get("/protocolos/{protocol_id}/estrutura")
def get_protocol_structure(
    protocol_id: str,
    _: dict[str, Any] = Depends(require_admin_user),
    service: MethodConfigService = Depends(get_method_config_service),
) -> dict[str, Any]:
    try:
        return service.get_protocol_structure(protocol_id=protocol_id)
    except EntityNotFoundError as exc:
        error_code, message = _map_method_not_found(exc)
        raise api_error(status_code=status.HTTP_404_NOT_FOUND, code=error_code, message=message) from exc
