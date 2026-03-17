from __future__ import annotations

from typing import Any

from app.storage.checkpoint_repository import CheckpointRepository
from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.measurement_repository import MeasurementRepository
from app.storage.metric_repository import MetricRepository
from app.storage.organization_repository import OrganizationRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.student_repository import StudentRepository


class EntityNotFoundError(Exception):
    pass


class IndicatorCargaService:
    def __init__(
        self,
        *,
        students: StudentRepository,
        organizations: OrganizationRepository,
        enrollments: EnrollmentRepository,
        metrics: MetricRepository,
        measurements: MeasurementRepository,
        checkpoints: CheckpointRepository,
        pillars: PillarRepository | None = None,
    ) -> None:
        self._students = students
        self._organizations = organizations
        self._enrollments = enrollments
        self._metrics = metrics
        self._measurements = measurements
        self._checkpoints = checkpoints
        self._pillars = pillars

    @staticmethod
    def _derive_progress(*, day: int, total_days: int, fallback_progress: float) -> float:
        if total_days > 0:
            value = day / total_days
            return max(0.0, min(1.0, round(value, 4)))
        return max(0.0, min(1.0, round(fallback_progress, 4)))

    @staticmethod
    def _derive_urgency(*, engagement: float, days_left: int) -> str:
        d45 = days_left <= 45
        if d45 and engagement <= 0.1:
            return "rescue"
        if engagement <= 0.2:
            return "critical"
        if d45 or engagement < 0.6:
            return "watch"
        return "normal"

    @staticmethod
    def _derive_risk(urgency: str) -> str:
        if urgency in {"rescue", "critical"}:
            return "high"
        if urgency == "watch":
            return "medium"
        return "low"

    @staticmethod
    def _derive_hormozi_score(*, progress: float, engagement: float) -> int:
        score = (progress * 0.4 + engagement * 0.6) * 100
        return int(max(0, min(100, round(score))))

    def _get_student_and_enrollment(self, student_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        student = self._students.get_by_id(student_id)
        if not student:
            raise EntityNotFoundError("student not found")

        enrollment = self._enrollments.get_active_by_student(student_id)
        if not enrollment:
            raise EntityNotFoundError("student enrollment not found")

        return student, enrollment

    def _build_center_summary(
        self,
        *,
        student: dict[str, Any],
        enrollment: dict[str, Any],
        organization: dict[str, Any] | None,
    ) -> dict[str, Any]:
        day = int(enrollment.get("day", 0))
        total_days = int(enrollment.get("total_days", 0))
        days_left = int(enrollment.get("days_left", 0))
        engagement = float(enrollment.get("engagement_score", 0))
        progress = self._derive_progress(
            day=day,
            total_days=total_days,
            fallback_progress=float(enrollment.get("progress_score", 0)),
        )
        urgency = self._derive_urgency(engagement=engagement, days_left=days_left)

        return {
            "id": str(student["id"]),
            "name": str(student["full_name"]),
            "programName": str((organization or {}).get("name") or "Mentoria"),
            "urgency": urgency,
            "risk": self._derive_risk(urgency),
            "daysLeft": days_left,
            "day": day,
            "totalDays": total_days,
            "engagement": engagement,
            "progress": progress,
            "d45": days_left <= 45,
            "hormoziScore": self._derive_hormozi_score(progress=progress, engagement=engagement),
            "ltv": int(enrollment.get("ltv_cents", 0)),
        }

    @staticmethod
    def _classify_quadrant(*, progress: float, engagement: float) -> str:
        if progress >= 0.6 and engagement >= 0.6:
            return "topRight"
        if progress < 0.6 and engagement >= 0.6:
            return "topLeft"
        if progress >= 0.6 and engagement < 0.6:
            return "bottomRight"
        return "bottomLeft"

    @staticmethod
    def _renewal_texts(urgency: str) -> tuple[str, str]:
        if urgency == "rescue":
            return (
                "Risco de renovacao imediato",
                "Ativar plano de resgate com contato do mentor",
            )
        if urgency == "critical":
            return (
                "Engajamento critico",
                "Reforcar rotina semanal e acompanhamento proximo",
            )
        if urgency == "watch":
            return (
                "Atencao para renovacao",
                "Acompanhar checkpoints e ajustar plano da mentoria",
            )
        return (
            "Evolucao consistente",
            "Preparar oferta de continuidade da mentoria",
        )

    @staticmethod
    def _as_pct(value: float) -> int:
        return int(max(0, min(100, round(value))))

    @staticmethod
    def _normalize_checkpoint_status(value: Any) -> str:
        status = str(value or "green").lower()
        if status in {"green", "yellow", "red"}:
            return status
        return "yellow"

    @staticmethod
    def _build_anomaly_texts(*, direction: str) -> tuple[str, str]:
        if direction == "lower_better":
            return (
                "Aumento acima do baseline no indicador de risco.",
                "Priorizar acao corretiva na rotina e reforcar acompanhamento com o mentor.",
            )
        if direction == "target_range":
            return (
                "Oscilacao fora da faixa esperada para o eixo.",
                "Ajustar plano de execucao e revisar checkpoints de curto prazo.",
            )
        return (
            "Queda de consistencia no indicador de execucao.",
            "Reforcar rotina semanal e revisar bloqueios com o mentor.",
        )

    @classmethod
    def _is_anomaly(
        cls,
        *,
        direction: str,
        baseline: float,
        current: float,
        improving_trend: Any,
    ) -> bool:
        if improving_trend is False:
            return True
        if direction == "lower_better":
            return current > baseline
        if direction == "target_range":
            return abs(current - baseline) >= 5
        return current < baseline

    def _build_anomalies(self, *, enrollment_id: str) -> list[dict[str, Any]]:
        anomalies: list[dict[str, Any]] = []
        measurements = self._measurements.list_by_enrollment(enrollment_id)
        for measurement in measurements:
            metric = self._metrics.get_by_id(str(measurement.get("metric_id")))
            if not metric:
                continue

            baseline = float(measurement.get("value_baseline", 0))
            current = float(measurement.get("value_current", 0))
            projected_raw = measurement.get("value_projected")
            projected = baseline if projected_raw is None else float(projected_raw)
            direction = str(metric.get("direction") or "higher_better")
            improving_trend = measurement.get("improving_trend")

            if not self._is_anomaly(
                direction=direction,
                baseline=baseline,
                current=current,
                improving_trend=improving_trend,
            ):
                continue

            cause, action = self._build_anomaly_texts(direction=direction)
            anomalies.append(
                {
                    "marker": str(metric.get("name") or "Indicador"),
                    "value": round(current, 2),
                    "ref": f"Baseline {round(baseline, 2)} | Projecao {round(projected, 2)}",
                    "cause": cause,
                    "action": action,
                }
            )

        return anomalies

    @staticmethod
    def _build_axis_insight(*, axis_label: str, baseline: float, current: float, projected: float) -> str:
        delta_current = round(current - baseline, 2)
        delta_projection = round(projected - current, 2)

        if delta_current < 0:
            return f"{axis_label}: abaixo do baseline. Reforcar execucao semanal e remover bloqueios."
        if delta_projection <= 0:
            return f"{axis_label}: manter consistencia para preservar o resultado atual."
        if delta_projection >= 8:
            return f"{axis_label}: alta alavanca para o proximo ciclo com ganho projetado relevante."
        return f"{axis_label}: evolucao positiva e espaco de consolidacao no proximo ciclo."

    def _build_markers(self, enrollment_id: str) -> list[dict[str, Any]]:
        markers: list[dict[str, Any]] = []
        for measurement in self._measurements.list_by_enrollment(enrollment_id):
            metric = self._metrics.get_by_id(str(measurement.get("metric_id")))
            if not metric:
                continue
            current = float(measurement.get("value_current", 0))
            target = measurement.get("value_projected")
            if target is None:
                target = measurement.get("value_baseline")
            markers.append(
                {
                    "label": str(metric.get("name", "Indicador")),
                    "value": current,
                    "target": target,
                    "pct": self._as_pct(current),
                    "improving": measurement.get("improving_trend"),
                }
            )
        return markers

    def _build_matrix_item(
        self,
        *,
        student: dict[str, Any],
        enrollment: dict[str, Any],
        organization: dict[str, Any] | None,
    ) -> dict[str, Any]:
        base = self._build_center_summary(
            student=student,
            enrollment=enrollment,
            organization=organization,
        )
        quadrant = self._classify_quadrant(
            progress=float(base["progress"]),
            engagement=float(base["engagement"]),
        )
        renewal_reason, suggestion = self._renewal_texts(str(base["urgency"]))
        return {
            "id": str(base["id"]),
            "name": str(base["name"]),
            "initials": str(student.get("initials") or ""),
            "programName": str(base["programName"]),
            "plan": str(base["programName"]),
            "progress": float(base["progress"]),
            "engagement": float(base["engagement"]),
            "daysLeft": int(base["daysLeft"]),
            "urgency": str(base["urgency"]),
            "ltv": int(base["ltv"]),
            "renewalReason": renewal_reason,
            "suggestion": suggestion,
            "markers": self._build_markers(str(enrollment["id"])),
            "quadrant": quadrant,
        }

    def list_command_center_students(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for enrollment in self._enrollments.list_enrollments():
            if not bool(enrollment.get("is_active", True)):
                continue
            student = self._students.get_by_id(str(enrollment.get("student_id")))
            if not student:
                continue
            organization = self._organizations.get_by_id(str(enrollment.get("organization_id")))
            items.append(
                self._build_center_summary(
                    student=student,
                    enrollment=enrollment,
                    organization=organization,
                )
            )
        return items

    def get_renewal_matrix(self, *, filter_mode: str = "all") -> dict[str, Any]:
        all_items: list[dict[str, Any]] = []
        for enrollment in self._enrollments.list_enrollments():
            if not bool(enrollment.get("is_active", True)):
                continue
            student = self._students.get_by_id(str(enrollment.get("student_id")))
            if not student:
                continue
            organization = self._organizations.get_by_id(str(enrollment.get("organization_id")))
            all_items.append(
                self._build_matrix_item(
                    student=student,
                    enrollment=enrollment,
                    organization=organization,
                )
            )

        total_ltv = sum(int(item["ltv"]) for item in all_items)
        critical_renewals = sum(1 for item in all_items if item["daysLeft"] <= 45 and item["quadrant"] == "topRight")
        rescue_count = sum(1 for item in all_items if item["urgency"] == "rescue")
        avg_engagement = round((sum(float(item["engagement"]) for item in all_items) / len(all_items) * 100), 2) if all_items else 0.0

        valid_filters = {"all", "topRight", "critical", "rescue"}
        normalized_filter = filter_mode if filter_mode in valid_filters else "all"
        if normalized_filter == "topRight":
            filtered = [item for item in all_items if item["quadrant"] == "topRight"]
        elif normalized_filter == "critical":
            filtered = [item for item in all_items if item["daysLeft"] <= 45 and item["quadrant"] == "topRight"]
        elif normalized_filter == "rescue":
            filtered = [item for item in all_items if item["urgency"] == "rescue"]
        else:
            filtered = all_items

        return {
            "filter": normalized_filter,
            "items": filtered,
            "kpis": {
                "totalLTV": total_ltv,
                "criticalRenewals": critical_renewals,
                "rescueCount": rescue_count,
                "avgEngagement": avg_engagement,
            },
        }

    @staticmethod
    def _avg(values: list[float]) -> float:
        if not values:
            return 0.0
        return round(sum(values) / len(values), 2)

    def get_student_radar(self, *, student_id: str) -> dict[str, Any]:
        self._get_student_and_enrollment(student_id)
        enrollment = self._enrollments.get_active_by_student(student_id)
        if not enrollment:
            raise EntityNotFoundError("student enrollment not found")

        grouped: dict[str, dict[str, Any]] = {}
        measurements = self._measurements.list_by_enrollment(str(enrollment["id"]))
        for measurement in measurements:
            metric = self._metrics.get_by_id(str(measurement["metric_id"]))
            if not metric:
                continue
            pillar_id = str(metric.get("pillar_id", ""))
            if not pillar_id:
                continue

            projected_raw = measurement.get("value_projected")
            current = float(measurement["value_current"])
            projected = current if projected_raw is None else float(projected_raw)

            bucket = grouped.setdefault(
                pillar_id,
                {"baseline": [], "current": [], "projected": []},
            )
            bucket["baseline"].append(float(measurement["value_baseline"]))
            bucket["current"].append(current)
            bucket["projected"].append(projected)

        axis_scores: list[dict[str, Any]] = []
        for pillar_id, values in grouped.items():
            pillar = self._pillars.get_by_id(pillar_id) if self._pillars else None
            metadata = (pillar or {}).get("metadata") or {}
            axis_scores.append(
                {
                    "axisKey": str((pillar or {}).get("code") or pillar_id),
                    "axisLabel": str((pillar or {}).get("name") or pillar_id),
                    "axisSub": str(metadata.get("axis_sub") or ""),
                    "baseline": self._avg(values["baseline"]),
                    "current": self._avg(values["current"]),
                    "projected": self._avg(values["projected"]),
                    "insight": "",
                    "_order": int((pillar or {}).get("order_index", 999)),
                }
            )

        axis_scores.sort(key=lambda item: int(item.get("_order", 999)))
        for axis in axis_scores:
            axis["insight"] = self._build_axis_insight(
                axis_label=str(axis.get("axisLabel") or "Eixo"),
                baseline=float(axis.get("baseline", 0)),
                current=float(axis.get("current", 0)),
                projected=float(axis.get("projected", 0)),
            )
            axis.pop("_order", None)

        return {
            "studentId": student_id,
            "axisScores": axis_scores,
            "avgBaseline": self._avg([float(axis["baseline"]) for axis in axis_scores]),
            "avgCurrent": self._avg([float(axis["current"]) for axis in axis_scores]),
            "avgProjected": self._avg([float(axis["projected"]) for axis in axis_scores]),
        }

    def get_command_center_timeline_anomalies(self, *, student_id: str) -> dict[str, Any]:
        _, enrollment = self._get_student_and_enrollment(student_id)
        checkpoints = self._checkpoints.list_by_enrollment(str(enrollment["id"]))
        checkpoints.sort(key=lambda row: int(row.get("week", 0)))

        anomalies = self._build_anomalies(enrollment_id=str(enrollment["id"]))
        anomaly_cursor = 0
        timeline: list[dict[str, Any]] = []

        for checkpoint in checkpoints:
            status = self._normalize_checkpoint_status(checkpoint.get("status"))
            anomaly = None
            if status in {"yellow", "red"} and anomaly_cursor < len(anomalies):
                anomaly = anomalies[anomaly_cursor]
                anomaly_cursor += 1

            timeline.append(
                {
                    "week": int(checkpoint.get("week", 0)),
                    "label": str(checkpoint.get("label") or f"Semana {checkpoint.get('week', 0)}"),
                    "status": status,
                    "anomaly": anomaly,
                }
            )

        if not timeline:
            urgency = self._derive_urgency(
                engagement=float(enrollment.get("engagement_score", 0)),
                days_left=int(enrollment.get("days_left", 0)),
            )
            timeline_status = "red" if urgency in {"rescue", "critical"} else "yellow" if urgency == "watch" else "green"
            timeline.append(
                {
                    "week": int(max(int(enrollment.get("day", 0)) // 7, 1)),
                    "label": "Checkpoint atual",
                    "status": timeline_status,
                    "anomaly": anomalies[0] if anomalies else None,
                }
            )

        return {
            "studentId": str(student_id),
            "timeline": timeline,
            "anomalies": anomalies,
            "summary": {
                "anomalyCount": len(anomalies),
                "hasAnomalies": len(anomalies) > 0,
                "currentWeek": int(max(int(enrollment.get("day", 0)) // 7, 1)),
                "lastWeek": int(max((entry["week"] for entry in timeline), default=0)),
            },
        }

    def load_initial_indicators(
        self,
        *,
        student_id: str,
        metric_values: list[dict[str, Any]],
        checkpoints: list[dict[str, Any]],
    ) -> dict[str, Any]:
        _, enrollment = self._get_student_and_enrollment(student_id)

        normalized_measurements: list[dict[str, Any]] = []
        for row in metric_values:
            metric_id = str(row["metric_id"])
            metric = self._metrics.get_by_id(metric_id)
            if not metric or not bool(metric.get("is_active", True)):
                raise EntityNotFoundError("metric not found")
            normalized_measurements.append(
                {
                    "metric_id": metric_id,
                    "value_baseline": row["value_baseline"],
                    "value_current": row["value_current"],
                    "value_projected": row.get("value_projected"),
                    "improving_trend": row.get("improving_trend"),
                }
            )

        normalized_checkpoints = [
            {
                "week": row["week"],
                "status": row["status"],
                "label": row.get("label"),
            }
            for row in checkpoints
        ]

        persisted_measurements = self._measurements.replace_for_enrollment(
            str(enrollment["id"]),
            normalized_measurements,
        )
        persisted_checkpoints = self._checkpoints.replace_for_enrollment(
            str(enrollment["id"]),
            normalized_checkpoints,
        )
        return {
            "student_id": student_id,
            "enrollment_id": str(enrollment["id"]),
            "measurement_count": len(persisted_measurements),
            "checkpoint_count": len(persisted_checkpoints),
        }

    def get_student_detail(self, *, student_id: str) -> dict[str, Any]:
        student, enrollment = self._get_student_and_enrollment(student_id)
        organization = self._organizations.get_by_id(str(enrollment["organization_id"]))

        measurements = self._measurements.list_by_enrollment(str(enrollment["id"]))
        checkpoints = self._checkpoints.list_by_enrollment(str(enrollment["id"]))

        metric_values: list[dict[str, Any]] = []
        for measurement in measurements:
            metric = self._metrics.get_by_id(str(measurement["metric_id"]))
            if not metric:
                continue
            metric_values.append(
                {
                    "id": str(measurement["id"]),
                    "metricLabel": str(metric["name"]),
                    "valueCurrent": measurement["value_current"],
                    "valueBaseline": measurement["value_baseline"],
                    "valueProjected": measurement.get("value_projected"),
                    "improvingTrend": measurement.get("improving_trend"),
                    "unit": metric.get("unit"),
                    "optimal": (metric.get("metadata") or {}).get("optimal"),
                }
            )

        checkpoint_values = [
            {
                "id": str(checkpoint["id"]),
                "week": checkpoint["week"],
                "status": checkpoint["status"],
                "label": checkpoint.get("label"),
            }
            for checkpoint in checkpoints
        ]

        base = self._build_center_summary(
            student=student,
            enrollment=enrollment,
            organization=organization,
        )
        return {**base, "metricValues": metric_values, "checkpoints": checkpoint_values}
