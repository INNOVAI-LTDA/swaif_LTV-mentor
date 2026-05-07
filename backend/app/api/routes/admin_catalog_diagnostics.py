from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.api.routes.admin_students import require_admin_user
from app.services.catalog_diagnostic_service import CatalogDiagnosticService
from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.measurement_repository import MeasurementRepository
from app.storage.metric_repository import MetricRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository
from app.storage.student_repository import StudentRepository

router = APIRouter(prefix="/admin", tags=["admin-catalogo"])


def get_catalog_diagnostic_service() -> CatalogDiagnosticService:
    return CatalogDiagnosticService(
        protocols=ProtocolRepository(),
        pillars=PillarRepository(),
        metrics=MetricRepository(),
        enrollments=EnrollmentRepository(),
        measurements=MeasurementRepository(),
        students=StudentRepository(),
    )


@router.get("/catalogo/diagnostico")
def get_catalog_diagnostics(
    _: dict[str, Any] = Depends(require_admin_user),
    service: CatalogDiagnosticService = Depends(get_catalog_diagnostic_service),
) -> dict[str, Any]:
    return service.build_report()
