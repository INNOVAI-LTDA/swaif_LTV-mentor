from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.api.errors import api_error
from app.api.routes.provider import require_provider_user
from app.config.runtime import get_supabase_db_url, require_supabase_runtime_database_url
from app.core.security import canonicalize_role
from app.services.client_metric_transformation_service import process_mock_client_absolute_metrics
from app.services.indicator_carga_service import EntityNotFoundError as IndicatorEntityNotFoundError
from app.services.indicator_carga_service import IndicatorCargaService
from app.services.provider_workspace_service import ProviderWorkspaceService
from app.services.student_workspace_service import StudentContextError, StudentWorkspaceService
from app.storage.checkpoint_repository import CheckpointRepository
from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.analytical_history_repository import AnalyticalHistoryRepository
from app.storage.measurement_overall_repository import MeasurementOverallRepository
from app.storage.measurement_history_repository import MeasurementHistoryRepository
from app.storage.measurement_repository import MeasurementRepository
from app.storage.metric_repository import MetricRepository
from app.storage.organization_repository import OrganizationRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.postgres_indicator_repositories import (
    PostgresAnalyticalHistoryRepository,
    PostgresCheckpointRepository,
    PostgresMeasurementHistoryRepository,
    PostgresMeasurementRepository,
)
from app.storage.product_assignment_repository import ProductAssignmentRepository
from app.storage.protocol_repository import ProtocolRepository
from app.storage.student_repository import StudentRepository
from app.storage.supabase_provider_hierarchy_repository import SupabaseProviderHierarchyRepository
from app.storage.supabase_product_metric_repository import SupabaseProductMetricRepository
from app.storage.supabase_runtime_measurement_repository import SupabaseRuntimeMeasurementRepository


router = APIRouter(prefix="/mentor", tags=["mentor"])


class MentorMeasurementUpdateRequest(BaseModel):
    value_current: float


def _resolve_indicator_runtime_repositories() -> tuple[Any, Any]:
    try:
        database_url = require_supabase_runtime_database_url(flow_name="/mentor runtime repositories")
    except RuntimeError as exc:
        raise api_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="SUPABASE_DB_URL_REQUIRED",
            message="SUPABASE_DB_URL obrigatorio para runtime sem fallback JSON.",
        ) from exc
    if database_url:
        return PostgresMeasurementRepository(database_url), PostgresCheckpointRepository(database_url)
    return MeasurementRepository(), CheckpointRepository()


def _resolve_student_workspace_runtime_repositories() -> tuple[Any, Any, Any, Any]:
    try:
        database_url = require_supabase_runtime_database_url(flow_name="/mentor student workspace repositories")
    except RuntimeError as exc:
        raise api_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="SUPABASE_DB_URL_REQUIRED",
            message="SUPABASE_DB_URL obrigatorio para runtime sem fallback JSON.",
        ) from exc
    if database_url:
        return (
            PostgresMeasurementRepository(database_url),
            PostgresCheckpointRepository(database_url),
            PostgresMeasurementHistoryRepository(database_url),
            PostgresAnalyticalHistoryRepository(database_url),
        )
    return MeasurementRepository(), CheckpointRepository(), MeasurementHistoryRepository(), AnalyticalHistoryRepository()


def get_indicator_carga_service() -> IndicatorCargaService:
    measurements, checkpoints = _resolve_indicator_runtime_repositories()
    return IndicatorCargaService(
        students=StudentRepository(),
        organizations=OrganizationRepository(),
        enrollments=EnrollmentRepository(),
        product_assignments=ProductAssignmentRepository(),
        metrics=MetricRepository(),
        measurements=measurements,
        checkpoints=checkpoints,
        pillars=PillarRepository(),
        protocols=ProtocolRepository(),
        measurement_overalls=MeasurementOverallRepository(),
    )


def get_provider_workspace_service() -> ProviderWorkspaceService:
    database_url = get_supabase_db_url()
    if not database_url:
        raise api_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="SUPABASE_DB_URL_REQUIRED",
            message="SUPABASE_DB_URL obrigatorio para runtime Supabase no workspace do provider.",
        )
    return ProviderWorkspaceService(
        SupabaseProviderHierarchyRepository(),
        product_metric_repository=SupabaseProductMetricRepository(),
        runtime_measurement_repository=SupabaseRuntimeMeasurementRepository(),
    )


def get_student_workspace_service() -> StudentWorkspaceService:
    students = StudentRepository()
    enrollments = EnrollmentRepository()
    measurements, _, measurement_history, analytical_history = _resolve_student_workspace_runtime_repositories()
    metrics = MetricRepository()
    pillars = PillarRepository()
    measurement_overalls = MeasurementOverallRepository()
    indicator_carga = get_indicator_carga_service()
    return StudentWorkspaceService(
        students=students,
        enrollments=enrollments,
        measurements=measurements,
        metrics=metrics,
        pillars=pillars,
        measurement_overalls=measurement_overalls,
        indicator_carga=indicator_carga,
        measurement_history=measurement_history,
        analytical_history=analytical_history,
    )


def require_mentor_profile(
    user: dict[str, Any] = Depends(require_provider_user),
) -> dict[str, Any]:
    user_id = str(user.get("id") or "")
    mentor_id = user_id[4:] if user_id.startswith("usr_") else user_id
    return {
        "id": mentor_id,
        "email": str(user.get("email") or ""),
        "full_name": str(user.get("full_name") or user.get("email") or mentor_id),
        "organization_id": user.get("organization_id"),
        "role": canonicalize_role(str(user.get("role") or "provider")),
    }


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


def _raise_student_workspace_error(exc: StudentContextError) -> None:
    if str(exc) in {"measurement out of scope", "pillar out of scope", "active enrollment not found"}:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ALUNO_NOT_FOUND",
            message="Aluno nao encontrado na carteira do mentor.",
        ) from exc
    if str(exc) in {"pillar not found", "measurement not found", "measurement metric not found", "student radar not found"}:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ALUNO_RESOURCE_NOT_FOUND",
            message="Recurso do workspace do aluno nao encontrado.",
        ) from exc
    if str(exc) in {"value below min score", "value above max score", "measurement value invalid"}:
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


@router.get("/centro-comando/alunos")
def list_command_center_students(
    mentor: dict[str, Any] = Depends(require_mentor_profile),
    service: ProviderWorkspaceService = Depends(get_provider_workspace_service),
) -> dict[str, Any]:
    payload = service.list_command_center_students(provider_user_id=str(mentor["id"]))
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
    service: ProviderWorkspaceService = Depends(get_provider_workspace_service),
) -> dict[str, Any]:
    try:
        payload = service.get_student_radar(
            provider_user_id=str(mentor["id"]),
            client_user_id=student_id,
        )
        context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
        payload["context"] = {
            **context,
            "mentorId": str(mentor.get("id") or ""),
            "mentorName": str(mentor.get("full_name") or mentor.get("id") or "Mentor"),
        }
        return payload
    except ValueError as error:
        if str(error) == "enrollment_not_found":
            raise api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="ALUNO_NOT_FOUND",
                message="Aluno nao encontrado na carteira do mentor.",
            ) from error
        raise


@router.get("/radar/clientes")
def get_clients_radar(
    include_mock_preview: bool = False,
    mentor: dict[str, Any] = Depends(require_mentor_profile),
    service: ProviderWorkspaceService = Depends(get_provider_workspace_service),
) -> dict[str, Any]:
    payload = service.get_clients_radar(provider_user_id=str(mentor["id"]))
    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    payload["context"] = {
        **context,
        "mentorId": str(mentor.get("id") or ""),
        "mentorName": str(mentor.get("full_name") or mentor.get("id") or "Mentor"),
    }
    if include_mock_preview:
        payload["mockTransformationPreview"] = process_mock_client_absolute_metrics()
    return payload


@router.get("/matriz-renovacao")
def get_renewal_matrix(
    filter: str = "all",
    mentor: dict[str, Any] = Depends(require_mentor_profile),
    service: ProviderWorkspaceService = Depends(get_provider_workspace_service),
) -> dict[str, Any]:
    payload = service.get_renewal_matrix(filter_mode=filter, provider_user_id=str(mentor["id"]))
    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    payload["context"] = {
        **context,
        "mentorId": str(mentor.get("id") or ""),
        "mentorName": str(mentor.get("full_name") or mentor.get("id") or "Mentor"),
    }
    return payload


@router.get("/radar/alunos/{student_id}/pilares/{pillar_id}/metricas")
def get_student_pillar_metrics(
    student_id: str,
    pillar_id: str,
    mentor: dict[str, Any] = Depends(require_mentor_profile),
    service: StudentWorkspaceService = Depends(get_student_workspace_service),
) -> dict[str, Any]:
    try:
        return service.list_student_pillar_measurements_for_mentor(
            mentor_id=str(mentor["id"]),
            student_id=student_id,
            pillar_id=pillar_id,
        )
    except StudentContextError as exc:
        _raise_student_workspace_error(exc)


@router.patch("/radar/alunos/{student_id}/measurements/{measurement_id}")
def update_student_measurement_current(
    student_id: str,
    measurement_id: str,
    payload: MentorMeasurementUpdateRequest,
    mentor: dict[str, Any] = Depends(require_mentor_profile),
    service: StudentWorkspaceService = Depends(get_student_workspace_service),
) -> dict[str, Any]:
    try:
        return service.update_student_measurement_current_for_mentor(
            mentor_id=str(mentor["id"]),
            student_id=student_id,
            measurement_id=measurement_id,
            value_current=float(payload.value_current),
        )
    except StudentContextError as exc:
        _raise_student_workspace_error(exc)
