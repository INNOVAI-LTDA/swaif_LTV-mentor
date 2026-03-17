from __future__ import annotations

from collections.abc import Iterable
from typing import Any


DEMO_CLIENT_NAME = "Grupo Acelerador M\u00e9dico"
DEMO_PRODUCT_NAME = "Mentoria Acelerador M\u00e9dico"
DEMO_MENTOR_NAME = "Dr. Jos\u00e9 Netto"
DEMO_MENTOR_EMAIL = "mentor@swaif.local"


PILLAR_DEFINITIONS: list[dict[str, Any]] = [
    {
        "id": "pillar_positioning",
        "code": "posicionamento",
        "name": "Posicionamento de Autoridade",
        "axisSub": "Clareza de nicho, proposta e percepcao premium.",
        "order": 1,
        "metrics": [
            {"id": "metric_authority", "name": "Autoridade percebida", "unit": "pts", "optimal": "80+", "baseline": 56, "weight": 1.1},
            {"id": "metric_offer_clarity", "name": "Clareza da oferta", "unit": "pts", "optimal": "82+", "baseline": 54, "weight": 0.9},
            {"id": "metric_ticket_plan", "name": "Ticket medio planejado", "unit": "pts", "optimal": "78+", "baseline": 52, "weight": 0.8},
        ],
    },
    {
        "id": "pillar_conversion",
        "code": "conversao",
        "name": "Conversao Comercial",
        "axisSub": "Diagnostico, fechamento premium e ritmo comercial.",
        "order": 2,
        "metrics": [
            {"id": "metric_diagnostic_conversion", "name": "Conversao do diagnostico", "unit": "%", "optimal": "35%+", "baseline": 51, "weight": 1.0},
            {"id": "metric_premium_close", "name": "Fechamento premium", "unit": "%", "optimal": "25%+", "baseline": 47, "weight": 1.2},
        ],
    },
    {
        "id": "pillar_operation",
        "code": "operacao",
        "name": "Operacao de Agenda",
        "axisSub": "Rotina, comparecimento e previsibilidade semanal.",
        "order": 3,
        "metrics": [
            {"id": "metric_schedule_fill", "name": "Ocupacao da agenda ideal", "unit": "%", "optimal": "85%+", "baseline": 58, "weight": 0.9},
            {"id": "metric_show_rate", "name": "Comparecimento dos pacientes", "unit": "%", "optimal": "90%+", "baseline": 63, "weight": 0.7},
        ],
    },
    {
        "id": "pillar_experience",
        "code": "experiencia",
        "name": "Experiencia e Prova",
        "axisSub": "Percepcao do paciente, prova social e consolidacao do valor.",
        "order": 4,
        "metrics": [
            {"id": "metric_nps", "name": "NPS dos pacientes", "unit": "pts", "optimal": "75+", "baseline": 61, "weight": 0.8},
            {"id": "metric_testimonials", "name": "Depoimentos convertidos", "unit": "pts", "optimal": "70+", "baseline": 46, "weight": 0.7},
        ],
    },
    {
        "id": "pillar_scale",
        "code": "escala",
        "name": "Escala e Recorrencia",
        "axisSub": "Receita previsivel, recorrencia e ampliacao da base premium.",
        "order": 5,
        "metrics": [
            {"id": "metric_revenue_predictability", "name": "Receita previsivel", "unit": "pts", "optimal": "80+", "baseline": 49, "weight": 1.0},
            {"id": "metric_retention_base", "name": "Renovacoes da base", "unit": "%", "optimal": "70%+", "baseline": 53, "weight": 1.1},
            {"id": "metric_upsell", "name": "Upsell consultivo", "unit": "pts", "optimal": "68+", "baseline": 44, "weight": 1.2},
        ],
    },
]


STUDENT_DEFINITIONS: list[dict[str, Any]] = [
    {"id": "demo_student_01", "name": "Ana Paula Costa", "progress": 0.82, "engagement": 0.84, "day": 118, "total_days": 180, "days_left": 62, "ltv": 2800000},
    {"id": "demo_student_02", "name": "Bruno Nogueira", "progress": 0.76, "engagement": 0.68, "day": 142, "total_days": 180, "days_left": 38, "ltv": 2450000},
    {"id": "demo_student_03", "name": "Camila Rezende", "progress": 0.64, "engagement": 0.74, "day": 159, "total_days": 180, "days_left": 21, "ltv": 3100000},
    {"id": "demo_student_04", "name": "Diego Pires", "progress": 0.41, "engagement": 0.79, "day": 127, "total_days": 180, "days_left": 53, "ltv": 1980000},
    {"id": "demo_student_05", "name": "Elisa Moura", "progress": 0.28, "engagement": 0.66, "day": 146, "total_days": 180, "days_left": 34, "ltv": 1760000},
    {"id": "demo_student_06", "name": "Fabio Lessa", "progress": 0.72, "engagement": 0.44, "day": 122, "total_days": 180, "days_left": 58, "ltv": 2240000},
    {"id": "demo_student_07", "name": "Gabriela Torres", "progress": 0.67, "engagement": 0.31, "day": 153, "total_days": 180, "days_left": 27, "ltv": 2070000},
    {"id": "demo_student_08", "name": "Helena Martins", "progress": 0.33, "engagement": 0.17, "day": 139, "total_days": 180, "days_left": 41, "ltv": 1650000},
    {"id": "demo_student_09", "name": "Igor Freitas", "progress": 0.22, "engagement": 0.08, "day": 161, "total_days": 180, "days_left": 19, "ltv": 1430000},
    {"id": "demo_student_10", "name": "Juliana Prado", "progress": 0.51, "engagement": 0.26, "day": 108, "total_days": 180, "days_left": 72, "ltv": 1910000},
]


class EntityNotFoundError(Exception):
    pass


def _clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return round(max(minimum, min(maximum, value)), 2)


def _avg(values: Iterable[float]) -> float:
    values_list = list(values)
    if not values_list:
        return 0.0
    return round(sum(values_list) / len(values_list), 2)


def _to_initials(name: str) -> str:
    parts = [part[:1] for part in name.split() if part]
    return "".join(parts[:2]).upper()


class MentorDemoService:
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
                "Acionar plano de resgate com conversa consultiva nas proximas 24h.",
            )
        if urgency == "critical":
            return (
                "Engajamento critico",
                "Reforcar rotina e remover gargalos de execucao com o mentorado.",
            )
        if urgency == "watch":
            return (
                "Atencao para renovacao",
                "Acompanhar checkpoints e aumentar a consistencia semanal.",
            )
        return (
            "Evolucao consistente",
            "Preparar narrativa de continuidade e ampliacao do contrato.",
        )

    @staticmethod
    def _checkpoint_statuses(urgency: str) -> list[str]:
        if urgency == "rescue":
            return ["red", "red", "yellow", "red"]
        if urgency == "critical":
            return ["yellow", "red", "yellow", "red"]
        if urgency == "watch":
            return ["green", "yellow", "green", "yellow"]
        return ["green", "green", "green", "green"]

    @staticmethod
    def _build_anomalies(student: dict[str, Any]) -> list[dict[str, Any]]:
        urgency = str(student["urgency"])
        if urgency == "normal":
            return []
        if urgency == "watch":
            return [
                {
                    "marker": "Ocupacao da agenda ideal",
                    "value": "61.0",
                    "ref": "Baseline 68.0 | Projecao 74.0",
                    "cause": "Ritmo semanal abaixo do necessario para consolidar o valor percebido.",
                    "action": "Revisar cadencia de oferta e follow-up da semana com o mentorado.",
                }
            ]
        if urgency == "critical":
            return [
                {
                    "marker": "Fechamento premium",
                    "value": "32.0",
                    "ref": "Baseline 46.0 | Projecao 39.0",
                    "cause": "Conversao abaixo do necessario para sustentar a narrativa de renovacao.",
                    "action": "Ajustar roteiro comercial e revisar prova de valor com urgencia.",
                },
                {
                    "marker": "Receita previsivel",
                    "value": "37.0",
                    "ref": "Baseline 49.0 | Projecao 43.0",
                    "cause": "Base recorrente ainda fragilizada para o ciclo atual.",
                    "action": "Ativar plano de recorrencia e revisao de carteira nos proximos 7 dias.",
                },
            ]
        return [
            {
                "marker": "Comparecimento dos pacientes",
                "value": "48.0",
                "ref": "Baseline 63.0 | Projecao 55.0",
                "cause": "A aderencia operacional caiu abaixo do patamar minimo da jornada.",
                "action": "Intervir com resgate consultivo e redefinir rotina de confirmacao.",
            },
            {
                "marker": "Renovacoes da base",
                "value": "29.0",
                "ref": "Baseline 53.0 | Projecao 35.0",
                "cause": "Baixa consistencia na retencao da carteira premium.",
                "action": "Montar plano de retomada e monitorar o aluno em janela curta.",
            },
        ]

    def _metric_values(self, student_index: int, student: dict[str, Any]) -> list[dict[str, Any]]:
        values: list[dict[str, Any]] = []
        progress = float(student["progress"])
        engagement = float(student["engagement"])
        urgency = str(student["urgency"])
        mood_shift = ((student_index % 3) - 1) * 2.5
        urgency_penalty = {"normal": 0.0, "watch": 4.0, "critical": 9.0, "rescue": 13.0}[urgency]

        for pillar in PILLAR_DEFINITIONS:
            for metric_index, metric in enumerate(pillar["metrics"]):
                baseline = _clamp(float(metric["baseline"]) + mood_shift + (metric_index * 0.7), 25, 88)
                current = _clamp(
                    baseline
                    + ((progress - 0.5) * 24)
                    + ((engagement - 0.5) * 28 * float(metric["weight"]))
                    - urgency_penalty
                    + (pillar["order"] * 0.4),
                    12,
                    97,
                )
                projected = _clamp(
                    current + max(1.5, (engagement * 9) - (urgency_penalty / 4) + (progress * 3)),
                    15,
                    99,
                )
                values.append(
                    {
                        "id": f"{student['id']}_{metric['id']}",
                        "metricId": metric["id"],
                        "pillarId": pillar["id"],
                        "metricLabel": metric["name"],
                        "valueBaseline": baseline,
                        "valueCurrent": current,
                        "valueProjected": projected,
                        "improvingTrend": projected >= current,
                        "unit": metric["unit"],
                        "optimal": metric["optimal"],
                    }
                )

        return values

    def _build_student(self, student_index: int, row: dict[str, Any]) -> dict[str, Any]:
        progress = float(row["progress"])
        engagement = float(row["engagement"])
        days_left = int(row["days_left"])
        urgency = self._derive_urgency(engagement=engagement, days_left=days_left)
        metric_values = self._metric_values(student_index, {**row, "urgency": urgency})
        checkpoints_status = self._checkpoint_statuses(urgency)
        checkpoints = [
            {
                "id": f"{row['id']}_checkpoint_{index + 1}",
                "week": week,
                "status": checkpoints_status[index],
                "label": label,
            }
            for index, (week, label) in enumerate(
                [(2, "Onboarding"), (5, "Ajuste de proposta"), (9, "Aceleracao"), (13, "Renovacao")]
            )
        ]

        anomalies = self._build_anomalies(
            {
                "urgency": urgency,
            }
        )
        timeline: list[dict[str, Any]] = []
        anomaly_index = 0
        for checkpoint in checkpoints:
            anomaly = None
            if checkpoint["status"] in {"yellow", "red"} and anomaly_index < len(anomalies):
                anomaly = anomalies[anomaly_index]
                anomaly_index += 1
            timeline.append({**checkpoint, "anomaly": anomaly})

        axis_scores: list[dict[str, Any]] = []
        for pillar in PILLAR_DEFINITIONS:
            pillar_metrics = [metric for metric in metric_values if metric["pillarId"] == pillar["id"]]
            baseline = _avg([float(metric["valueBaseline"]) for metric in pillar_metrics])
            current = _avg([float(metric["valueCurrent"]) for metric in pillar_metrics])
            projected = _avg([float(metric["valueProjected"]) for metric in pillar_metrics])
            axis_scores.append(
                {
                    "axisKey": str(pillar["code"]),
                    "axisLabel": str(pillar["name"]),
                    "axisSub": str(pillar["axisSub"]),
                    "baseline": baseline,
                    "current": current,
                    "projected": projected,
                    "insight": self._build_axis_insight(
                        axis_label=str(pillar["name"]),
                        baseline=baseline,
                        current=current,
                        projected=projected,
                    ),
                }
            )

        renewal_reason, suggestion = self._renewal_texts(urgency)
        markers = [
            {
                "label": metric["metricLabel"],
                "value": metric["valueCurrent"],
                "target": metric["valueProjected"],
                "pct": int(_clamp(float(metric["valueCurrent"]))),
                "improving": metric["improvingTrend"],
            }
            for metric in metric_values[:3]
        ]

        return {
            "id": row["id"],
            "name": row["name"],
            "initials": _to_initials(str(row["name"])),
            "programName": DEMO_PRODUCT_NAME,
            "mentorName": DEMO_MENTOR_NAME,
            "clientName": DEMO_CLIENT_NAME,
            "urgency": urgency,
            "risk": self._derive_risk(urgency),
            "daysLeft": days_left,
            "day": int(row["day"]),
            "totalDays": int(row["total_days"]),
            "engagement": engagement,
            "progress": progress,
            "d45": days_left <= 45,
            "hormoziScore": int(round((progress * 0.4 + engagement * 0.6) * 100)),
            "ltv": int(row["ltv"]),
            "quadrant": self._classify_quadrant(progress=progress, engagement=engagement),
            "renewalReason": renewal_reason,
            "suggestion": suggestion,
            "markers": markers,
            "metricValues": metric_values,
            "checkpoints": checkpoints,
            "timeline": timeline,
            "anomalies": anomalies,
            "axisScores": axis_scores,
        }

    @staticmethod
    def _build_axis_insight(*, axis_label: str, baseline: float, current: float, projected: float) -> str:
        delta_current = round(current - baseline, 1)
        delta_projection = round(projected - current, 1)
        if delta_current < 0:
            return f"{axis_label}: abaixo do baseline. Reforcar execucao semanal e clareza de plano."
        if delta_projection >= 8:
            return f"{axis_label}: eixo com boa alavanca de ganho para o proximo ciclo."
        if delta_projection <= 2:
            return f"{axis_label}: manter consistencia para preservar o resultado atual."
        return f"{axis_label}: evolucao positiva com espaco real de consolidacao."

    def _dataset(self) -> dict[str, Any]:
        students = [self._build_student(index, row) for index, row in enumerate(STUDENT_DEFINITIONS)]
        return {
            "client": {"name": DEMO_CLIENT_NAME},
            "product": {"name": DEMO_PRODUCT_NAME},
            "mentor": {"name": DEMO_MENTOR_NAME, "email": DEMO_MENTOR_EMAIL},
            "pillars": [
                {
                    "id": pillar["id"],
                    "code": pillar["code"],
                    "name": pillar["name"],
                    "axisSub": pillar["axisSub"],
                    "order": pillar["order"],
                    "metricCount": len(pillar["metrics"]),
                }
                for pillar in PILLAR_DEFINITIONS
            ],
            "students": students,
        }

    def _get_student(self, student_id: str) -> dict[str, Any]:
        for student in self._dataset()["students"]:
            if student["id"] == student_id:
                return student
        raise EntityNotFoundError("student not found")

    def list_command_center_students(self) -> list[dict[str, Any]]:
        students = self._dataset()["students"]
        items = [
            {
                "id": student["id"],
                "name": student["name"],
                "initials": student["initials"],
                "programName": student["programName"],
                "urgency": student["urgency"],
                "risk": student["risk"],
                "daysLeft": student["daysLeft"],
                "day": student["day"],
                "totalDays": student["totalDays"],
                "engagement": student["engagement"],
                "progress": student["progress"],
                "d45": student["d45"],
                "hormoziScore": student["hormoziScore"],
                "ltv": student["ltv"],
            }
            for student in students
        ]
        return sorted(items, key=lambda item: (item["daysLeft"], item["name"]))

    def get_student_detail(self, *, student_id: str) -> dict[str, Any]:
        student = self._get_student(student_id)
        return {
            "id": student["id"],
            "name": student["name"],
            "initials": student["initials"],
            "programName": student["programName"],
            "urgency": student["urgency"],
            "risk": student["risk"],
            "daysLeft": student["daysLeft"],
            "day": student["day"],
            "totalDays": student["totalDays"],
            "engagement": student["engagement"],
            "progress": student["progress"],
            "d45": student["d45"],
            "hormoziScore": student["hormoziScore"],
            "ltv": student["ltv"],
            "metricValues": student["metricValues"],
            "checkpoints": student["checkpoints"],
        }

    def get_command_center_timeline_anomalies(self, *, student_id: str) -> dict[str, Any]:
        student = self._get_student(student_id)
        return {
            "studentId": student["id"],
            "timeline": student["timeline"],
            "anomalies": student["anomalies"],
            "summary": {
                "anomalyCount": len(student["anomalies"]),
                "hasAnomalies": len(student["anomalies"]) > 0,
                "currentWeek": int(max(student["day"] // 7, 1)),
                "lastWeek": int(max((entry["week"] for entry in student["timeline"]), default=0)),
            },
        }

    def get_student_radar(self, *, student_id: str) -> dict[str, Any]:
        student = self._get_student(student_id)
        axis_scores = student["axisScores"]
        return {
            "studentId": student["id"],
            "axisScores": axis_scores,
            "avgBaseline": _avg([float(axis["baseline"]) for axis in axis_scores]),
            "avgCurrent": _avg([float(axis["current"]) for axis in axis_scores]),
            "avgProjected": _avg([float(axis["projected"]) for axis in axis_scores]),
        }

    def get_renewal_matrix(self, *, filter_mode: str = "all") -> dict[str, Any]:
        students = self._dataset()["students"]
        items = [
            {
                "id": student["id"],
                "name": student["name"],
                "initials": student["initials"],
                "programName": student["programName"],
                "plan": student["programName"],
                "progress": student["progress"],
                "engagement": student["engagement"],
                "daysLeft": student["daysLeft"],
                "urgency": student["urgency"],
                "ltv": student["ltv"],
                "renewalReason": student["renewalReason"],
                "suggestion": student["suggestion"],
                "markers": student["markers"],
                "quadrant": student["quadrant"],
            }
            for student in students
        ]

        valid_filters = {"all", "topRight", "critical", "rescue"}
        safe_filter = filter_mode if filter_mode in valid_filters else "all"
        if safe_filter == "topRight":
            filtered = [item for item in items if item["quadrant"] == "topRight"]
        elif safe_filter == "critical":
            filtered = [item for item in items if item["daysLeft"] <= 45 and item["quadrant"] == "topRight"]
        elif safe_filter == "rescue":
            filtered = [item for item in items if item["urgency"] == "rescue"]
        else:
            filtered = items

        return {
            "filter": safe_filter,
            "items": filtered,
            "kpis": {
                "totalLTV": sum(int(item["ltv"]) for item in items),
                "criticalRenewals": sum(1 for item in items if item["daysLeft"] <= 45 and item["quadrant"] == "topRight"),
                "rescueCount": sum(1 for item in items if item["urgency"] == "rescue"),
                "avgEngagement": round((_avg([float(item["engagement"]) for item in items]) * 100), 2),
            },
        }
