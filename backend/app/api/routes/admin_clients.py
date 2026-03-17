from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.errors import api_error
from app.api.routes.admin_mentoria import require_admin_user
from app.schemas.client import ClientCreate, ClientOut
from app.services.client_admin_service import ClientAdminService, EntityNotFoundError, ValidationError
from app.storage.client_repository import ClientRepository


router = APIRouter(prefix="/admin", tags=["admin-clientes"])


def get_client_admin_service() -> ClientAdminService:
    return ClientAdminService(ClientRepository())


@router.get("/clientes", response_model=list[ClientOut])
def list_clients(
    _: dict[str, Any] = Depends(require_admin_user),
    service: ClientAdminService = Depends(get_client_admin_service),
) -> list[ClientOut]:
    return [ClientOut(**item) for item in service.list_clients()]


@router.post("/clientes", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientCreate,
    _: dict[str, Any] = Depends(require_admin_user),
    service: ClientAdminService = Depends(get_client_admin_service),
) -> ClientOut:
    try:
        client = service.create_client(
            name=payload.name,
            cnpj=payload.cnpj,
            slug=payload.slug,
            brand_name=payload.brand_name,
            timezone_name=payload.timezone or "America/Sao_Paulo",
            currency=payload.currency or "BRL",
            notes=payload.notes,
        )
    except ValidationError as exc:
        raise api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="CLIENTE_CNPJ_INVALIDO",
            message="CNPJ deve conter 14 digitos.",
        ) from exc
    except ValueError as exc:
        detail = str(exc)
        if detail == "client cnpj already exists":
            raise api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="CLIENTE_CONFLICT",
                message="Ja existe cliente com este CNPJ.",
            ) from exc
        raise api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="CLIENTE_CONFLICT",
            message="Ja existe cliente com este slug.",
        ) from exc
    return ClientOut(**client)


@router.get("/clientes/{client_id}", response_model=ClientOut)
def get_client_detail(
    client_id: str,
    _: dict[str, Any] = Depends(require_admin_user),
    service: ClientAdminService = Depends(get_client_admin_service),
) -> ClientOut:
    try:
        return ClientOut(**service.get_client_detail(client_id))
    except EntityNotFoundError as exc:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="CLIENTE_NOT_FOUND",
            message="Cliente nao encontrado.",
        ) from exc
