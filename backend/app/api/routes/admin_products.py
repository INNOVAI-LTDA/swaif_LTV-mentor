from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.errors import api_error
from app.api.routes.admin_mentoria import require_admin_user
from app.schemas.product import ProductCreate, ProductOut
from app.services.admin_product_service import AdminProductService, EntityNotFoundError, ValidationError
from app.storage.client_repository import ClientRepository
from app.storage.organization_repository import OrganizationRepository


router = APIRouter(prefix="/admin", tags=["admin-produtos"])


def get_admin_product_service() -> AdminProductService:
    return AdminProductService(ClientRepository(), OrganizationRepository())


@router.get("/clientes/{client_id}/produtos", response_model=list[ProductOut])
def list_products_by_client(
    client_id: str,
    _: dict[str, Any] = Depends(require_admin_user),
    service: AdminProductService = Depends(get_admin_product_service),
) -> list[ProductOut]:
    try:
        return [ProductOut(**item) for item in service.list_products_by_client(client_id)]
    except EntityNotFoundError as exc:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="CLIENTE_NOT_FOUND",
            message="Cliente nao encontrado.",
        ) from exc


@router.post("/clientes/{client_id}/produtos", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    client_id: str,
    payload: ProductCreate,
    _: dict[str, Any] = Depends(require_admin_user),
    service: AdminProductService = Depends(get_admin_product_service),
) -> ProductOut:
    try:
        product = service.create_product(
            client_id=client_id,
            name=payload.name,
            code=payload.code,
            slug=payload.slug,
            description=payload.description,
            delivery_model=payload.delivery_model,
        )
    except EntityNotFoundError as exc:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="CLIENTE_NOT_FOUND",
            message="Cliente nao encontrado.",
        ) from exc
    except ValidationError as exc:
        raise api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="PRODUTO_INVALIDO",
            message="Nome e codigo do produto sao obrigatorios.",
        ) from exc
    except ValueError as exc:
        detail = str(exc)
        if detail == "organization code already exists":
            raise api_error(
                status_code=status.HTTP_409_CONFLICT,
                code="PRODUTO_CONFLICT",
                message="Ja existe produto com este codigo para o cliente.",
            ) from exc
        raise api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="PRODUTO_CONFLICT",
            message="Ja existe produto com este slug para o cliente.",
        ) from exc
    return ProductOut(**product)


@router.get("/clientes/{client_id}/produtos/{product_id}", response_model=ProductOut)
def get_product_detail(
    client_id: str,
    product_id: str,
    _: dict[str, Any] = Depends(require_admin_user),
    service: AdminProductService = Depends(get_admin_product_service),
) -> ProductOut:
    try:
        return ProductOut(**service.get_product_detail(client_id, product_id))
    except EntityNotFoundError as exc:
        message = "Cliente nao encontrado." if str(exc) == "client not found" else "Produto nao encontrado."
        code = "CLIENTE_NOT_FOUND" if str(exc) == "client not found" else "PRODUTO_NOT_FOUND"
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code=code,
            message=message,
        ) from exc
