from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials

from app.api.errors import api_error
from app.api.routes.auth import bearer, get_auth_service
from app.services.indicator_carga_service import EntityNotFoundError as IndicatorEntityNotFoundError
from app.services.indicator_carga_service import IndicatorCargaService
from app.services.auth_service import AuthService
from app.storage.checkpoint_repository import CheckpointRepository
from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.measurement_overall_repository import MeasurementOverallRepository
from app.storage.measurement_repository import MeasurementRepository
from app.storage.mentor_repository import MentorRepository
from app.storage.metric_repository import MetricRepository
from app.storage.organization_repository import OrganizationRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository
from app.storage.student_repository import StudentRepository


router = APIRouter(prefix="/mentor", tags=["mentor"])


def get_indicator_carga_service() -> IndicatorCargaService:
    return IndicatorCargaService(
        students=StudentRepository(),
        organizations=OrganizationRepository(),
        enrollments=EnrollmentRepository(),
        metrics=MetricRepository(),
        measurements=MeasurementRepository(),
        checkpoints=CheckpointRepository(),
        pillars=PillarRepository(),
        protocols=ProtocolRepository(),
        measurement_overalls=MeasurementOverallRepository(),
    )


def get_mentor_repository() -> MentorRepository:
    return MentorRepository()


def require_mentor_user(
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

    if str(user.get("role")) != "mentor":
        raise api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="AUTH_FORBIDDEN",
            message="Perfil mentor obrigatorio.",
        )

    return user


def require_mentor_profile(
    user: dict[str, Any] = Depends(require_mentor_user),
    mentors: MentorRepository = Depends(get_mentor_repository),
) -> dict[str, Any]:
    mentor = mentors.get_by_email(str(user.get("email") or ""))
    if not mentor:
        raise api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="AUTH_FORBIDDEN",
            message="Mentor sem cadastro vinculado.",
        )
    return mentor


def _raise_student_not_found(exc: IndicatorEntityNotFoundError) -> None:
    if str(exc) == "student enrollment not found":
        message = "Aluno nao encontrado na carteira do mentor."
    else:
        message = "Aluno nao encontrado."
    raise api_error(
        status_code=status.HTTP_404_NOT_FOUND,
        code="ALUNO_NOT_FOUND",
        message=message,
    ) from exc


@router.get("/centro-comando/alunos")
def list_command_center_students(
    mentor: dict[str, Any] = Depends(require_mentor_profile),
    service: IndicatorCargaService = Depends(get_indicator_carga_service),
) -> dict[str, Any]:
    payload = service.list_command_center_students(mentor_id=str(mentor["id"]))
    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    payload["context"] = {
        **context,
        "mentorId": str(mentor.get("id") or ""),
        "mentorName": str(mentor.get("full_name") or mentor.get("id") or "Mentor"),
    }
    return payload


@router.get("/centro-comando/alunos/{student_id}")
def get_command_center_student_detail(
    student_id: str,
    mentor: dict[str, Any] = Depends(require_mentor_profile),
    service: IndicatorCargaService = Depends(get_indicator_carga_service),
) -> dict[str, Any]:
    try:
        return service.get_student_detail(student_id=student_id, mentor_id=str(mentor["id"]))
    except IndicatorEntityNotFoundError as exc:
        _raise_student_not_found(exc)


@router.get("/centro-comando/alunos/{student_id}/timeline-anomalias")
def get_command_center_timeline_anomalies(
    student_id: str,
    mentor: dict[str, Any] = Depends(require_mentor_profile),
    service: IndicatorCargaService = Depends(get_indicator_carga_service),
) -> dict[str, Any]:
    try:
        return service.get_command_center_timeline_anomalies(student_id=student_id, mentor_id=str(mentor["id"]))
    except IndicatorEntityNotFoundError as exc:
        _raise_student_not_found(exc)


@router.get("/radar/alunos/{student_id}")
def get_student_radar(
    student_id: str,
    mentor: dict[str, Any] = Depends(require_mentor_profile),
    service: IndicatorCargaService = Depends(get_indicator_carga_service),
) -> dict[str, Any]:
    try:
        payload = service.get_student_radar(student_id=student_id, mentor_id=str(mentor["id"]))
        context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
        payload["context"] = {
            **context,
            "mentorId": str(mentor.get("id") or ""),
            "mentorName": str(mentor.get("full_name") or mentor.get("id") or "Mentor"),
        }
        return payload
    except IndicatorEntityNotFoundError as exc:
        _raise_student_not_found(exc)


@router.get("/matriz-renovacao")
def get_renewal_matrix(
    filter: str = "all",
    mentor: dict[str, Any] = Depends(require_mentor_profile),
    service: IndicatorCargaService = Depends(get_indicator_carga_service),
) -> dict[str, Any]:
    payload = service.get_renewal_matrix(filter_mode=filter, mentor_id=str(mentor["id"]))
    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    payload["context"] = {
        **context,
        "mentorId": str(mentor.get("id") or ""),
        "mentorName": str(mentor.get("full_name") or mentor.get("id") or "Mentor"),
    }
    return payload