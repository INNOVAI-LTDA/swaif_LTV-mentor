from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.api.errors import api_error
from app.api.routes.auth import bearer, get_auth_service
from app.core.security import canonicalize_role
from app.services.auth_service import AuthService
from app.services.indicator_carga_service import IndicatorCargaService
from app.services.student_workspace_service import StudentContextError, StudentWorkspaceService
from app.storage.checkpoint_repository import CheckpointRepository
from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.measurement_overall_repository import MeasurementOverallRepository
from app.storage.measurement_repository import MeasurementRepository
from app.storage.metric_repository import MetricRepository
from app.storage.organization_repository import OrganizationRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.product_assignment_repository import ProductAssignmentRepository
from app.storage.protocol_repository import ProtocolRepository
from app.storage.student_repository import StudentRepository


router = APIRouter(prefix="/aluno/workspace", tags=["aluno-workspace"])


class StudentMeasurementUpdateRequest(BaseModel):
    value_current: float


def get_student_workspace_service() -> StudentWorkspaceService:
    students = StudentRepository()
    enrollments = EnrollmentRepository()
    measurements = MeasurementRepository()
    metrics = MetricRepository()
    pillars = PillarRepository()
    protocols = ProtocolRepository()
    organizations = OrganizationRepository()
    checkpoints = CheckpointRepository()
    measurement_overalls = MeasurementOverallRepository()

    indicator_carga = IndicatorCargaService(
        students=students,
        organizations=organizations,
        enrollments=enrollments,
        product_assignments=ProductAssignmentRepository(),
        metrics=metrics,
        measurements=measurements,
        checkpoints=checkpoints,
        pillars=pillars,
        protocols=protocols,
        measurement_overalls=measurement_overalls,
    )

    return StudentWorkspaceService(
        students=students,
        enrollments=enrollments,
        measurements=measurements,
        metrics=metrics,
        pillars=pillars,
        measurement_overalls=measurement_overalls,
        indicator_carga=indicator_carga,
    )


def require_aluno_user(
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

    if canonicalize_role(str(user.get("role"))) != "client":
        raise api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="AUTH_FORBIDDEN",
            message="Perfil aluno obrigatorio.",
        )

    return user


def _raise_student_context_error(exc: StudentContextError) -> None:
    detail = str(exc)
    if detail in {"student role required"}:
        raise api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="AUTH_FORBIDDEN",
            message="Perfil aluno obrigatorio.",
        ) from exc

    if detail in {"student context not found", "student context ambiguous", "active enrollment not found"}:
        raise api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="ALUNO_CONTEXT_NOT_FOUND",
            message="Contexto do aluno autenticado nao foi resolvido.",
        ) from exc

    if detail in {"measurement out of scope", "pillar out of scope"}:
        raise api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="MEASUREMENT_FORBIDDEN",
            message="Indicador fora do escopo autorizado do aluno.",
        ) from exc

    if detail in {"measurement not found", "measurement metric not found", "student radar not found", "pillar not found"}:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ALUNO_RESOURCE_NOT_FOUND",
            message="Recurso do workspace do aluno nao encontrado.",
        ) from exc

    if detail in {"value below min score", "value above max score", "measurement value invalid"}:
        raise api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="MEASUREMENT_VALUE_INVALID",
            message="Valor informado fora da faixa permitida para a metrica.",
        ) from exc

    raise api_error(
        status_code=status.HTTP_409_CONFLICT,
        code="ALUNO_WORKSPACE_CONFLICT",
        message="Nao foi possivel concluir a operacao no workspace do aluno.",
    ) from exc


@router.get("/radar")
def get_self_radar(
    user: dict[str, Any] = Depends(require_aluno_user),
    service: StudentWorkspaceService = Depends(get_student_workspace_service),
) -> dict[str, Any]:
    try:
        return service.get_self_radar(user=user)
    except StudentContextError as exc:
        _raise_student_context_error(exc)


@router.get("/pilares/{pillar_id}/metricas")
def list_self_pillar_measurements(
    pillar_id: str,
    user: dict[str, Any] = Depends(require_aluno_user),
    service: StudentWorkspaceService = Depends(get_student_workspace_service),
) -> dict[str, Any]:
    try:
        return service.list_self_pillar_measurements(user=user, pillar_id=pillar_id)
    except StudentContextError as exc:
        _raise_student_context_error(exc)


@router.patch("/measurements/{measurement_id}")
def update_self_measurement_current(
    measurement_id: str,
    payload: StudentMeasurementUpdateRequest,
    user: dict[str, Any] = Depends(require_aluno_user),
    service: StudentWorkspaceService = Depends(get_student_workspace_service),
) -> dict[str, Any]:
    try:
        return service.update_self_measurement_current(
            user=user,
            measurement_id=measurement_id,
            value_current=float(payload.value_current),
        )
    except StudentContextError as exc:
        _raise_student_context_error(exc)
