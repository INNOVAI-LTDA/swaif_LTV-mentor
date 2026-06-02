from __future__ import annotations

from typing import Any


class ProviderHierarchyService:
    def __init__(self, hierarchy_repository: Any) -> None:
        self._hierarchy_repository = hierarchy_repository

    def get_provider_hierarchy(self, provider_user_id: str) -> dict[str, Any]:
        rows = self._hierarchy_repository.list_active_provider_hierarchy(provider_user_id)
        if not rows:
            return {
                "provider": {},
                "organization": {},
                "products": [],
                "enrollments": [],
                "clients": [],
            }

        first = rows[0]
        provider = {
            "id": str(first.get("provider_id") or ""),
            "name": str(first.get("provider_name") or ""),
            "email": str(first.get("provider_email") or ""),
            "organizationId": str(first.get("provider_organization_id") or ""),
        }
        organization = {
            "id": str(first.get("organization_id") or ""),
            "name": str(first.get("organization_name") or ""),
            "slug": str(first.get("organization_slug") or ""),
        }

        products: list[dict[str, Any]] = []
        enrollments: list[dict[str, Any]] = []
        clients: list[dict[str, Any]] = []

        seen_product_ids: set[str] = set()
        seen_client_ids: set[str] = set()

        for row in rows:
            product_id = str(row.get("product_id") or "")
            if product_id and product_id not in seen_product_ids:
                products.append(
                    {
                        "id": product_id,
                        "name": str(row.get("product_name") or ""),
                        "slug": str(row.get("product_slug") or ""),
                        "category": str(row.get("product_category") or ""),
                    }
                )
                seen_product_ids.add(product_id)

            enrollments.append(
                {
                    "id": str(row.get("enrollment_id") or ""),
                    "status": str(row.get("enrollment_status") or ""),
                    "startDay": row.get("start_day"),
                    "daysLeft": row.get("days_left"),
                    "investment": row.get("investment"),
                    "decisionMatrixStatus": row.get("decision_matrix_status"),
                    "providerUserId": str(row.get("provider_id") or ""),
                    "clientUserId": str(row.get("client_id") or ""),
                    "productId": product_id,
                }
            )

            client_id = str(row.get("client_id") or "")
            if client_id and client_id not in seen_client_ids:
                clients.append(
                    {
                        "id": client_id,
                        "name": str(row.get("client_name") or ""),
                        "email": str(row.get("client_email") or ""),
                    }
                )
                seen_client_ids.add(client_id)

        return {
            "provider": provider,
            "organization": organization,
            "products": products,
            "enrollments": enrollments,
            "clients": clients,
        }

    def get_provider_enrollment_metric_tree(
        self,
        provider_user_id: str,
        enrollment_id: str,
        *,
        enrollment_repository: Any,
        product_metric_repository: Any,
        measurement_repository: Any,
    ) -> dict[str, Any]:
        enrollments = enrollment_repository.list_active_by_provider(provider_user_id)
        enrollment = next((item for item in enrollments if str(item.get("id") or "") == enrollment_id), None)
        if enrollment is None:
            raise ValueError("enrollment_not_found")

        product_id = str(enrollment.get("product_id") or "")
        metric_tree = product_metric_repository.list_metric_tree_by_product(product_id)
        measurements = measurement_repository.list_by_enrollment(enrollment_id)
        measurements_by_metric_id = {str(item.get("metric_id") or ""): item for item in measurements}

        pillars: list[dict[str, Any]] = []
        for pillar in metric_tree:
            metrics: list[dict[str, Any]] = []
            for metric in pillar.get("metrics", []):
                metric_id = str(metric.get("id") or "")
                measurement = measurements_by_metric_id.get(metric_id)
                metrics.append(
                    {
                        **metric,
                        "measurement": measurement,
                    }
                )

            pillars.append(
                {
                    "id": str(pillar.get("id") or ""),
                    "name": str(pillar.get("name") or ""),
                    "slug": str(pillar.get("slug") or ""),
                    "orderIndex": pillar.get("orderIndex"),
                    "metrics": metrics,
                }
            )

        return {
            "enrollmentId": enrollment_id,
            "productId": product_id,
            "pillars": pillars,
        }
