from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials

from app.api.errors import api_error
from app.api.routes.auth import bearer, get_auth_service
from app.services.auth_service import AuthService
from app.services.mentor_demo_service import DEMO_MENTOR_EMAIL, EntityNotFoundError, MentorDemoService


router = APIRouter(prefix="/mentor", tags=["mentor-demo"])


def get_mentor_demo_service() -> MentorDemoService:
    return MentorDemoService()


def require_demo_mentor_user(
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

    if str(user.get("role")) != "mentor" or str(user.get("email")) != DEMO_MENTOR_EMAIL:
        raise api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="AUTH_FORBIDDEN",
            message="Perfil mentor demo obrigatorio.",
        )

    return user


def _raise_student_not_found(exc: EntityNotFoundError) -> None:
    raise api_error(
        status_code=status.HTTP_404_NOT_FOUND,
        code="ALUNO_NOT_FOUND",
        message="Aluno nao encontrado.",
    ) from exc


@router.get("/centro-comando/alunos")
def list_command_center_students(
    _: dict[str, Any] = Depends(require_demo_mentor_user),
    service: MentorDemoService = Depends(get_mentor_demo_service),
) -> list[dict[str, Any]]:
    return service.list_command_center_students()


@router.get("/centro-comando/alunos/{student_id}")
def get_command_center_student_detail(
    student_id: str,
    _: dict[str, Any] = Depends(require_demo_mentor_user),
    service: MentorDemoService = Depends(get_mentor_demo_service),
) -> dict[str, Any]:
    try:
        return service.get_student_detail(student_id=student_id)
    except EntityNotFoundError as exc:
        _raise_student_not_found(exc)


@router.get("/centro-comando/alunos/{student_id}/timeline-anomalias")
def get_command_center_timeline_anomalies(
    student_id: str,
    _: dict[str, Any] = Depends(require_demo_mentor_user),
    service: MentorDemoService = Depends(get_mentor_demo_service),
) -> dict[str, Any]:
    try:
        return service.get_command_center_timeline_anomalies(student_id=student_id)
    except EntityNotFoundError as exc:
        _raise_student_not_found(exc)


@router.get("/radar/alunos/{student_id}")
def get_student_radar(
    student_id: str,
    _: dict[str, Any] = Depends(require_demo_mentor_user),
    service: MentorDemoService = Depends(get_mentor_demo_service),
) -> dict[str, Any]:
    try:
        return service.get_student_radar(student_id=student_id)
    except EntityNotFoundError as exc:
        _raise_student_not_found(exc)


@router.get("/matriz-renovacao")
def get_renewal_matrix(
    filter: str = "all",
    _: dict[str, Any] = Depends(require_demo_mentor_user),
    service: MentorDemoService = Depends(get_mentor_demo_service),
) -> dict[str, Any]:
    return service.get_renewal_matrix(filter_mode=filter)
