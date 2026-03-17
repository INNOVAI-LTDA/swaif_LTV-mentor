from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.errors import api_error
from app.api.routes.admin_mentoria import require_admin_user
from app.schemas.enrollment import (
    EnrollmentOut,
    EnrollmentWithStudentOut,
    LinkStudentMentoriaRequest,
    ReassignStudentRequest,
    UnlinkStudentRequest,
)
from app.schemas.indicator_load import IndicatorLoadRequest, IndicatorLoadResult
from app.schemas.student import AdminStudentCreate, AdminStudentOut, StudentCreate, StudentOut
from app.services.admin_student_link_service import AdminStudentLinkService
from app.services.admin_student_link_service import ConsistencyError as AdminLinkConsistencyError
from app.services.admin_student_link_service import EntityNotFoundError as AdminLinkEntityNotFoundError
from app.services.admin_student_link_service import ValidationError as AdminLinkValidationError
from app.services.admin_student_service import AdminStudentService, ConsistencyError as AdminConsistencyError
from app.services.admin_student_service import EntityNotFoundError as AdminEntityNotFoundError
from app.services.admin_student_service import ValidationError as AdminValidationError
from app.services.indicator_carga_service import EntityNotFoundError as IndicatorEntityNotFoundError
from app.services.indicator_carga_service import IndicatorCargaService
from app.services.student_vinculo_service import ConsistencyError, EntityNotFoundError, StudentVinculoService
from app.storage.checkpoint_repository import CheckpointRepository
from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.measurement_repository import MeasurementRepository
from app.storage.metric_repository import MetricRepository
from app.storage.mentor_repository import MentorRepository
from app.storage.organization_repository import OrganizationRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.student_repository import StudentRepository


router = APIRouter(prefix="/admin", tags=["admin-alunos"])


def get_student_vinculo_service() -> StudentVinculoService:
    return StudentVinculoService(
        organizations=OrganizationRepository(),
        students=StudentRepository(),
        enrollments=EnrollmentRepository(),
    )


def get_indicator_carga_service() -> IndicatorCargaService:
    return IndicatorCargaService(
        students=StudentRepository(),
        organizations=OrganizationRepository(),
        enrollments=EnrollmentRepository(),
        metrics=MetricRepository(),
        measurements=MeasurementRepository(),
        checkpoints=CheckpointRepository(),
        pillars=PillarRepository(),
    )


def get_admin_student_service() -> AdminStudentService:
    return AdminStudentService(
        organizations=OrganizationRepository(),
        mentors=MentorRepository(),
        students=StudentRepository(),
        enrollments=EnrollmentRepository(),
    )


def get_admin_student_link_service() -> AdminStudentLinkService:
    return AdminStudentLinkService(
        organizations=OrganizationRepository(),
        mentors=MentorRepository(),
        students=StudentRepository(),
        enrollments=EnrollmentRepository(),
    )


def _map_student_not_found(exc: EntityNotFoundError) -> tuple[str, str]:
    detail = str(exc)
    if detail == "student not found":
        return "ALUNO_NOT_FOUND", "Aluno nao encontrado."
    return "MENTORIA_NOT_FOUND", "Mentoria nao encontrada."


def _map_student_consistency_error(exc: ConsistencyError) -> tuple[str, str]:
    detail = str(exc)
    if detail == "progress score must be between 0 and 1":
        return "ALUNO_PROGRESS_OUT_OF_RANGE", "Progresso deve estar entre 0 e 1."
    if detail == "engagement score must be between 0 and 1":
        return "ALUNO_ENGAGEMENT_OUT_OF_RANGE", "Engajamento deve estar entre 0 e 1."
    if detail == "timeline values must be non-negative":
        return "ALUNO_TIMELINE_INVALID", "Campos de tempo devem ser nao negativos."
    if detail == "day cannot be greater than total_days":
        return "ALUNO_TIMELINE_INVALID", "Dia nao pode ser maior que total_days."
    return "ALUNO_CONFLICT", "Conflito de dados do aluno."


def _map_indicator_not_found(exc: IndicatorEntityNotFoundError) -> tuple[str, str]:
    detail = str(exc)
    if detail == "metric not found":
        return "INDICADOR_NOT_FOUND", "Indicador nao encontrado."
    if detail == "student not found":
        return "ALUNO_NOT_FOUND", "Aluno nao encontrado."
    if detail == "student enrollment not found":
        return "MATRICULA_NOT_FOUND", "Vinculo do aluno com mentoria nao encontrado."
    return "RESOURCE_NOT_FOUND", "Recurso nao encontrado."


def _map_admin_student_not_found(exc: AdminEntityNotFoundError) -> tuple[str, str]:
    detail = str(exc)
    if detail == "mentor not found":
        return "MENTOR_NOT_FOUND", "Mentor nao encontrado."
    return "PRODUTO_NOT_FOUND", "Produto nao encontrado."


def _map_admin_link_not_found(exc: AdminLinkEntityNotFoundError) -> tuple[str, str]:
    detail = str(exc)
    if detail == "student not found":
        return "ALUNO_NOT_FOUND", "Aluno nao encontrado."
    if detail == "mentor not found":
        return "MENTOR_NOT_FOUND", "Mentor nao encontrado."
    if detail == "product not found":
        return "PRODUTO_NOT_FOUND", "Produto nao encontrado."
    return "MATRICULA_NOT_FOUND", "Vinculo ativo do aluno nao encontrado."


def _map_admin_link_consistency(exc: AdminLinkConsistencyError) -> tuple[str, str]:
    detail = str(exc)
    if detail == "student already linked to mentor":
        return "VINCULO_DUPLICADO", "O aluno ja esta vinculado a este mentor."
    if detail == "mentor product mismatch":
        return "VINCULO_INVALIDO", "O mentor precisa pertencer ao mesmo produto do aluno."
    return "VINCULO_INVALIDO", "O mentor precisa estar vinculado a um produto ativo."


@router.post("/alunos", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    _: dict[str, Any] = Depends(require_admin_user),
    service: StudentVinculoService = Depends(get_student_vinculo_service),
) -> StudentOut:
    try:
        student = service.create_student(
            full_name=payload.full_name,
            initials=payload.initials,
            email=payload.email,
        )
    except ValueError as exc:
        raise api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="ALUNO_CONFLICT",
            message="Ja existe aluno com este email.",
        ) from exc
    return StudentOut(**student)


@router.post("/mentores/{mentor_id}/alunos", response_model=AdminStudentOut, status_code=status.HTTP_201_CREATED)
def create_student_by_mentor(
    mentor_id: str,
    payload: AdminStudentCreate,
    _: dict[str, Any] = Depends(require_admin_user),
    service: AdminStudentService = Depends(get_admin_student_service),
) -> AdminStudentOut:
    try:
        student = service.create_student(
            mentor_id=mentor_id,
            full_name=payload.full_name,
            cpf=payload.cpf,
            email=payload.email,
            phone=payload.phone,
            notes=payload.notes,
        )
    except AdminEntityNotFoundError as exc:
        code, message = _map_admin_student_not_found(exc)
        raise api_error(status_code=status.HTTP_404_NOT_FOUND, code=code, message=message) from exc
    except AdminValidationError as exc:
        raise api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="ALUNO_INVALIDO",
            message="Nome completo e CPF do aluno sao obrigatorios.",
        ) from exc
    except AdminConsistencyError as exc:
        raise api_error(
            status_code=status.HTTP_409_CONFLICT,
            code="ALUNO_CONFLICT",
            message="O mentor precisa estar vinculado a um produto ativo.",
        ) from exc
    except ValueError as exc:
        message = "Ja existe aluno com este CPF." if str(exc) == "student cpf already exists" else "Ja existe aluno com este email."
        raise api_error(status_code=status.HTTP_409_CONFLICT, code="ALUNO_CONFLICT", message=message) from exc
    return AdminStudentOut(**student)


@router.post("/alunos/{student_id}/vincular-mentoria", response_model=EnrollmentOut)
def link_student_to_mentoria(
    student_id: str,
    payload: LinkStudentMentoriaRequest,
    _: dict[str, Any] = Depends(require_admin_user),
    service: StudentVinculoService = Depends(get_student_vinculo_service),
) -> EnrollmentOut:
    try:
        enrollment = service.link_student_to_organization(
            student_id=student_id,
            organization_id=payload.organization_id,
            mentor_id=payload.mentor_id,
            progress_score=payload.progress_score,
            engagement_score=payload.engagement_score,
            urgency_status=payload.urgency_status,
            day=payload.day,
            total_days=payload.total_days,
            days_left=payload.days_left,
            ltv_cents=payload.ltv_cents,
        )
    except EntityNotFoundError as exc:
        error_code, message = _map_student_not_found(exc)
        raise api_error(status_code=status.HTTP_404_NOT_FOUND, code=error_code, message=message) from exc
    except ConsistencyError as exc:
        error_code, message = _map_student_consistency_error(exc)
        raise api_error(status_code=status.HTTP_409_CONFLICT, code=error_code, message=message) from exc
    return EnrollmentOut(**enrollment)


@router.get("/mentorias/{organization_id}/alunos", response_model=list[EnrollmentWithStudentOut])
def list_students_by_mentoria(
    organization_id: str,
    _: dict[str, Any] = Depends(require_admin_user),
    service: StudentVinculoService = Depends(get_student_vinculo_service),
) -> list[EnrollmentWithStudentOut]:
    try:
        items = service.list_students_by_organization(organization_id)
    except EntityNotFoundError as exc:
        raise api_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code="MENTORIA_NOT_FOUND",
            message="Mentoria nao encontrada.",
        ) from exc
    return [EnrollmentWithStudentOut(**item) for item in items]


@router.get("/produtos/{product_id}/alunos", response_model=list[AdminStudentOut])
def list_students_by_product(
    product_id: str,
    _: dict[str, Any] = Depends(require_admin_user),
    service: AdminStudentService = Depends(get_admin_student_service),
) -> list[AdminStudentOut]:
    try:
        items = service.list_students_by_product(product_id)
    except AdminEntityNotFoundError as exc:
        raise api_error(status_code=status.HTTP_404_NOT_FOUND, code="PRODUTO_NOT_FOUND", message="Produto nao encontrado.") from exc
    return [AdminStudentOut(**item) for item in items]


@router.get("/mentores/{mentor_id}/alunos", response_model=list[AdminStudentOut])
def list_students_by_mentor(
    mentor_id: str,
    _: dict[str, Any] = Depends(require_admin_user),
    service: AdminStudentService = Depends(get_admin_student_service),
) -> list[AdminStudentOut]:
    try:
        items = service.list_students_by_mentor(mentor_id)
    except AdminEntityNotFoundError as exc:
        raise api_error(status_code=status.HTTP_404_NOT_FOUND, code="MENTOR_NOT_FOUND", message="Mentor nao encontrado.") from exc
    return [AdminStudentOut(**item) for item in items]


@router.post("/alunos/{student_id}/reatribuir-mentor", response_model=AdminStudentOut)
def reassign_student_to_mentor(
    student_id: str,
    payload: ReassignStudentRequest,
    current_user: dict[str, Any] = Depends(require_admin_user),
    service: AdminStudentLinkService = Depends(get_admin_student_link_service),
) -> AdminStudentOut:
    try:
        student = service.reassign_student(
            student_id=student_id,
            target_mentor_id=payload.target_mentor_id,
            justificativa=payload.justificativa,
            performed_by=str(current_user.get("email") or current_user.get("id") or "admin"),
        )
    except AdminLinkEntityNotFoundError as exc:
        code, message = _map_admin_link_not_found(exc)
        raise api_error(status_code=status.HTTP_404_NOT_FOUND, code=code, message=message) from exc
    except AdminLinkValidationError as exc:
        raise api_error(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code="VINCULO_INVALIDO", message="Justificativa obrigatoria.") from exc
    except AdminLinkConsistencyError as exc:
        code, message = _map_admin_link_consistency(exc)
        raise api_error(status_code=status.HTTP_409_CONFLICT, code=code, message=message) from exc
    return AdminStudentOut(**student)


@router.post("/alunos/{student_id}/desvincular", response_model=EnrollmentOut)
def unlink_student_from_mentor(
    student_id: str,
    payload: UnlinkStudentRequest,
    current_user: dict[str, Any] = Depends(require_admin_user),
    service: AdminStudentLinkService = Depends(get_admin_student_link_service),
) -> EnrollmentOut:
    try:
        enrollment = service.unlink_student(
            student_id=student_id,
            justificativa=payload.justificativa,
            performed_by=str(current_user.get("email") or current_user.get("id") or "admin"),
        )
    except AdminLinkEntityNotFoundError as exc:
        code, message = _map_admin_link_not_found(exc)
        raise api_error(status_code=status.HTTP_404_NOT_FOUND, code=code, message=message) from exc
    except AdminLinkValidationError as exc:
        raise api_error(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code="VINCULO_INVALIDO", message="Justificativa obrigatoria.") from exc
    return EnrollmentOut(**enrollment)


@router.post("/alunos/{student_id}/indicadores/carga-inicial", response_model=IndicatorLoadResult)
def load_initial_indicators(
    student_id: str,
    payload: IndicatorLoadRequest,
    _: dict[str, Any] = Depends(require_admin_user),
    service: IndicatorCargaService = Depends(get_indicator_carga_service),
) -> IndicatorLoadResult:
    try:
        result = service.load_initial_indicators(
            student_id=student_id,
            metric_values=[row.model_dump() for row in payload.metric_values],
            checkpoints=[row.model_dump() for row in payload.checkpoints],
        )
    except IndicatorEntityNotFoundError as exc:
        error_code, message = _map_indicator_not_found(exc)
        raise api_error(status_code=status.HTTP_404_NOT_FOUND, code=error_code, message=message) from exc
    return IndicatorLoadResult(**result)


@router.get("/alunos/{student_id}/detalhe")
def get_student_detail(
    student_id: str,
    _: dict[str, Any] = Depends(require_admin_user),
    service: IndicatorCargaService = Depends(get_indicator_carga_service),
) -> dict[str, Any]:
    try:
        return service.get_student_detail(student_id=student_id)
    except IndicatorEntityNotFoundError as exc:
        error_code, message = _map_indicator_not_found(exc)
        raise api_error(status_code=status.HTTP_404_NOT_FOUND, code=error_code, message=message) from exc


@router.get("/centro-comando/alunos")
def list_command_center_students(
    _: dict[str, Any] = Depends(require_admin_user),
    service: IndicatorCargaService = Depends(get_indicator_carga_service),
) -> list[dict[str, Any]]:
    return service.list_command_center_students()


@router.get("/centro-comando/alunos/{student_id}")
def get_command_center_student_detail(
    student_id: str,
    _: dict[str, Any] = Depends(require_admin_user),
    service: IndicatorCargaService = Depends(get_indicator_carga_service),
) -> dict[str, Any]:
    try:
        return service.get_student_detail(student_id=student_id)
    except IndicatorEntityNotFoundError as exc:
        error_code, message = _map_indicator_not_found(exc)
        raise api_error(status_code=status.HTTP_404_NOT_FOUND, code=error_code, message=message) from exc


@router.get("/centro-comando/alunos/{student_id}/timeline-anomalias")
def get_command_center_timeline_anomalies(
    student_id: str,
    _: dict[str, Any] = Depends(require_admin_user),
    service: IndicatorCargaService = Depends(get_indicator_carga_service),
) -> dict[str, Any]:
    try:
        return service.get_command_center_timeline_anomalies(student_id=student_id)
    except IndicatorEntityNotFoundError as exc:
        error_code, message = _map_indicator_not_found(exc)
        raise api_error(status_code=status.HTTP_404_NOT_FOUND, code=error_code, message=message) from exc


@router.get("/radar/alunos/{student_id}")
def get_student_radar(
    student_id: str,
    _: dict[str, Any] = Depends(require_admin_user),
    service: IndicatorCargaService = Depends(get_indicator_carga_service),
) -> dict[str, Any]:
    try:
        return service.get_student_radar(student_id=student_id)
    except IndicatorEntityNotFoundError as exc:
        error_code, message = _map_indicator_not_found(exc)
        raise api_error(status_code=status.HTTP_404_NOT_FOUND, code=error_code, message=message) from exc


@router.get("/matriz-renovacao")
def get_renewal_matrix(
    filter: str = "all",
    _: dict[str, Any] = Depends(require_admin_user),
    service: IndicatorCargaService = Depends(get_indicator_carga_service),
) -> dict[str, Any]:
    return service.get_renewal_matrix(filter_mode=filter)
