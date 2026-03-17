from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.errors import api_error
from app.api.routes.admin_mentoria import require_admin_user
from app.schemas.mentor import AdminMentorCreate, MentorOut
from app.services.admin_mentor_service import AdminMentorService, EntityNotFoundError, ValidationError
from app.storage.mentor_repository import MentorRepository
from app.storage.organization_repository import OrganizationRepository


router = APIRouter(prefix="/admin", tags=["admin-mentores"])


def get_admin_mentor_service() -> AdminMentorService:
    return AdminMentorService(OrganizationRepository(), MentorRepository())


@router.get("/produtos/{product_id}/mentores", response_model=list[MentorOut])
def list_mentors_by_product(
    product_id: str,
    _: dict[str, Any] = Depends(require_admin_user),
    service: AdminMentorService = Depends(get_admin_mentor_service),
) -> list[MentorOut]:
    try:
        return [MentorOut(**item) for item in service.list_mentors_by_product(product_id)]
    except EntityNotFoundError as exc:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="PRODUTO_NOT_FOUND",
            message="Produto nao encontrado.",
        ) from exc


@router.post("/produtos/{product_id}/mentores", response_model=MentorOut, status_code=status.HTTP_201_CREATED)
def create_mentor(
    product_id: str,
    payload: AdminMentorCreate,
    _: dict[str, Any] = Depends(require_admin_user),
    service: AdminMentorService = Depends(get_admin_mentor_service),
) -> MentorOut:
    try:
        mentor = service.create_mentor(
            product_id=product_id,
            full_name=payload.full_name,
            cpf=payload.cpf,
            email=payload.email,
            phone=payload.phone,
            bio=payload.bio,
            notes=payload.notes,
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
            code="MENTOR_INVALIDO",
            message="Nome completo, CPF e email do mentor sao obrigatorios.",
        ) from exc
    except ValueError as exc:
        detail = str(exc)
        message = "Ja existe mentor com este CPF." if detail == "mentor cpf already exists" else "Ja existe mentor com este email."
        raise api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="MENTOR_CONFLICT",
            message=message,
        ) from exc
    return MentorOut(**mentor)
