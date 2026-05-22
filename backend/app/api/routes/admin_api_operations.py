from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.api.errors import api_error
from app.api.routes.admin_mentoria import require_admin_user
from app.services.admin_api_operations_service import AdminApiOperationsService

router = APIRouter(prefix="/admin/api-operations", tags=["admin-api-operations"])


class ExecuteOperationRequest(BaseModel):
    endpoint: str


def get_service() -> AdminApiOperationsService:
    return AdminApiOperationsService()


@router.get("/catalog")
def list_catalog(_: dict[str, Any] = Depends(require_admin_user), service: AdminApiOperationsService = Depends(get_service)) -> dict[str, Any]:
    return {"items": service.list_operations()}


@router.post("/execute")
def execute_operation(
    payload: ExecuteOperationRequest,
    admin: dict[str, Any] = Depends(require_admin_user),
    service: AdminApiOperationsService = Depends(get_service),
) -> dict[str, str]:
    endpoint = payload.endpoint.strip()
    if not endpoint:
        raise api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="ADMIN_OPERATION_INVALID",
            message="endpoint e obrigatorio.",
        )
    try:
        return service.execute_operation(
            admin_user_id=str(admin.get("id") or ""),
            admin_email=str(admin.get("email") or ""),
            operation_endpoint=endpoint,
        )
    except ValueError as exc:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ADMIN_OPERATION_NOT_FOUND",
            message="Operacao administrativa nao encontrada.",
        ) from exc
