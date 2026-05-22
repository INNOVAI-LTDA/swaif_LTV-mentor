from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.api.errors import api_error
from app.api.routes.admin_mentoria import require_admin_user
from app.services.admin_database_view_service import AdminDatabaseViewService
from app.storage.admin_database_view_repository import AdminDatabaseViewRepository

router = APIRouter(prefix="/admin/database-view", tags=["admin-database-view"])


class UpdateRecordPayload(BaseModel):
    changes: dict[str, Any] = Field(default_factory=dict)


def get_service() -> AdminDatabaseViewService:
    return AdminDatabaseViewService(AdminDatabaseViewRepository())


@router.get("/tables")
def list_tables(_: dict[str, Any] = Depends(require_admin_user), service: AdminDatabaseViewService = Depends(get_service)) -> dict[str, Any]:
    return {"tables": service.list_tables()}


@router.get("/tables/{table}/records")
def list_records(
    table: str,
    limit: int = Query(default=10, ge=1, le=10),
    offset: int = Query(default=0, ge=0),
    _: dict[str, Any] = Depends(require_admin_user),
    service: AdminDatabaseViewService = Depends(get_service),
) -> dict[str, Any]:
    try:
        result = service.list_records(table=table, limit=limit, offset=offset)
    except KeyError as exc:
        raise api_error(status_code=status.HTTP_404_NOT_FOUND, code="DATABASE_TABLE_NOT_FOUND", message="Tabela nao permitida.") from exc
    return result.__dict__


@router.patch("/tables/{table}/records/{record_id}")
def update_record(
    table: str,
    record_id: str,
    payload: UpdateRecordPayload,
    admin: dict[str, Any] = Depends(require_admin_user),
    service: AdminDatabaseViewService = Depends(get_service),
) -> dict[str, Any]:
    if not payload.changes:
        raise api_error(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code="DATABASE_EMPTY_CHANGES", message="Alteracoes obrigatorias.")
    try:
        item = service.update_record(admin_id=str(admin.get("id") or admin.get("email") or "admin"), table=table, record_id=record_id, changes=payload.changes)
    except KeyError as exc:
        message = "Tabela nao permitida." if str(exc) == "'table_not_allowed'" else "Registro nao encontrado."
        code = "DATABASE_TABLE_NOT_FOUND" if str(exc) == "'table_not_allowed'" else "DATABASE_RECORD_NOT_FOUND"
        raise api_error(status_code=status.HTTP_404_NOT_FOUND, code=code, message=message) from exc
    return {"item": item}
