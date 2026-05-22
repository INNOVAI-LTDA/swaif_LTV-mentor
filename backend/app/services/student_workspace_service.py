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
from app.storage.student_repository import StudentRepository
from app.services.indicator_carga_service import IndicatorCargaService, EntityNotFoundError as IndicatorEntityNotFoundError
from app.services.metric_score_service import ScoreCalculationError, calculate_metric_score


PROJECTION_FORMULA_VERSION = "v1_pillar_geomean_product_geomean"


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
        measurement_overalls: MeasurementOverallRepository,
        indicator_carga: IndicatorCargaService,
        measurement_history: Any | None = None,
        analytical_history: Any | None = None,
    ) -> None:
        self._students = students
        self._enrollments = enrollments
        self._measurements = measurements
        self._metrics = metrics
        self._pillars = pillars
        self._measurement_overalls = measurement_overalls
        self._indicator_carga = indicator_carga
        self._measurement_history = measurement_history
        self._analytical_history = analytical_history

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

    @staticmethod
    def _classify_quadrant(*, progress: float, engagement: float, prd_thr: float, eng_thr: float) -> str:
        if progress >= prd_thr and engagement >= eng_thr:
            return "topRight"
        if progress < 0.3 and engagement < 0.3:
            return "bottomLeft"
        if progress < prd_thr and engagement >= eng_thr:
            return "topLeft"
        if progress >= prd_thr and engagement < eng_thr:
            return "bottomRight"
        return "bottomLeft"

    def resolve_student_context(self, *, user: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        if canonicalize_role(str(user.get("role"))) != "client":
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
        student, enrollment = self.resolve_student_context(user=user)
        try:
            payload = self._indicator_carga.get_student_radar(student_id=str(student["id"]))
            payload["pillarScores"] = self._build_client_pillar_scores(payload)
            payload["metricScoresByPillar"] = self._build_client_metric_scores(
                enrollment_id=str(enrollment.get("id") or "")
            )
            return payload
        except IndicatorEntityNotFoundError as exc:
            raise StudentContextError("student radar not found") from exc

    def _build_client_pillar_scores(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        axis_scores = payload.get("axisScores") if isinstance(payload.get("axisScores"), list) else []
        items: list[dict[str, Any]] = []
        for axis in axis_scores:
            if not isinstance(axis, dict):
                continue
            items.append(
                {
                    "pillarId": str(axis.get("axisId") or ""),
                    "pillarKey": str(axis.get("axisKey") or ""),
                    "pillarLabel": str(axis.get("axisLabel") or ""),
                    "baseline": float(axis.get("baseline") or 0.0),
                    "current": float(axis.get("current") or 0.0),
                    "goal": float(axis.get("projected") or axis.get("current") or 0.0),
                }
            )
        return items

    def _build_client_metric_scores(self, *, enrollment_id: str) -> list[dict[str, Any]]:
        if not enrollment_id:
            return []

        metrics_by_id = {str(metric.get("id") or ""): metric for metric in self._metrics.list_metrics()}
        pillars_by_id = {str(pillar.get("id") or ""): pillar for pillar in self._pillars.list_pillars()}
        grouped: dict[str, dict[str, Any]] = {}

        measurements = self._measurements.list_by_enrollment(enrollment_id)
        for measurement in measurements:
            metric = metrics_by_id.get(str(measurement.get("metric_id") or ""))
            if not metric:
                continue

            pillar_id = str(metric.get("pillar_id") or "")
            if not pillar_id:
                continue

            pillar = pillars_by_id.get(pillar_id) or {}
            pillar_bucket = grouped.setdefault(
                pillar_id,
                {
                    "pillarId": pillar_id,
                    "pillarKey": str(pillar.get("code") or pillar_id),
                    "pillarLabel": str(pillar.get("name") or pillar_id),
                    "_pillarOrder": int(pillar.get("order_index") or 999),
                    "items": [],
                },
            )

            projected_raw = measurement.get("value_projected")
            goal = measurement.get("value_current") if projected_raw is None else projected_raw
            pillar_bucket["items"].append(
                {
                    "measurementId": str(measurement.get("id") or ""),
                    "metricId": str(metric.get("id") or ""),
                    "metricKey": str(metric.get("code") or metric.get("id") or ""),
                    "metricLabel": str(metric.get("name") or "Indicador"),
                    "baseline": float(measurement.get("value_baseline") or 0.0),
                    "current": float(measurement.get("value_current") or 0.0),
                    "goal": float(goal or 0.0),
                    "direction": str(metric.get("direction") or "higher_better"),
                    "unit": metric.get("unit"),
                    "_metricOrder": int(metric.get("order_index") or 999),
                }
            )

        result = list(grouped.values())
        result.sort(key=lambda row: int(row.get("_pillarOrder") or 999))
        for row in result:
            items = row.get("items") if isinstance(row.get("items"), list) else []
            items.sort(key=lambda metric: (int(metric.get("_metricOrder") or 999), str(metric.get("metricLabel") or "")))
            for metric in items:
                metric.pop("_metricOrder", None)
            row.pop("_pillarOrder", None)
        return result

    def list_self_pillar_measurements(self, *, user: dict[str, Any], pillar_id: str) -> dict[str, Any]:
        student, enrollment = self.resolve_student_context(user=user)
        return self._list_pillar_measurements(student=student, enrollment=enrollment, pillar_id=pillar_id)

    def list_student_pillar_measurements_for_mentor(self, *, mentor_id: str, student_id: str, pillar_id: str) -> dict[str, Any]:
        student = self._students.get_by_id(student_id)
        if not student:
            raise StudentContextError("student radar not found")
        enrollment = self._enrollments.get_active_by_student(student_id)
        if not enrollment:
            raise StudentContextError("active enrollment not found")
        if str(enrollment.get("mentor_id") or "") != mentor_id:
            raise StudentContextError("measurement out of scope")
        return self._list_pillar_measurements(student=student, enrollment=enrollment, pillar_id=pillar_id)

    def _list_pillar_measurements(self, *, student: dict[str, Any], enrollment: dict[str, Any], pillar_id: str) -> dict[str, Any]:
        resolved_pillar = self._resolve_pillar_identifier(pillar_id)
        if not resolved_pillar:
            raise StudentContextError("pillar not found")

        resolved_pillar_id = str(resolved_pillar.get("id") or "")
        resolved_pillar_protocol_id = str(resolved_pillar.get("protocol_id") or "")
        enrollment_id = str(enrollment.get("id") or "")
        overall = self._measurement_overalls.get_by_enrollment(enrollment_id=enrollment_id)
        enrollment_protocol_id = str((overall or {}).get("protocol_id") or "")

        metrics_by_id = {str(metric.get("id") or ""): metric for metric in self._metrics.list_metrics()}
        measurements = self._measurements.list_by_enrollment(enrollment_id)

        in_scope = bool(enrollment_protocol_id and enrollment_protocol_id == resolved_pillar_protocol_id)
        if not in_scope:
            in_scope = any(
                str((metrics_by_id.get(str(measurement.get("metric_id") or "")) or {}).get("pillar_id") or "") == resolved_pillar_id
                for measurement in measurements
            )
        if not in_scope:
            raise StudentContextError("pillar out of scope")

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
            "enrollmentId": enrollment_id,
            "pillar": {
                "id": resolved_pillar_id,
                "name": str(resolved_pillar.get("name") or "Pilar"),
                "code": str(resolved_pillar.get("code") or resolved_pillar_id),
            },
            "items": items,
        }

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
        return self._update_measurement_current(
            actor=user,
            enrollment=enrollment,
            measurement_id=measurement_id,
            value_current=value_current,
        )

    def update_student_measurement_current_for_mentor(
        self,
        *,
        mentor_id: str,
        student_id: str,
        measurement_id: str,
        value_current: float,
    ) -> dict[str, Any]:
        student = self._students.get_by_id(student_id)
        if not student:
            raise StudentContextError("student radar not found")

        enrollment = self._enrollments.get_active_by_student(student_id)
        if not enrollment:
            raise StudentContextError("active enrollment not found")
        if str(enrollment.get("mentor_id") or "") != mentor_id:
            raise StudentContextError("measurement out of scope")

        return self._update_measurement_current(
            actor={"id": mentor_id, "role": "provider"},
            enrollment=enrollment,
            measurement_id=measurement_id,
            value_current=value_current,
        )

    def _update_measurement_current(
        self,
        *,
        actor: dict[str, Any],
        enrollment: dict[str, Any],
        measurement_id: str,
        value_current: float,
    ) -> dict[str, Any]:
        measurement = self._measurements.get_by_id(measurement_id)
        if not measurement:
            raise StudentContextError("measurement not found")

        enrollment_id = str(enrollment.get("id") or "")
        if str(measurement.get("enrollment_id") or "") != enrollment_id:
            raise StudentContextError("measurement out of scope")

        metric = self._metrics.get_by_id(str(measurement.get("metric_id") or ""))
        if not metric:
            raise StudentContextError("measurement metric not found")

        try:
            calculate_metric_score(metric, value_current)
        except ScoreCalculationError as exc:
            raise StudentContextError("measurement value invalid") from exc

        before_relative = self._calculate_normalized_score(metric=metric, value=measurement.get("value_current"))
        after_relative = self._calculate_normalized_score(metric=metric, value=value_current)

        updated = self._measurements.update_value_current(measurement_id=measurement_id, value_current=value_current)
        existing_overall = self._measurement_overalls.get_by_enrollment(enrollment_id=enrollment_id)
        protocol_id = str((existing_overall or {}).get("protocol_id") or "")
        self._recompute_enrollment_derived(
            enrollment_id=enrollment_id,
            protocol_id=protocol_id,
            affected_pillar_id=str(metric.get("pillar_id") or ""),
        )
        self._append_measurement_history_event(
            user=actor,
            metric=metric,
            measurement_before=measurement,
            measurement_after=updated,
            value_relative_before=before_relative,
            value_relative_after=after_relative,
        )
        updated_overall = self._measurement_overalls.get_by_enrollment(enrollment_id=enrollment_id)
        if isinstance(updated_overall, dict):
            self._append_analytical_history_events(enrollment=enrollment, overall=updated_overall)

        return {
            "measurementId": str(updated.get("id") or ""),
            "metricId": str(updated.get("metric_id") or ""),
            "valueCurrent": float(updated.get("value_current") or 0),
            "pillarId": str(metric.get("pillar_id") or ""),
            "enrollmentId": enrollment_id,
        }

    @staticmethod
    def _resolve_metric_rule_version(metric: dict[str, Any]) -> str | None:
        scoring_rules = metric.get("scoring_rules")
        if isinstance(scoring_rules, dict):
            version = scoring_rules.get("version")
            if version is not None:
                return str(version)
        return None

    @staticmethod
    def _calculate_normalized_score(*, metric: dict[str, Any], value: Any) -> float | None:
        try:
            return float(calculate_metric_score(metric, value).normalized_score)
        except ScoreCalculationError:
            return None

    def _append_measurement_history_event(
        self,
        *,
        user: dict[str, Any],
        metric: dict[str, Any],
        measurement_before: dict[str, Any],
        measurement_after: dict[str, Any],
        value_relative_before: float | None,
        value_relative_after: float | None,
    ) -> None:
        if self._measurement_history is None:
            return

        payload = {
            "measurement_id": str(measurement_after.get("id") or ""),
            "enrollment_id": str(measurement_after.get("enrollment_id") or ""),
            "metric_id": str(measurement_after.get("metric_id") or ""),
            "actor_user_id": str(user.get("id") or "") or None,
            "actor_role": canonicalize_role(str(user.get("role") or "")) or None,
            "value_absolute_before": float(measurement_before.get("value_current") or 0),
            "value_absolute_after": float(measurement_after.get("value_current") or 0),
            "value_relative_before": value_relative_before,
            "value_relative_after": value_relative_after,
            "rule_version": self._resolve_metric_rule_version(metric),
        }
        self._measurement_history.append_event(payload)

    def _resolve_scoring_rule_version_for_metrics(self, metric_values: list[dict[str, Any]]) -> str | None:
        metrics_by_id = {str(metric.get("id") or ""): metric for metric in self._metrics.list_metrics()}
        versions: set[str] = set()
        for metric_value in metric_values:
            metric_id = str(metric_value.get("metric_id") or "")
            metric = metrics_by_id.get(metric_id)
            if not isinstance(metric, dict):
                continue
            version = self._resolve_metric_rule_version(metric)
            if version:
                versions.add(version)
        if not versions:
            return None
        return "|".join(sorted(versions))

    def _append_analytical_history_events(self, *, enrollment: dict[str, Any], overall: dict[str, Any]) -> None:
        if self._analytical_history is None:
            return

        enrollment_id = str(enrollment.get("id") or "")
        product_id = str(enrollment.get("organization_id") or "")
        protocol_id = str(overall.get("protocol_id") or "")

        metric_values = overall.get("metrics") if isinstance(overall.get("metrics"), list) else []
        pillars_payload = overall.get("pillars") if isinstance(overall.get("pillars"), list) else []
        decision_matrix = overall.get("decision_matrix") if isinstance(overall.get("decision_matrix"), dict) else {}

        scoring_rule_version = self._resolve_scoring_rule_version_for_metrics(metric_values)

        pillar_scores_payload: list[dict[str, Any]] = []
        for pillar_row in pillars_payload:
            if not isinstance(pillar_row, dict):
                continue
            pillar_id = str(pillar_row.get("pillar_id") or "")
            if not pillar_id:
                continue
            metric_average = pillar_row.get("metric_average") if isinstance(pillar_row.get("metric_average"), dict) else {}
            baseline_score = float(metric_average.get("base") or 0.0)
            current_score = float(metric_average.get("real") or 0.0)
            projected_score = float(metric_average.get("goal") or current_score)

            pillar_scores_payload.append(
                {
                    "pillar_id": pillar_id,
                    "baseline_score": baseline_score,
                    "current_score": current_score,
                    "projected_score": projected_score,
                }
            )

            self._analytical_history.append_event(
                {
                    "event_type": "radar_axis_snapshot",
                    "enrollment_id": enrollment_id,
                    "product_id": product_id,
                    "pillar_id": pillar_id,
                    "scoring_rule_version": scoring_rule_version,
                    "projection_formula_version": PROJECTION_FORMULA_VERSION,
                    "payload": {
                        "protocol_id": protocol_id,
                        "baseline_score": baseline_score,
                        "current_score": current_score,
                        "projected_score": projected_score,
                    },
                }
            )

        progress_score = float(decision_matrix.get("product_score") or 0.0)
        engagement_score = float(decision_matrix.get("engagement_score") or 0.0)
        thresholds = decision_matrix.get("thresholds") if isinstance(decision_matrix.get("thresholds"), dict) else {}
        prd_thr = float(thresholds.get("prd_thr") or PRD_THR)
        eng_thr = float(thresholds.get("eng_thr") or ENG_THR)
        quadrant = self._classify_quadrant(
            progress=progress_score,
            engagement=engagement_score,
            prd_thr=prd_thr,
            eng_thr=eng_thr,
        )

        self._analytical_history.append_event(
            {
                "event_type": "assignment_score_snapshot",
                "enrollment_id": enrollment_id,
                "product_id": product_id,
                "scoring_rule_version": scoring_rule_version,
                "projection_formula_version": PROJECTION_FORMULA_VERSION,
                "payload": {
                    "protocol_id": protocol_id,
                    "product_score": progress_score,
                    "engagement_score": engagement_score,
                    "pillar_scores": pillar_scores_payload,
                },
            }
        )

        self._analytical_history.append_event(
            {
                "event_type": "decision_matrix_snapshot",
                "enrollment_id": enrollment_id,
                "product_id": product_id,
                "scoring_rule_version": scoring_rule_version,
                "projection_formula_version": PROJECTION_FORMULA_VERSION,
                "payload": {
                    "protocol_id": protocol_id,
                    "product_score": progress_score,
                    "engagement_score": engagement_score,
                    "thresholds": {"prd_thr": prd_thr, "eng_thr": eng_thr},
                    "quadrant": quadrant,
                },
            }
        )

        self._append_product_radar_history(
            product_id=product_id,
            protocol_id=protocol_id,
            scoring_rule_version=scoring_rule_version,
        )

    def _append_product_radar_history(self, *, product_id: str, protocol_id: str, scoring_rule_version: str | None) -> None:
        if self._analytical_history is None or not product_id:
            return

        active_enrollment_ids = {
            str(row.get("id") or "")
            for row in self._enrollments.list_enrollments()
            if str(row.get("organization_id") or "") == product_id and bool(row.get("is_active", True))
        }
        if not active_enrollment_ids:
            return

        per_pillar: dict[str, dict[str, list[float]]] = {}
        for enrollment_id in active_enrollment_ids:
            overall = self._measurement_overalls.get_by_enrollment(enrollment_id)
            if not isinstance(overall, dict):
                continue
            pillars_payload = overall.get("pillars") if isinstance(overall.get("pillars"), list) else []
            for pillar_row in pillars_payload:
                if not isinstance(pillar_row, dict):
                    continue
                pillar_id = str(pillar_row.get("pillar_id") or "")
                if not pillar_id:
                    continue
                metric_average = pillar_row.get("metric_average") if isinstance(pillar_row.get("metric_average"), dict) else {}
                bucket = per_pillar.setdefault(pillar_id, {"base": [], "real": [], "goal": []})
                bucket["base"].append(float(metric_average.get("base") or 0.0))
                bucket["real"].append(float(metric_average.get("real") or 0.0))
                bucket["goal"].append(float(metric_average.get("goal") or 0.0))

        for pillar_id, bucket in per_pillar.items():
            sample_size = len(bucket["real"])
            if sample_size == 0:
                continue
            self._analytical_history.append_event(
                {
                    "event_type": "product_radar_snapshot",
                    "product_id": product_id,
                    "pillar_id": pillar_id,
                    "scoring_rule_version": scoring_rule_version,
                    "projection_formula_version": PROJECTION_FORMULA_VERSION,
                    "payload": {
                        "protocol_id": protocol_id,
                        "sample_size": sample_size,
                        "baseline_score": self._geometric_mean(bucket["base"]),
                        "current_score": self._geometric_mean(bucket["real"]),
                        "projected_score": self._geometric_mean(bucket["goal"]),
                    },
                }
            )

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
            metric = metrics_by_id.get(metric_id)
            if not metric_row or not metric:
                continue
            projected_raw = measurement.get("value_projected")
            projected_input = measurement.get("value_current") if projected_raw is None else projected_raw
            try:
                baseline_score = calculate_metric_score(metric, measurement.get("value_baseline"))
                current_score = calculate_metric_score(metric, measurement.get("value_current"))
                projected_score = calculate_metric_score(metric, projected_input)
                scoring_rules = metric.get("scoring_rules") if isinstance(metric.get("scoring_rules"), dict) else {}
                scoring = scoring_rules.get("scoring") if isinstance(scoring_rules.get("scoring"), dict) else {}
                rules = scoring.get("rules") if isinstance(scoring.get("rules"), list) else None
                has_degenerate_rules = rules is not None and len(rules) == 0

                if has_degenerate_rules and current_score.normalized_score == 0.0 and baseline_score.normalized_score == 0.0:
                    metric_row["values"] = {
                        "goal": float(projected_input or 0.0),
                        "base": float(measurement.get("value_baseline") or 0.0),
                        "real": float(measurement.get("value_current") or 0.0),
                    }
                else:
                    metric_row["values"] = {
                        "goal": float(projected_score.normalized_score),
                        "base": float(baseline_score.normalized_score),
                        "real": float(current_score.normalized_score),
                    }
            except ScoreCalculationError:
                metric_row["values"] = {
                    "goal": float(projected_input or 0.0),
                    "base": float(measurement.get("value_baseline") or 0.0),
                    "real": float(measurement.get("value_current") or 0.0),
                }

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
