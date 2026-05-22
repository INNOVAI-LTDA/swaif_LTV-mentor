from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.api.errors import api_error
from app.api.routes.admin_students import require_admin_user
from app.services.admin_provider_view_service import AdminProviderViewService

router = APIRouter(prefix="/admin/provider-view", tags=["admin-provider-view"])


class ProviderConsentRequest(BaseModel):
    provider_id: str
    provider_name: str
    operation: str
    consent_granted: bool


def get_admin_provider_view_service() -> AdminProviderViewService:
    return AdminProviderViewService()


@router.post("/consent")
def register_provider_consent(
    payload: ProviderConsentRequest,
    admin: dict[str, Any] = Depends(require_admin_user),
    service: AdminProviderViewService = Depends(get_admin_provider_view_service),
) -> dict[str, Any]:
    if not payload.provider_id.strip() or not payload.operation.strip() or not payload.provider_name.strip():
        raise api_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="PROVIDER_CONSENT_INVALID",
            message="provider_id, provider_name e operation sao obrigatorios.",
        )

    result = service.register_attempt(
        admin_id=str(admin.get("id") or ""),
        provider_id=payload.provider_id.strip(),
        provider_name=payload.provider_name.strip(),
        operation=payload.operation.strip(),
        consent_granted=payload.consent_granted,
    )
    return {
        "providerId": result.provider_id,
        "providerName": result.provider_name,
        "operation": result.operation,
        "consentGranted": result.consent_granted,
        "adminId": result.actor_admin_id,
    }
