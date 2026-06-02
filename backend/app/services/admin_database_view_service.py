from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.storage.admin_database_view_repository import AdminDatabaseViewRepository

logger = logging.getLogger("swaif.runtime")


@dataclass(frozen=True)
class TablePage:
    table: str
    items: list[dict[str, Any]]
    total: int
    limit: int
    offset: int


class AdminDatabaseViewService:
    def __init__(self, repository: AdminDatabaseViewRepository) -> None:
        self._repository = repository

    def list_tables(self) -> list[str]:
        return self._repository.list_tables()

    def list_records(self, *, table: str, limit: int, offset: int) -> TablePage:
        items, total = self._repository.list_records(table=table, limit=limit, offset=offset)
        return TablePage(table=table, items=items, total=total, limit=limit, offset=offset)

    def update_record(self, *, admin_id: str, table: str, record_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        updated = self._repository.update_record(table=table, record_id=record_id, changes=changes)
        logger.critical(
            "admin_database_view_data_changed urgency=critical admin_id=%s table=%s record_id=%s changed_fields=%s",
            admin_id,
            table,
            record_id,
            ",".join(sorted(changes.keys())),
        )
        return updated

    @staticmethod
    def _without_password_hash(item: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in item.items() if key != "password_hash"}

    @staticmethod
    def _normalize_user_ref(value: Any) -> str:
        raw = str(value or "").strip()
        if raw.startswith("usr_") or raw.startswith("mtr_") or raw.startswith("std_"):
            return raw[4:]
        return raw

    def _build_integrity(self, *, users_grouped: dict[str, list[dict[str, Any]]], products: list[dict[str, Any]], enrollments: list[dict[str, Any]], pillars: list[dict[str, Any]], metrics: list[dict[str, Any]], measurements: list[dict[str, Any]], checkpoints: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        provider_ids = {self._normalize_user_ref(item.get("id")) for item in users_grouped.get("providers", [])}
        client_ids = {self._normalize_user_ref(item.get("id")) for item in users_grouped.get("clients", [])}

        enrollment_ids = {str(item.get("id") or "").strip() for item in enrollments if str(item.get("id") or "").strip()}
        product_ids = {str(item.get("id") or "").strip() for item in products if str(item.get("id") or "").strip()}
        pillar_ids = {str(item.get("id") or "").strip() for item in pillars if str(item.get("id") or "").strip()}
        metric_ids = {str(item.get("id") or "").strip() for item in metrics if str(item.get("id") or "").strip()}

        provider_refs_in_enrollments: set[str] = set()
        client_refs_in_enrollments: set[str] = set()

        enrollments_without_provider: list[dict[str, Any]] = []
        enrollments_without_client: list[dict[str, Any]] = []
        enrollments_without_product: list[dict[str, Any]] = []

        for enrollment in enrollments:
            enrollment_id = str(enrollment.get("id") or "").strip()
            provider_ref = self._normalize_user_ref(enrollment.get("provider_user_id") or enrollment.get("mentor_id"))
            client_ref = self._normalize_user_ref(enrollment.get("client_user_id") or enrollment.get("student_id"))
            product_ref = str(enrollment.get("product_id") or enrollment.get("organization_id") or "").strip()

            if provider_ref:
                provider_refs_in_enrollments.add(provider_ref)
            if client_ref:
                client_refs_in_enrollments.add(client_ref)

            if not provider_ref or provider_ref not in provider_ids:
                enrollments_without_provider.append({"enrollmentId": enrollment_id, "providerRef": provider_ref})
            if not client_ref or client_ref not in client_ids:
                enrollments_without_client.append({"enrollmentId": enrollment_id, "clientRef": client_ref})
            if not product_ref or product_ref not in product_ids:
                enrollments_without_product.append({"enrollmentId": enrollment_id, "productRef": product_ref})

        providers_without_enrollments = [
            {"providerId": provider_id}
            for provider_id in sorted(provider_ids)
            if provider_id and provider_id not in provider_refs_in_enrollments
        ]
        clients_without_enrollments = [
            {"clientId": client_id}
            for client_id in sorted(client_ids)
            if client_id and client_id not in client_refs_in_enrollments
        ]

        measurements_without_enrollment = []
        measurements_without_metric = []
        for measurement in measurements:
            measurement_id = str(measurement.get("id") or "").strip()
            enrollment_ref = str(measurement.get("enrollment_id") or "").strip()
            metric_ref = str(measurement.get("metric_id") or "").strip()
            if not enrollment_ref or enrollment_ref not in enrollment_ids:
                measurements_without_enrollment.append({"measurementId": measurement_id, "enrollmentRef": enrollment_ref})
            if not metric_ref or metric_ref not in metric_ids:
                measurements_without_metric.append({"measurementId": measurement_id, "metricRef": metric_ref})

        checkpoints_without_enrollment = []
        for checkpoint in checkpoints:
            checkpoint_id = str(checkpoint.get("id") or "").strip()
            enrollment_ref = str(checkpoint.get("enrollment_id") or "").strip()
            if not enrollment_ref or enrollment_ref not in enrollment_ids:
                checkpoints_without_enrollment.append({"checkpointId": checkpoint_id, "enrollmentRef": enrollment_ref})

        products_without_organization = []
        for product in products:
            product_id = str(product.get("id") or "").strip()
            organization_ref = str(product.get("organization_id") or product.get("client_id") or "").strip()
            if not organization_ref:
                products_without_organization.append({"productId": product_id, "organizationRef": organization_ref})

        metrics_without_pillar = []
        for metric in metrics:
            metric_id = str(metric.get("id") or "").strip()
            pillar_ref = str(metric.get("pillar_id") or "").strip()
            if not pillar_ref or pillar_ref not in pillar_ids:
                metrics_without_pillar.append({"metricId": metric_id, "pillarRef": pillar_ref})

        pillars_without_product = []
        for pillar in pillars:
            pillar_id = str(pillar.get("id") or "").strip()
            product_ref = str(pillar.get("product_id") or "").strip()
            if not product_ref:
                pillars_without_product.append({"pillarId": pillar_id, "productRef": product_ref})

        return {
            "providersWithoutEnrollments": providers_without_enrollments,
            "clientsWithoutEnrollments": clients_without_enrollments,
            "enrollmentsWithoutProvider": enrollments_without_provider,
            "enrollmentsWithoutClient": enrollments_without_client,
            "enrollmentsWithoutProduct": enrollments_without_product,
            "measurementsWithoutEnrollment": measurements_without_enrollment,
            "measurementsWithoutMetric": measurements_without_metric,
            "checkpointsWithoutEnrollment": checkpoints_without_enrollment,
            "productsWithoutOrganization": products_without_organization,
            "metricsWithoutPillar": metrics_without_pillar,
            "pillarsWithoutProduct": pillars_without_product,
        }

    def get_database_view_snapshot(self) -> dict[str, Any]:
        payloads = self._repository.snapshot_payloads()

        organizations = list(payloads.get("organizations", {}).get("items", []))
        products = list(payloads.get("products", {}).get("items", []))
        enrollments = list(payloads.get("enrollments", {}).get("items", []))
        pillars = list(payloads.get("pillars", {}).get("items", []))
        metrics = list(payloads.get("metrics", {}).get("items", []))
        measurements = list(payloads.get("measurements", {}).get("items", []))
        checkpoints = list(payloads.get("checkpoints", {}).get("items", []))

        contacts = list(payloads.get("contacts_users_v2", {}).get("items", []))
        users_grouped = {
            "admins": [],
            "providers": [],
            "clients": [],
        }
        for item in contacts:
            role = str(item.get("role") or "").strip().lower()
            safe_item = self._without_password_hash(item)
            if role == "admin":
                users_grouped["admins"].append(safe_item)
            elif role == "provider":
                users_grouped["providers"].append(safe_item)
            elif role == "client":
                users_grouped["clients"].append(safe_item)

        integrity = self._build_integrity(
            users_grouped=users_grouped,
            products=products,
            enrollments=enrollments,
            pillars=pillars,
            metrics=metrics,
            measurements=measurements,
            checkpoints=checkpoints,
        )

        return {
            "organizations": organizations,
            "users": users_grouped,
            "products": products,
            "enrollments": enrollments,
            "pillars": pillars,
            "metrics": metrics,
            "measurements": measurements,
            "checkpoints": checkpoints,
            "integrity": integrity,
        }
