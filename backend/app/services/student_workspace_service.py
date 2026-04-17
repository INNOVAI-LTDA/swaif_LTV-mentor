from __future__ import annotations

import math
from typing import Any

from app.core.security import canonicalize_role
from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.measurement_overall_repository import (
    ENGAGEMENT_PILLAR_BY_PROTOCOL,
    PRD_THR,
    PRODUCT_PILLARS_BY_PROTOCOL,
    ENG_THR,
    MeasurementOverallRepository,
)
from app.storage.measurement_repository import MeasurementRepository
from app.storage.metric_repository import MetricRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository
from app.storage.student_repository import StudentRepository
from app.services.indicator_carga_service import IndicatorCargaService, EntityNotFoundError as IndicatorEntityNotFoundError


class StudentContextError(Exception):
    pass


class StudentWorkspaceService:
    def __init__(
        self,
        *,
        students: StudentRepository,
        enrollments: EnrollmentRepository,
        measurements: MeasurementRepository,
        metrics: MetricRepository,
        pillars: PillarRepository,
        protocols: ProtocolRepository,
        measurement_overalls: MeasurementOverallRepository,
        indicator_carga: IndicatorCargaService,
    ) -> None:
        self._students = students
        self._enrollments = enrollments
        self._measurements = measurements
        self._metrics = metrics
        self._pillars = pillars
        self._protocols = protocols
        self._measurement_overalls = measurement_overalls
        self._indicator_carga = indicator_carga

    @staticmethod
    def _normalize_email(value: Any) -> str:
        return str(value or "").strip().lower()

    @staticmethod
    def _geometric_mean(values: list[float]) -> float:
        if not values:
            return 0.0
        non_negative = [max(0.0, float(value)) for value in values]
        if any(value == 0.0 for value in non_negative):
            return 0.0
        log_sum = sum(math.log(value) for value in non_negative)
        return round(math.exp(log_sum / len(non_negative)), 6)

    def resolve_student_context(self, *, user: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        if canonicalize_role(str(user.get("role"))) != "aluno":
            raise StudentContextError("student role required")

        explicit_student_id = str(user.get("student_id") or "")
        student: dict[str, Any] | None = None
        if explicit_student_id:
            student = self._students.get_by_id(explicit_student_id)

        if not student:
            user_email = self._normalize_email(user.get("email"))
            matches = [
                row
                for row in self._students.list_students()
                if self._normalize_email(row.get("email")) == user_email and bool(row.get("is_active", True))
            ]
            if len(matches) > 1:
                raise StudentContextError("student context ambiguous")
            student = matches[0] if matches else None

        if not student:
            raise StudentContextError("student context not found")

        enrollment = self._enrollments.get_active_by_student(str(student.get("id") or ""))
        if not enrollment:
            raise StudentContextError("active enrollment not found")

        return student, enrollment

    def get_self_radar(self, *, user: dict[str, Any]) -> dict[str, Any]:
        student, _ = self.resolve_student_context(user=user)
        try:
            return self._indicator_carga.get_student_radar(student_id=str(student["id"]))
        except IndicatorEntityNotFoundError as exc:
            raise StudentContextError("student radar not found") from exc

    def list_self_pillar_measurements(self, *, user: dict[str, Any], pillar_id: str) -> dict[str, Any]:
        student, enrollment = self.resolve_student_context(user=user)
        resolved_pillar = self._resolve_pillar_identifier(pillar_id)
        if not resolved_pillar:
            raise StudentContextError("pillar not found")
        if not self._is_pillar_in_enrollment_scope(enrollment=enrollment, pillar=resolved_pillar):
            raise StudentContextError("pillar out of scope")

        resolved_pillar_id = str(resolved_pillar.get("id") or "")
        metrics_by_id = {str(metric.get("id") or ""): metric for metric in self._metrics.list_metrics()}
        measurements = self._measurements.list_by_enrollment(str(enrollment["id"]))

        items: list[dict[str, Any]] = []
        for measurement in measurements:
            metric = metrics_by_id.get(str(measurement.get("metric_id") or ""))
            if not metric or str(metric.get("pillar_id") or "") != resolved_pillar_id:
                continue

            items.append(
                {
                    "measurementId": str(measurement.get("id") or ""),
                    "metricId": str(metric.get("id") or ""),
                    "metricLabel": str(metric.get("name") or "Indicador"),
                    "direction": str(metric.get("direction") or "higher_better"),
                    "unit": metric.get("unit"),
                    "valueBaseline": float(measurement.get("value_baseline") or 0),
                    "valueCurrent": float(measurement.get("value_current") or 0),
                    "valueProjected": None
                    if measurement.get("value_projected") is None
                    else float(measurement.get("value_projected")),
                    "improvingTrend": measurement.get("improving_trend"),
                    "minScore": metric.get("min_score"),
                    "maxScore": metric.get("max_score"),
                }
            )

        return {
            "studentId": str(student.get("id") or ""),
            "enrollmentId": str(enrollment.get("id") or ""),
            "pillar": {
                "id": resolved_pillar_id,
                "name": str(resolved_pillar.get("name") or "Pilar"),
                "code": str(resolved_pillar.get("code") or resolved_pillar_id),
            },
            "items": items,
        }

    def _is_pillar_in_enrollment_scope(self, *, enrollment: dict[str, Any], pillar: dict[str, Any]) -> bool:
        organization_id = str(enrollment.get("organization_id") or "")
        if not organization_id:
            return False

        protocol_ids = {
            str(protocol.get("id") or "")
            for protocol in self._protocols.list_by_organization(organization_id)
            if str(protocol.get("id") or "")
        }
        if not protocol_ids:
            return False

        pillar_protocol_id = str(pillar.get("protocol_id") or "")
        return bool(pillar_protocol_id and pillar_protocol_id in protocol_ids)

    def _resolve_pillar_identifier(self, pillar_identifier: str) -> dict[str, Any] | None:
        direct = self._pillars.get_by_id(pillar_identifier)
        if direct:
            return direct

        normalized = str(pillar_identifier or "").strip().lower()
        if not normalized:
            return None

        for pillar in self._pillars.list_pillars():
            if str(pillar.get("code") or "").strip().lower() == normalized:
                return pillar
        return None

    def update_self_measurement_current(
        self,
        *,
        user: dict[str, Any],
        measurement_id: str,
        value_current: float,
    ) -> dict[str, Any]:
        _, enrollment = self.resolve_student_context(user=user)

        measurement = self._measurements.get_by_id(measurement_id)
        if not measurement:
            raise StudentContextError("measurement not found")

        enrollment_id = str(enrollment.get("id") or "")
        if str(measurement.get("enrollment_id") or "") != enrollment_id:
            raise StudentContextError("measurement out of scope")

        metric = self._metrics.get_by_id(str(measurement.get("metric_id") or ""))
        if not metric:
            raise StudentContextError("measurement metric not found")

        min_score = metric.get("min_score")
        max_score = metric.get("max_score")
        if min_score is not None and float(value_current) < float(min_score):
            raise StudentContextError("value below min score")
        if max_score is not None and float(value_current) > float(max_score):
            raise StudentContextError("value above max score")

        updated = self._measurements.update_value_current(measurement_id=measurement_id, value_current=value_current)
        existing_overall = self._measurement_overalls.get_by_enrollment(enrollment_id=enrollment_id)
        protocol_id = str((existing_overall or {}).get("protocol_id") or "")
        self._recompute_enrollment_derived(
            enrollment_id=enrollment_id,
            protocol_id=protocol_id,
            affected_pillar_id=str(metric.get("pillar_id") or ""),
        )

        return {
            "measurementId": str(updated.get("id") or ""),
            "metricId": str(updated.get("metric_id") or ""),
            "valueCurrent": float(updated.get("value_current") or 0),
            "pillarId": str(metric.get("pillar_id") or ""),
            "enrollmentId": enrollment_id,
        }

    def _recompute_enrollment_derived(self, *, enrollment_id: str, protocol_id: str, affected_pillar_id: str) -> None:
        overall = self._measurement_overalls.get_by_enrollment(enrollment_id)
        if not overall:
            return

        metrics_payload = overall.get("metrics")
        pillars_payload = overall.get("pillars")
        if not isinstance(metrics_payload, list) or not isinstance(pillars_payload, list):
            return

        metrics_by_id = {str(metric.get("id") or ""): metric for metric in self._metrics.list_metrics()}
        metric_values_by_id = {
            str(row.get("metric_id") or ""): row
            for row in metrics_payload
            if isinstance(row, dict) and row.get("metric_id")
        }

        measurements = self._measurements.list_by_enrollment(enrollment_id)
        for measurement in measurements:
            metric_id = str(measurement.get("metric_id") or "")
            metric_row = metric_values_by_id.get(metric_id)
            if not metric_row:
                continue
            values = metric_row.get("values") if isinstance(metric_row.get("values"), dict) else {}
            values["real"] = float(measurement.get("value_current") or 0)
            metric_row["values"] = values

        affected_metric_values: list[dict[str, float]] = []
        for metric_id, metric_row in metric_values_by_id.items():
            metric = metrics_by_id.get(metric_id)
            if not metric or str(metric.get("pillar_id") or "") != affected_pillar_id:
                continue
            values = metric_row.get("values") if isinstance(metric_row.get("values"), dict) else {}
            affected_metric_values.append(
                {
                    "goal": float(values.get("goal") or 0.0),
                    "base": float(values.get("base") or 0.0),
                    "real": float(values.get("real") or 0.0),
                }
            )

        if affected_metric_values:
            recomputed = {
                "goal": self._geometric_mean([row["goal"] for row in affected_metric_values]),
                "base": self._geometric_mean([row["base"] for row in affected_metric_values]),
                "real": self._geometric_mean([row["real"] for row in affected_metric_values]),
            }
            for pillar_row in pillars_payload:
                if not isinstance(pillar_row, dict):
                    continue
                if str(pillar_row.get("pillar_id") or "") == affected_pillar_id:
                    pillar_row["metric_average"] = recomputed
                    break

        decision_matrix = overall.get("decision_matrix")
        if isinstance(decision_matrix, dict):
            pillar_real_by_id: dict[str, float] = {}
            for pillar_row in pillars_payload:
                if not isinstance(pillar_row, dict):
                    continue
                metric_average = pillar_row.get("metric_average") if isinstance(pillar_row.get("metric_average"), dict) else {}
                pillar_real_by_id[str(pillar_row.get("pillar_id") or "")] = float(metric_average.get("real") or 0.0)

            product_pillars = PRODUCT_PILLARS_BY_PROTOCOL.get(protocol_id, set())
            engagement_pillar = ENGAGEMENT_PILLAR_BY_PROTOCOL.get(protocol_id)
            product_values = [pillar_real_by_id.get(pillar_id, 0.0) for pillar_id in product_pillars]

            decision_matrix["product_score"] = (
                sum(product_values) / len(product_values)
                if product_values
                else 0.0
            )
            decision_matrix["engagement_score"] = pillar_real_by_id.get(engagement_pillar, 0.0) if engagement_pillar else 0.0
            decision_matrix["thresholds"] = {"prd_thr": PRD_THR, "eng_thr": ENG_THR}
            overall["decision_matrix"] = decision_matrix

        overall["metrics"] = metrics_payload
        overall["pillars"] = pillars_payload
        self._measurement_overalls.upsert_for_enrollment(enrollment_id=enrollment_id, data=overall)
