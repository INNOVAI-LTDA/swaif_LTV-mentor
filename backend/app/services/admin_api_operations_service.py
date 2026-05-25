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
        name="Provider View",
        description="Monitoramento operacional da visao de provider no painel administrativo.",
        method="GET",
        endpoint="/admin/provider-view",
    ),
    AdminApiOperation(
        name="Client View",
        description="Leitura do radar no contexto de client no painel administrativo.",
        method="GET",
        endpoint="/admin/client-view",
    ),
    AdminApiOperation(
        name="Database View",
        description="Consulta tabelas e registros permitidos na visao de banco.",
        method="GET",
        endpoint="/admin/database-view/tables",
    ),
    AdminApiOperation(
        name="API",
        description="Catalogo didatico de requests monitoraveis da area administrativa.",
        method="POST",
        endpoint="/admin/api-operations/execute",
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
