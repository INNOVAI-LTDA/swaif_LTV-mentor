from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials

from app.api.errors import api_error
from app.api.routes.auth import bearer, get_auth_service
from app.schemas.mentor import MentorCreate, MentorOut
from app.schemas.organization import LinkMentorRequest, OrganizationCreate, OrganizationOut
from app.services.auth_service import AuthService
from app.services.mentoria_service import EntityNotFoundError, MentoriaService
from app.storage.mentor_repository import MentorRepository
from app.storage.organization_repository import OrganizationRepository


router = APIRouter(prefix="/admin", tags=["admin-mentoria"])


def get_mentoria_service() -> MentoriaService:
    return MentoriaService(OrganizationRepository(), MentorRepository())


def _map_mentoria_not_found_error(exc: EntityNotFoundError) -> tuple[str, str]:
    detail = str(exc)
    if detail == "mentor not found":
        return "MENTOR_NOT_FOUND", "Mentor nao encontrado."
    return "MENTORIA_NOT_FOUND", "Mentoria nao encontrada."


def require_admin_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    auth: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    if credentials is None:
        raise api_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTH_MISSING_TOKEN",
            message="Token de acesso ausente.",
        )

    user = auth.get_current_user(credentials.credentials)
    if not user:
        raise api_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTH_INVALID_TOKEN",
            message="Token de acesso invalido.",
        )
    if str(user.get("role")) != "admin":
        raise api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="AUTH_FORBIDDEN",
            message="Perfil admin obrigatorio.",
        )
    return user


@router.post("/mentorias", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
def create_mentoria(
    payload: OrganizationCreate,
    _: dict[str, Any] = Depends(require_admin_user),
    service: MentoriaService = Depends(get_mentoria_service),
) -> OrganizationOut:
    try:
        org = service.create_organization(name=payload.name, slug=payload.slug)
    except ValueError as exc:
        raise api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="MENTORIA_CONFLICT",
            message="Ja existe mentoria com este slug.",
        ) from exc
    return OrganizationOut(**org)


@router.post("/mentores", response_model=MentorOut, status_code=status.HTTP_201_CREATED)
def create_mentor(
    payload: MentorCreate,
    _: dict[str, Any] = Depends(require_admin_user),
    service: MentoriaService = Depends(get_mentoria_service),
) -> MentorOut:
    try:
        mentor = service.create_mentor(full_name=payload.full_name, email=payload.email)
    except ValueError as exc:
        raise api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="MENTOR_CONFLICT",
            message="Ja existe mentor com este email.",
        ) from exc
    return MentorOut(**mentor)


@router.post("/mentorias/{organization_id}/vincular-mentor", response_model=OrganizationOut)
def link_mentor_to_mentoria(
    organization_id: str,
    payload: LinkMentorRequest,
    _: dict[str, Any] = Depends(require_admin_user),
    service: MentoriaService = Depends(get_mentoria_service),
) -> OrganizationOut:
    try:
        linked = service.link_mentor_to_organization(organization_id, payload.mentor_id)
    except EntityNotFoundError as exc:
        error_code, message = _map_mentoria_not_found_error(exc)
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code=error_code,
            message=message,
        ) from exc
    return OrganizationOut(**linked)


@router.get("/mentorias/{organization_id}")
def get_mentoria_detail(
    organization_id: str,
    _: dict[str, Any] = Depends(require_admin_user),
    service: MentoriaService = Depends(get_mentoria_service),
) -> dict[str, Any]:
    try:
        return service.get_organization_with_mentor(organization_id)
    except EntityNotFoundError as exc:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="MENTORIA_NOT_FOUND",
            message="Mentoria nao encontrada.",
        ) from exc
