from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger("swaif.runtime")


@dataclass(frozen=True)
class AdminApiOperation:
    name: str
    description: str
    method: str
    endpoint: str


OPERATIONS_CATALOG: tuple[AdminApiOperation, ...] = (
    AdminApiOperation(
        name="Revalidar cache de clientes",
        description="Executa leitura consolidada de clientes para monitoramento operacional.",
        method="GET",
        endpoint="/admin/clientes",
    ),
    AdminApiOperation(
        name="Saude do backend",
        description="Consulta status atual do backend para validacao de disponibilidade.",
        method="GET",
        endpoint="/health",
    ),
)


class AdminApiOperationsService:
    def list_operations(self) -> list[dict[str, str]]:
        return [
            {
                "name": item.name,
                "description": item.description,
                "method": item.method,
                "endpoint": item.endpoint,
            }
            for item in OPERATIONS_CATALOG
        ]

    def execute_operation(self, *, admin_user_id: str, admin_email: str, operation_endpoint: str) -> dict[str, str]:
        operation = next((item for item in OPERATIONS_CATALOG if item.endpoint == operation_endpoint), None)
        if operation is None:
            raise ValueError("operation not found")

        timestamp = datetime.now(timezone.utc).isoformat()
        actor = admin_email or admin_user_id or "admin"
        logger.critical(
            "admin_api_operation_requested urgency=critical admin=%s operation=%s method=%s endpoint=%s at=%s",
            actor,
            operation.name,
            operation.method,
            operation.endpoint,
            timestamp,
        )
        return {
            "status": "success",
            "operation": operation.name,
            "method": operation.method,
            "endpoint": operation.endpoint,
            "requestedBy": actor,
            "requestedAt": timestamp,
        }
