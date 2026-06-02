from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials

from app.api.errors import api_error
from app.api.routes.auth import bearer, get_auth_service
from app.config.runtime import get_supabase_db_url
from app.core.security import canonicalize_role
from app.services.provider_hierarchy_service import ProviderHierarchyService
from app.services.auth_service import AuthService
from app.storage.supabase_enrollment_repository import SupabaseEnrollmentRepository
from app.storage.supabase_product_metric_repository import SupabaseProductMetricRepository
from app.storage.supabase_runtime_measurement_repository import SupabaseRuntimeMeasurementRepository
from app.storage.supabase_provider_hierarchy_repository import SupabaseProviderHierarchyRepository


router = APIRouter(prefix="/provider", tags=["provider"])


def _require_supabase_db_url() -> str:
    database_url = get_supabase_db_url()
    if database_url:
        return database_url
    raise api_error(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code="SUPABASE_DB_URL_REQUIRED",
        message="SUPABASE_DB_URL obrigatorio para runtime Supabase do provider.",
    )


def require_provider_user(
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

    if not bool(user.get("is_active", False)):
        raise api_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTH_INVALID_TOKEN",
            message="Token de acesso invalido.",
        )

    if canonicalize_role(str(user.get("role") or "")) != "provider":
        raise api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code="AUTH_FORBIDDEN",
            message="Perfil provider obrigatorio.",
        )

    return user


def get_provider_hierarchy_service() -> ProviderHierarchyService:
    _require_supabase_db_url()
    repository = SupabaseProviderHierarchyRepository()
    return ProviderHierarchyService(repository)


def get_supabase_enrollment_repository() -> SupabaseEnrollmentRepository:
    _require_supabase_db_url()
    return SupabaseEnrollmentRepository()


def get_supabase_product_metric_repository() -> SupabaseProductMetricRepository:
    _require_supabase_db_url()
    return SupabaseProductMetricRepository()


def get_supabase_runtime_measurement_repository() -> SupabaseRuntimeMeasurementRepository:
    _require_supabase_db_url()
    return SupabaseRuntimeMeasurementRepository()


@router.get("/me")
def get_provider_me(user: dict[str, Any] = Depends(require_provider_user)) -> dict[str, Any]:
    return {
        "id": str(user.get("id") or ""),
        "email": str(user.get("email") or ""),
        "fullName": str(user.get("full_name") or ""),
        "role": canonicalize_role(str(user.get("role") or "")),
        "organizationId": str(user.get("organization_id") or ""),
    }


@router.get("/me/hierarchy")
def get_provider_me_hierarchy(
    user: dict[str, Any] = Depends(require_provider_user),
    service: ProviderHierarchyService = Depends(get_provider_hierarchy_service),
) -> dict[str, Any]:
    return service.get_provider_hierarchy(str(user.get("id") or ""))


@router.get("/me/enrollments/{enrollment_id}/metric-tree")
def get_provider_enrollment_metric_tree(
    enrollment_id: str,
    user: dict[str, Any] = Depends(require_provider_user),
    service: ProviderHierarchyService = Depends(get_provider_hierarchy_service),
    enrollment_repository: SupabaseEnrollmentRepository = Depends(get_supabase_enrollment_repository),
    product_metric_repository: SupabaseProductMetricRepository = Depends(get_supabase_product_metric_repository),
    measurement_repository: SupabaseRuntimeMeasurementRepository = Depends(get_supabase_runtime_measurement_repository),
) -> dict[str, Any]:
    try:
        return service.get_provider_enrollment_metric_tree(
            str(user.get("id") or ""),
            enrollment_id,
            enrollment_repository=enrollment_repository,
            product_metric_repository=product_metric_repository,
            measurement_repository=measurement_repository,
        )
    except ValueError as error:
        if str(error) == "enrollment_not_found":
            raise api_error(
                status_code=status.HTTP_404_NOT_FOUND,
                code="ENROLLMENT_NOT_FOUND",
                message="Enrollment nao encontrado para o provider autenticado.",
            ) from error
        raise
