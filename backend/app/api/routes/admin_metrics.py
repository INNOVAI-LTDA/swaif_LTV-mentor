from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.errors import api_error
from app.api.routes.admin_mentoria import require_admin_user
from app.schemas.metric import AdminMetricCreate, AdminMetricOut
from app.services.admin_metric_service import AdminMetricService, EntityNotFoundError, ValidationError
from app.storage.metric_repository import MetricRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository


router = APIRouter(prefix="/admin", tags=["admin-metricas"])


def get_admin_metric_service() -> AdminMetricService:
    return AdminMetricService(
        protocols=ProtocolRepository(),
        pillars=PillarRepository(),
        metrics=MetricRepository(),
    )


@router.get("/pilares/{pillar_id}/metricas", response_model=list[AdminMetricOut])
def list_metrics_by_pillar(
    pillar_id: str,
    _: dict[str, Any] = Depends(require_admin_user),
    service: AdminMetricService = Depends(get_admin_metric_service),
) -> list[AdminMetricOut]:
    try:
        return [AdminMetricOut(**item) for item in service.list_metrics_by_pillar(pillar_id)]
    except EntityNotFoundError as exc:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PILAR_NOT_FOUND",
            message="Pilar nao encontrado.",
        ) from exc


@router.get("/produtos/{product_id}/metricas", response_model=list[AdminMetricOut])
def list_metrics_by_product(
    product_id: str,
    _: dict[str, Any] = Depends(require_admin_user),
    service: AdminMetricService = Depends(get_admin_metric_service),
) -> list[AdminMetricOut]:
    return [AdminMetricOut(**item) for item in service.list_metrics_by_product(product_id)]


@router.post("/pilares/{pillar_id}/metricas", response_model=AdminMetricOut, status_code=status.HTTP_201_CREATED)
def create_metric(
    pillar_id: str,
    payload: AdminMetricCreate,
    _: dict[str, Any] = Depends(require_admin_user),
    service: AdminMetricService = Depends(get_admin_metric_service),
) -> AdminMetricOut:
    try:
        metric = service.create_metric(
            pillar_id=pillar_id,
            name=payload.name,
            code=payload.code,
            direction=payload.direction,
            unit=payload.unit,
        )
    except EntityNotFoundError as exc:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PILAR_NOT_FOUND",
            message="Pilar nao encontrado.",
        ) from exc
    except ValidationError as exc:
        detail = str(exc)
        message = "Nome da metrica e obrigatorio." if detail == "name is required" else "Direcao da metrica e invalida."
        raise api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="METRICA_INVALIDA",
            message=message,
        ) from exc
    except ValueError as exc:
        raise api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="METRICA_CONFLICT",
            message="Ja existe metrica com este codigo para o pilar.",
        ) from exc
    return AdminMetricOut(**metric)
