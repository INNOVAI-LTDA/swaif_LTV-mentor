from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.errors import api_error
from app.api.routes.admin_mentoria import require_admin_user
from app.schemas.pillar import AdminPillarCreate, AdminPillarOut
from app.services.admin_pillar_service import AdminPillarService, EntityNotFoundError, ValidationError
from app.storage.organization_repository import OrganizationRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository


router = APIRouter(prefix="/admin", tags=["admin-pilares"])


def get_admin_pillar_service() -> AdminPillarService:
    return AdminPillarService(
        organizations=OrganizationRepository(),
        protocols=ProtocolRepository(),
        pillars=PillarRepository(),
    )


@router.get("/produtos/{product_id}/pilares", response_model=list[AdminPillarOut])
def list_pillars_by_product(
    product_id: str,
    _: dict[str, Any] = Depends(require_admin_user),
    service: AdminPillarService = Depends(get_admin_pillar_service),
) -> list[AdminPillarOut]:
    try:
        return [AdminPillarOut(**item) for item in service.list_pillars_by_product(product_id)]
    except EntityNotFoundError as exc:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUTO_NOT_FOUND",
            message="Produto nao encontrado.",
        ) from exc


@router.post("/produtos/{product_id}/pilares", response_model=AdminPillarOut, status_code=status.HTTP_201_CREATED)
def create_pillar(
    product_id: str,
    payload: AdminPillarCreate,
    _: dict[str, Any] = Depends(require_admin_user),
    service: AdminPillarService = Depends(get_admin_pillar_service),
) -> AdminPillarOut:
    try:
        pillar = service.create_pillar(
            product_id=product_id,
            name=payload.name,
            code=payload.code,
            order_index=payload.order_index,
        )
    except EntityNotFoundError as exc:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUTO_NOT_FOUND",
            message="Produto nao encontrado.",
        ) from exc
    except ValidationError as exc:
        raise api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="PILAR_INVALIDO",
            message="Nome do pilar e obrigatorio.",
        ) from exc
    except ValueError as exc:
        raise api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="PILAR_CONFLICT",
            message="Ja existe pilar com este codigo no produto.",
        ) from exc
    return AdminPillarOut(**pillar)
