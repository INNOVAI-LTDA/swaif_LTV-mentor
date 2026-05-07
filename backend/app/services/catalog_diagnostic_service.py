from __future__ import annotations

from typing import Any

from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.measurement_repository import MeasurementRepository
from app.storage.metric_repository import MetricRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository
from app.storage.student_repository import StudentRepository


class CatalogDiagnosticService:
    def __init__(
        self,
        *,
        protocols: ProtocolRepository,
        pillars: PillarRepository,
        metrics: MetricRepository,
        enrollments: EnrollmentRepository,
        measurements: MeasurementRepository,
        students: StudentRepository,
    ) -> None:
        self._protocols = protocols
        self._pillars = pillars
        self._metrics = metrics
        self._enrollments = enrollments
        self._measurements = measurements
        self._students = students

    def build_report(self) -> dict[str, Any]:
        products = self._protocols.list_protocols()
        pillars = self._pillars.list_pillars()
        metrics = self._metrics.list_metrics()
        enrollments = self._enrollments.list_enrollments()
        measurements = self._measurements.list_measurements()
        students_by_id = {str(s.get("id")): s for s in self._students.list_students() if s.get("id")}

        pillars_by_product: dict[str, list[dict[str, Any]]] = {}
        for pillar in pillars:
            product_id = str(pillar.get("product_id") or pillar.get("protocol_id") or "")
            if product_id:
                pillars_by_product.setdefault(product_id, []).append(pillar)

        metrics_by_pillar: dict[str, list[dict[str, Any]]] = {}
        for metric in metrics:
            metrics_by_pillar.setdefault(str(metric.get("pillar_id") or ""), []).append(metric)

        measurements_by_enrollment: dict[str, set[str]] = {}
        for measurement in measurements:
            enrollment_id = str(measurement.get("enrollment_id") or "")
            metric_id = str(measurement.get("metric_id") or "")
            if not enrollment_id or not metric_id:
                continue
            measurements_by_enrollment.setdefault(enrollment_id, set()).add(metric_id)

        report_products: list[dict[str, Any]] = []
        coverage_errors: list[dict[str, Any]] = []

        for product in products:
            product_id = str(product.get("id") or "")
            expected_pillars = sorted(
                pillars_by_product.get(product_id, []),
                key=lambda row: int(row.get("order_index", 999)),
            )

            pillar_rows: list[dict[str, Any]] = []
            expected_metric_ids: set[str] = set()
            for pillar in expected_pillars:
                pillar_id = str(pillar.get("id") or "")
                pillar_metrics = metrics_by_pillar.get(pillar_id, [])
                has_metrics = len(pillar_metrics) > 0
                exception = bool((pillar.get("metadata") or {}).get("allow_no_metrics", False))
                if not has_metrics and not exception:
                    coverage_errors.append(
                        {
                            "product_id": product_id,
                            "pillar_id": pillar_id,
                            "issue": "pillar_without_metric",
                        }
                    )

                metric_ids = [str(metric.get("id")) for metric in pillar_metrics if metric.get("id")]
                expected_metric_ids.update(metric_ids)
                pillar_rows.append(
                    {
                        "pillar_id": pillar_id,
                        "pillar_name": str(pillar.get("name") or ""),
                        "metrics_count": len(metric_ids),
                        "metric_ids": metric_ids,
                        "allow_no_metrics": exception,
                    }
                )

            active_enrollments = [
                row
                for row in enrollments
                if bool(row.get("is_active", True)) and str(row.get("organization_id") or "") == product_id
            ]
            incomplete_students: list[dict[str, Any]] = []
            for enrollment in active_enrollments:
                enrollment_id = str(enrollment.get("id") or "")
                student_id = str(enrollment.get("student_id") or "")
                measured = measurements_by_enrollment.get(enrollment_id, set())
                missing_metric_ids = sorted(expected_metric_ids - measured)
                if missing_metric_ids:
                    incomplete_students.append(
                        {
                            "enrollment_id": enrollment_id,
                            "student_id": student_id,
                            "student_name": str((students_by_id.get(student_id) or {}).get("full_name") or student_id),
                            "missing_metric_ids": missing_metric_ids,
                        }
                    )

            report_products.append(
                {
                    "product_id": product_id,
                    "product_name": str(product.get("name") or ""),
                    "expected_pillars": [str(p.get("id") or "") for p in expected_pillars],
                    "present_pillars": [str(p.get("id") or "") for p in expected_pillars],
                    "pillars": pillar_rows,
                    "students_with_incomplete_data": incomplete_students,
                }
            )

        return {
            "canonical_source": "backend/data_new/pillars.json",
            "coverage_ok": len(coverage_errors) == 0,
            "coverage_errors": coverage_errors,
            "products": report_products,
        }
