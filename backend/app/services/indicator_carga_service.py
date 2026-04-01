from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from app.storage.checkpoint_repository import CheckpointRepository
from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.measurement_repository import MeasurementRepository
from app.storage.metric_repository import MetricRepository
from app.storage.organization_repository import OrganizationRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository
from app.storage.student_repository import StudentRepository
from app.storage.measurement_overall_repository import MeasurementOverallRepository


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
        protocols: ProtocolRepository | None = None,
        measurement_overalls: MeasurementOverallRepository | None = None,
    ) -> None:
        self._students = students
        self._organizations = organizations
        self._enrollments = enrollments
        self._metrics = metrics
        self._measurements = measurements
        self._checkpoints = checkpoints
        self._pillars = pillars
        self._protocols = protocols
        self._measurement_overalls = measurement_overalls
        self._students_by_id_cache: dict[str, dict[str, Any]] | None = None
        self._organizations_by_id_cache: dict[str, dict[str, Any]] | None = None
        self._metrics_by_id_cache: dict[str, dict[str, Any]] | None = None
        self._pillars_by_id_cache: dict[str, dict[str, Any]] | None = None
        self._protocols_by_id_cache: dict[str, dict[str, Any]] | None = None
        self._protocol_by_org_id_cache: dict[str, dict[str, Any]] | None = None
        self._measurements_by_enrollment_cache: dict[str, list[dict[str, Any]]] | None = None
        self._measurement_overalls_by_enrollment_cache: dict[str, dict[str, Any]] | None = None

    def _students_by_id(self) -> dict[str, dict[str, Any]]:
        if self._students_by_id_cache is None:
            self._students_by_id_cache = {
                str(student.get("id")): student
                for student in self._students.list_students()
                if student.get("id")
            }
        return self._students_by_id_cache

    def _organizations_by_id(self) -> dict[str, dict[str, Any]]:
        if self._organizations_by_id_cache is None:
            self._organizations_by_id_cache = {
                str(organization.get("id")): organization
                for organization in self._organizations.list_organizations()
                if organization.get("id")
            }
        return self._organizations_by_id_cache

    def _metrics_by_id(self) -> dict[str, dict[str, Any]]:
        if self._metrics_by_id_cache is None:
            self._metrics_by_id_cache = {
                str(metric.get("id")): metric
                for metric in self._metrics.list_metrics()
                if metric.get("id")
            }
        return self._metrics_by_id_cache

    def _pillars_by_id(self) -> dict[str, dict[str, Any]]:
        if self._pillars_by_id_cache is None:
            if not self._pillars:
                self._pillars_by_id_cache = {}
            else:
                self._pillars_by_id_cache = {
                    str(pillar.get("id")): pillar
                    for pillar in self._pillars.list_pillars()
                    if pillar.get("id")
                }
        return self._pillars_by_id_cache

    def _measurements_by_enrollment(self) -> dict[str, list[dict[str, Any]]]:
        if self._measurements_by_enrollment_cache is None:
            grouped: dict[str, list[dict[str, Any]]] = {}
            for measurement in self._measurements.list_measurements():
                enrollment_id = str(measurement.get("enrollment_id") or "")
                if not enrollment_id:
                    continue
                grouped.setdefault(enrollment_id, []).append(measurement)
            self._measurements_by_enrollment_cache = grouped
        return self._measurements_by_enrollment_cache

    def _protocols_by_id(self) -> dict[str, dict[str, Any]]:
        if self._protocols_by_id_cache is None:
            if not self._protocols:
                self._protocols_by_id_cache = {}
            else:
                self._protocols_by_id_cache = {
                    str(protocol.get("id")): protocol
                    for protocol in self._protocols.list_protocols()
                    if protocol.get("id")
                }
        return self._protocols_by_id_cache

    def _protocol_by_org_id(self) -> dict[str, dict[str, Any]]:
        if self._protocol_by_org_id_cache is None:
            if not self._protocols:
                self._protocol_by_org_id_cache = {}
            else:
                grouped: dict[str, dict[str, Any]] = {}
                for protocol in self._protocols.list_protocols():
                    organization_id = str(protocol.get("organization_id") or "")
                    if not organization_id or organization_id in grouped:
                        continue
                    grouped[organization_id] = protocol
                self._protocol_by_org_id_cache = grouped
        return self._protocol_by_org_id_cache

    def _measurement_overalls_by_enrollment(self) -> dict[str, dict[str, Any]]:
        if self._measurement_overalls_by_enrollment_cache is None:
            if not self._measurement_overalls:
                self._measurement_overalls_by_enrollment_cache = {}
            else:
                self._measurement_overalls_by_enrollment_cache = {
                    str(row.get("enrollment_id")): row
                    for row in self._measurement_overalls.list_all()
                    if row.get("enrollment_id")
                }
        return self._measurement_overalls_by_enrollment_cache

    def _get_overall_by_enrollment(self, enrollment_id: str) -> dict[str, Any] | None:
        return self._measurement_overalls_by_enrollment().get(enrollment_id)

    @staticmethod
    def _parse_date(value: Any) -> date | None:
        if value is None:
            return None
        raw = str(value).strip()
        if not raw:
            return None
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            return None

    @classmethod
    def _derive_cycle_window(cls, *, student: dict[str, Any], enrollment: dict[str, Any]) -> tuple[int, int, int]:
        start_date = cls._parse_date(student.get("start_enrollment_date"))
        end_date = cls._parse_date(student.get("end_enrollment_date"))

        if start_date and end_date and end_date > start_date:
            today = datetime.now(timezone.utc).date()
            total_days = max((end_date - start_date).days, 1)

            if today <= start_date:
                return 0, total_days, total_days
            if today >= end_date:
                return total_days, total_days, 0

            day = max((today - start_date).days, 0)
            days_left = max((end_date - today).days, 0)
            return min(day, total_days), total_days, days_left

        return (
            int(enrollment.get("day", 0)),
            int(enrollment.get("total_days", 0)),
            int(enrollment.get("days_left", 0)),
        )

    def _iter_active_enrollments(self, *, mentor_id: str | None = None) -> list[dict[str, Any]]:
        enrollments = self._enrollments.list_by_mentor(mentor_id) if mentor_id else self._enrollments.list_enrollments()
        return [row for row in enrollments if bool(row.get("is_active", True))]

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

    def _get_student_and_enrollment(self, student_id: str, *, mentor_id: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
        student = self._students_by_id().get(student_id)
        if not student:
            raise EntityNotFoundError("student not found")

        enrollment = next(
            (
                row
                for row in self._enrollments.list_by_student(student_id)
                if bool(row.get("is_active", True))
                and (mentor_id is None or str(row.get("mentor_id") or "") == mentor_id)
            ),
            None,
        )
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
        day, total_days, days_left = self._derive_cycle_window(student=student, enrollment=enrollment)
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
    def _classify_quadrant(*, progress: float, engagement: float, prd_thr: float = 0.7, eng_thr: float = 0.7) -> str:
        if progress >= prd_thr and engagement >= eng_thr:
            return "topRight"
        if progress < 0.3 and engagement < 0.3:
            return "bottomLeft"
        if progress < prd_thr and engagement >= eng_thr:
            return "topLeft"
        if progress >= prd_thr and engagement < eng_thr:
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
        measurements = self._measurements_by_enrollment().get(enrollment_id, [])
        metrics_by_id = self._metrics_by_id()
        for measurement in measurements:
            metric = metrics_by_id.get(str(measurement.get("metric_id")))
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
        metrics_by_id = self._metrics_by_id()
        for measurement in self._measurements_by_enrollment().get(enrollment_id, []):
            metric = metrics_by_id.get(str(measurement.get("metric_id")))
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
        overall = self._get_overall_by_enrollment(str(enrollment["id"]))
        decision_matrix = (overall or {}).get("decision_matrix") if overall else None
        if isinstance(decision_matrix, dict):
            thresholds = decision_matrix.get("thresholds") if isinstance(decision_matrix.get("thresholds"), dict) else {}
            prd_thr = float(thresholds.get("prd_thr", 0.7))
            eng_thr = float(thresholds.get("eng_thr", 0.7))
            progress_value = float(decision_matrix.get("product_score", base["progress"]))
            engagement_value = float(decision_matrix.get("engagement_score", base["engagement"]))
        else:
            prd_thr = 0.7
            eng_thr = 0.7
            progress_value = float(base["progress"])
            engagement_value = float(base["engagement"])
        quadrant = self._classify_quadrant(
            progress=progress_value,
            engagement=engagement_value,
            prd_thr=prd_thr,
            eng_thr=eng_thr,
        )
        renewal_reason, suggestion = self._renewal_texts(str(base["urgency"]))
        return {
            "id": str(base["id"]),
            "name": str(base["name"]),
            "initials": str(student.get("initials") or ""),
            "programName": str(base["programName"]),
            "plan": str(base["programName"]),
            "progress": progress_value,
            "engagement": engagement_value,
            "daysLeft": int(base["daysLeft"]),
            "urgency": str(base["urgency"]),
            "ltv": int(base["ltv"]),
            "renewalReason": renewal_reason,
            "suggestion": suggestion,
            "markers": self._build_markers(str(enrollment["id"])),
            "quadrant": quadrant,
        }

    def list_command_center_students(self, *, mentor_id: str | None = None) -> dict[str, Any]:
        ranked_items: list[tuple[dict[str, Any], float]] = []
        protocol_ids_seen: list[str] = []
        students_by_id = self._students_by_id()
        organizations_by_id = self._organizations_by_id()
        for enrollment in self._iter_active_enrollments(mentor_id=mentor_id):
            student = students_by_id.get(str(enrollment.get("student_id")))
            if not student:
                continue
            organization = organizations_by_id.get(str(enrollment.get("organization_id")))
            overall = self._get_overall_by_enrollment(str(enrollment.get("id")))
            protocol_id = str((overall or {}).get("protocol_id") or "")
            if not protocol_id:
                protocol = self._protocol_by_org_id().get(str(enrollment.get("organization_id") or ""))
                protocol_id = str((protocol or {}).get("id") or "")
            if protocol_id:
                protocol_ids_seen.append(protocol_id)
            enrollment_for_summary = dict(enrollment)
            performance_score = 0.0

            decision_matrix = (overall or {}).get("decision_matrix") if overall else None
            if isinstance(decision_matrix, dict):
                enrollment_for_summary["progress_score"] = float(
                    decision_matrix.get("product_score", enrollment.get("progress_score", 0.0))
                )
                enrollment_for_summary["engagement_score"] = float(
                    decision_matrix.get("engagement_score", enrollment.get("engagement_score", 0.0))
                )

            pillars = (overall or {}).get("pillars") if overall else None
            if isinstance(pillars, list) and pillars:
                pillar_values: list[float] = []
                for pillar_row in pillars:
                    if not isinstance(pillar_row, dict):
                        continue
                    metric_average = pillar_row.get("metric_average")
                    if not isinstance(metric_average, dict):
                        continue
                    pillar_values.append(float(metric_average.get("real", 0.0)))
                if pillar_values:
                    performance_score = sum(pillar_values) / len(pillar_values)
            elif isinstance(decision_matrix, dict):
                performance_score = (
                    float(decision_matrix.get("product_score", 0.0))
                    + float(decision_matrix.get("engagement_score", 0.0))
                ) / 2

            summary = self._build_center_summary(
                student=student,
                enrollment=enrollment_for_summary,
                organization=organization,
            )
            if performance_score <= 0.0:
                performance_score = float(summary.get("hormoziScore", 0)) / 100
            ranked_items.append((summary, performance_score))

        context_protocol_id = protocol_ids_seen[0] if protocol_ids_seen else ""
        context_protocol = self._protocols_by_id().get(context_protocol_id)
        context = {
            "protocolId": context_protocol_id,
            "protocolName": str((context_protocol or {}).get("name") or ""),
        }

        ranked_items.sort(
            key=lambda row: (
                -row[1],
                -int(row[0].get("hormoziScore", 0)),
                str(row[0].get("name", "")),
            )
        )

        if len(ranked_items) <= 20:
            items = [item for item, _ in ranked_items]
            return {
                "items": items,
                "topItems": items,
                "bottomItems": [],
                "totalStudents": len(ranked_items),
                "rankingMode": "full",
                "context": context,
            }

        top = ranked_items[:10]
        bottom = sorted(
            ranked_items,
            key=lambda row: (
                row[1],
                int(row[0].get("hormoziScore", 0)),
                str(row[0].get("name", "")),
            ),
        )[:10]

        top_items = [item for item, _ in top]
        bottom_items = [item for item, _ in bottom]
        return {
            "items": top_items + bottom_items,
            "topItems": top_items,
            "bottomItems": bottom_items,
            "totalStudents": len(ranked_items),
            "rankingMode": "top_bottom",
            "context": context,
        }

    def get_renewal_matrix(self, *, filter_mode: str = "all", mentor_id: str | None = None) -> dict[str, Any]:
        all_items: list[dict[str, Any]] = []
        protocol_ids_seen: list[str] = []
        students_by_id = self._students_by_id()
        organizations_by_id = self._organizations_by_id()
        for enrollment in self._iter_active_enrollments(mentor_id=mentor_id):
            student = students_by_id.get(str(enrollment.get("student_id")))
            if not student:
                continue
            organization = organizations_by_id.get(str(enrollment.get("organization_id")))
            overall = self._get_overall_by_enrollment(str(enrollment.get("id") or ""))
            protocol_id = str((overall or {}).get("protocol_id") or "")
            if not protocol_id:
                protocol = self._protocol_by_org_id().get(str(enrollment.get("organization_id") or ""))
                protocol_id = str((protocol or {}).get("id") or "")
            if protocol_id:
                protocol_ids_seen.append(protocol_id)
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

        context_protocol_id = protocol_ids_seen[0] if protocol_ids_seen else ""
        context_protocol = self._protocols_by_id().get(context_protocol_id)

        return {
            "filter": normalized_filter,
            "items": filtered,
            "kpis": {
                "totalLTV": total_ltv,
                "criticalRenewals": critical_renewals,
                "rescueCount": rescue_count,
                "avgEngagement": avg_engagement,
            },
            "context": {
                "protocolId": context_protocol_id,
                "protocolName": str((context_protocol or {}).get("name") or (filtered[0].get("programName") if filtered else "")),
            },
        }

    @staticmethod
    def _avg(values: list[float]) -> float:
        if not values:
            return 0.0
        return round(sum(values) / len(values), 2)

    def get_student_radar(self, *, student_id: str, mentor_id: str | None = None) -> dict[str, Any]:
        _, enrollment = self._get_student_and_enrollment(student_id, mentor_id=mentor_id)

        overall = self._get_overall_by_enrollment(str(enrollment["id"]))
        protocol_id = str((overall or {}).get("protocol_id") or "")
        if not protocol_id:
            protocol = self._protocol_by_org_id().get(str(enrollment.get("organization_id") or ""))
            protocol_id = str((protocol or {}).get("id") or "")
        context_protocol = self._protocols_by_id().get(protocol_id)
        context = {
            "protocolId": protocol_id,
            "protocolName": str((context_protocol or {}).get("name") or ""),
        }

        if overall and isinstance(overall.get("pillars"), list):
            axis_scores: list[dict[str, Any]] = []
            pillars_by_id = self._pillars_by_id()
            for pillar_row in overall.get("pillars", []):
                pillar_id = str(pillar_row.get("pillar_id") or "")
                if not pillar_id:
                    continue
                pillar = pillars_by_id.get(pillar_id)
                values = pillar_row.get("metric_average") if isinstance(pillar_row.get("metric_average"), dict) else {}
                baseline = float(values.get("base", 0.0))
                current = float(values.get("real", 0.0))
                projected = float(values.get("goal", current))
                axis_scores.append(
                    {
                        "axisKey": str((pillar or {}).get("code") or pillar_id),
                        "axisLabel": str((pillar or {}).get("name") or pillar_id),
                        "axisSub": str((pillar or {}).get("axis_sub") or ""),
                        "baseline": baseline,
                        "current": current,
                        "projected": projected,
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
                "context": context,
            }

        grouped: dict[str, dict[str, Any]] = {}
        measurements = self._measurements_by_enrollment().get(str(enrollment["id"]), [])
        metrics_by_id = self._metrics_by_id()
        for measurement in measurements:
            metric = metrics_by_id.get(str(measurement["metric_id"]))
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
        pillars_by_id = self._pillars_by_id()
        for pillar_id, values in grouped.items():
            pillar = pillars_by_id.get(pillar_id)
            axis_scores.append(
                {
                    "axisKey": str((pillar or {}).get("code") or pillar_id),
                    "axisLabel": str((pillar or {}).get("name") or pillar_id),
                    "axisSub": str((pillar or {}).get("axis_sub") or ""),
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
            "context": context,
        }

    def get_command_center_timeline_anomalies(self, *, student_id: str, mentor_id: str | None = None) -> dict[str, Any]:
        _, enrollment = self._get_student_and_enrollment(student_id, mentor_id=mentor_id)
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
        metrics_by_id = self._metrics_by_id()
        for row in metric_values:
            metric_id = str(row["metric_id"])
            metric = metrics_by_id.get(metric_id)
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

    def get_student_detail(self, *, student_id: str, mentor_id: str | None = None) -> dict[str, Any]:
        student, enrollment = self._get_student_and_enrollment(student_id, mentor_id=mentor_id)
        organization = self._organizations_by_id().get(str(enrollment["organization_id"]))

        measurements = self._measurements_by_enrollment().get(str(enrollment["id"]), [])
        checkpoints = self._checkpoints.list_by_enrollment(str(enrollment["id"]))

        metric_values: list[dict[str, Any]] = []
        metrics_by_id = self._metrics_by_id()
        for measurement in measurements:
            metric = metrics_by_id.get(str(measurement["metric_id"]))
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
                    # If 'optimal' is needed, add as a top-level field in metric and use metric.get("optimal")
                    # "optimal": metric.get("optimal"),
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
