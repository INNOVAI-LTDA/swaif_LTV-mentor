from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("swaif.runtime")


@dataclass
class ProviderConsentResult:
    provider_id: str
    provider_name: str
    operation: str
    consent_granted: bool
    actor_admin_id: str


class AdminProviderViewService:
    def register_attempt(self, *, admin_id: str, provider_id: str, provider_name: str, operation: str, consent_granted: bool) -> ProviderConsentResult:
        logger.critical(
            "admin_provider_view_edit_attempt admin_id=%s provider_id=%s provider_name=%s operation=%s consent_granted=%s",
            admin_id,
            provider_id,
            provider_name,
            operation,
            consent_granted,
        )
        return ProviderConsentResult(
            provider_id=provider_id,
            provider_name=provider_name,
            operation=operation,
            consent_granted=consent_granted,
            actor_admin_id=admin_id,
        )
