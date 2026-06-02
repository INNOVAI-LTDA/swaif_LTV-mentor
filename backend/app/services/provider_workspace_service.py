from __future__ import annotations

from typing import Any


class ProviderWorkspaceService:
    def __init__(
        self,
        hierarchy_repository: Any,
        *,
        product_metric_repository: Any | None = None,
        runtime_measurement_repository: Any | None = None,
    ) -> None:
        self._hierarchy_repository = hierarchy_repository
        self._product_metric_repository = product_metric_repository
        self._runtime_measurement_repository = runtime_measurement_repository

    @staticmethod
    def _derive_urgency(days_left: int, has_investment: bool) -> str:
        if days_left <= 15:
            return "rescue"
        if days_left <= 30:
            return "critical"
        if days_left <= 45 or not has_investment:
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
    def _resolve_matrix_quadrant(decision_matrix_status: str, *, days_left: int, urgency: str) -> str:
        normalized_status = decision_matrix_status.strip().lower()
        if normalized_status == "topright":
            return "topRight"
        if normalized_status in {"critical", "rescue"}:
            return "topRight"
        if urgency in {"critical", "rescue"} or days_left <= 45:
            return "topRight"
        return "bottomRight"

    def list_command_center_students(self, *, provider_user_id: str) -> dict[str, Any]:
        rows = self._hierarchy_repository.list_active_provider_hierarchy(provider_user_id)
        deduped_items: list[dict[str, Any]] = []
        seen_client_ids: set[str] = set()

        for row in rows:
            client_id = str(row.get("client_id") or "")
            if not client_id or client_id in seen_client_ids:
                continue
            seen_client_ids.add(client_id)

            days_left = int(row.get("days_left") or 0)
            investment_raw = row.get("investment")
            has_investment = investment_raw is not None
            ltv = int(float(investment_raw or 0))
            urgency = self._derive_urgency(days_left, has_investment)

            deduped_items.append(
                {
                    "id": client_id,
                    "name": str(row.get("client_name") or ""),
                    "programName": str(row.get("product_name") or ""),
                    "daysLeft": days_left,
                    "ltv": ltv,
                    "urgency": urgency,
                    "risk": self._derive_risk(urgency),
                }
            )

        total_ltv = sum(int(item["ltv"]) for item in deduped_items)
        critical_count = sum(1 for item in deduped_items if item["urgency"] in {"critical", "rescue"})

        return {
            "items": deduped_items,
            "kpis": {
                "totalLTV": total_ltv,
                "criticalRenewals": critical_count,
                "rescueCount": sum(1 for item in deduped_items if item["urgency"] == "rescue"),
                "avgEngagement": 0.0,
            },
            "rankingMode": "full",
            "context": {},
        }

    @staticmethod
    def _avg(values: list[float]) -> float:
        if not values:
            return 0.0
        return round(sum(values) / len(values), 2)

    def get_clients_radar(self, *, provider_user_id: str) -> dict[str, Any]:
        if self._product_metric_repository is None or self._runtime_measurement_repository is None:
            raise RuntimeError("ProviderWorkspaceService radar dependencies are not configured.")

        rows = self._hierarchy_repository.list_active_provider_hierarchy(provider_user_id)
        clients: list[dict[str, Any]] = []
        axis_accumulator: dict[str, dict[str, Any]] = {}
        seen_enrollment_ids: set[str] = set()

        for row in rows:
            enrollment_id = str(row.get("enrollment_id") or "")
            if not enrollment_id or enrollment_id in seen_enrollment_ids:
                continue
            seen_enrollment_ids.add(enrollment_id)

            client_id = str(row.get("client_id") or "")
            clients.append(
                {
                    "studentId": client_id,
                    "studentName": str(row.get("client_name") or ""),
                    "programName": str(row.get("product_name") or ""),
                    "daysLeft": int(row.get("days_left") or 0),
                }
            )

            product_id = str(row.get("product_id") or "")
            metric_tree = self._product_metric_repository.list_metric_tree_by_product(product_id)
            measurements = self._runtime_measurement_repository.list_by_enrollment(enrollment_id)
            measurements_by_metric = {str(item.get("metric_id") or ""): item for item in measurements}

            for pillar in metric_tree:
                pillar_id = str(pillar.get("id") or "")
                if not pillar_id:
                    continue
                baseline_values: list[float] = []
                current_values: list[float] = []
                projected_values: list[float] = []

                for metric in pillar.get("metrics", []):
                    measurement = measurements_by_metric.get(str(metric.get("id") or ""))
                    if measurement is None:
                        continue
                    baseline_values.append(float(measurement.get("value_baseline") or 0.0))
                    current_values.append(float(measurement.get("value_current") or 0.0))
                    projected_values.append(float(measurement.get("value_projected") or measurement.get("value_current") or 0.0))

                if not baseline_values and not current_values and not projected_values:
                    continue

                bucket = axis_accumulator.setdefault(
                    pillar_id,
                    {
                        "axisId": pillar_id,
                        "axisKey": str(pillar.get("slug") or pillar_id),
                        "axisLabel": str(pillar.get("name") or pillar_id),
                        "baseline": [],
                        "current": [],
                        "projected": [],
                    },
                )
                bucket["baseline"].append(self._avg(baseline_values))
                bucket["current"].append(self._avg(current_values))
                bucket["projected"].append(self._avg(projected_values))

        axis_scores: list[dict[str, Any]] = []
        for bucket in axis_accumulator.values():
            axis_scores.append(
                {
                    "axisId": str(bucket["axisId"]),
                    "axisKey": str(bucket["axisKey"]),
                    "axisLabel": str(bucket["axisLabel"]),
                    "axisSub": "",
                    "baseline": self._avg(bucket["baseline"]),
                    "current": self._avg(bucket["current"]),
                    "projected": self._avg(bucket["projected"]),
                    "sampleSize": len(bucket["current"]),
                    "insight": "",
                }
            )

        return {
            "clients": clients,
            "axisScores": axis_scores,
            "avgBaseline": self._avg([float(item.get("baseline") or 0.0) for item in axis_scores]),
            "avgCurrent": self._avg([float(item.get("current") or 0.0) for item in axis_scores]),
            "avgProjected": self._avg([float(item.get("projected") or 0.0) for item in axis_scores]),
            "context": {},
        }

    def get_student_radar(self, *, provider_user_id: str, client_user_id: str) -> dict[str, Any]:
        if self._product_metric_repository is None or self._runtime_measurement_repository is None:
            raise RuntimeError("ProviderWorkspaceService radar dependencies are not configured.")

        rows = self._hierarchy_repository.list_active_provider_hierarchy(provider_user_id)
        enrollment = next((row for row in rows if str(row.get("client_id") or "") == client_user_id), None)
        if enrollment is None:
            raise ValueError("enrollment_not_found")

        enrollment_id = str(enrollment.get("enrollment_id") or "")
        product_id = str(enrollment.get("product_id") or "")
        metric_tree = self._product_metric_repository.list_metric_tree_by_product(product_id)
        measurements = self._runtime_measurement_repository.list_by_enrollment(enrollment_id)
        measurements_by_metric = {str(item.get("metric_id") or ""): item for item in measurements}

        axis_scores: list[dict[str, Any]] = []
        for pillar in metric_tree:
            baseline_values: list[float] = []
            current_values: list[float] = []
            projected_values: list[float] = []

            for metric in pillar.get("metrics", []):
                measurement = measurements_by_metric.get(str(metric.get("id") or ""))
                if measurement is None:
                    continue
                baseline_values.append(float(measurement.get("value_baseline") or 0.0))
                current_values.append(float(measurement.get("value_current") or 0.0))
                projected_values.append(float(measurement.get("value_projected") or measurement.get("value_current") or 0.0))

            axis_scores.append(
                {
                    "axisId": str(pillar.get("id") or ""),
                    "axisKey": str(pillar.get("slug") or pillar.get("id") or ""),
                    "axisLabel": str(pillar.get("name") or pillar.get("id") or ""),
                    "axisSub": "",
                    "baseline": self._avg(baseline_values),
                    "current": self._avg(current_values),
                    "projected": self._avg(projected_values),
                    "insight": "",
                }
            )

        return {
            "studentId": client_user_id,
            "axisScores": axis_scores,
            "avgBaseline": self._avg([float(item.get("baseline") or 0.0) for item in axis_scores]),
            "avgCurrent": self._avg([float(item.get("current") or 0.0) for item in axis_scores]),
            "avgProjected": self._avg([float(item.get("projected") or 0.0) for item in axis_scores]),
            "context": {},
        }

    def get_renewal_matrix(self, *, provider_user_id: str, filter_mode: str = "all") -> dict[str, Any]:
        rows = self._hierarchy_repository.list_active_provider_hierarchy(provider_user_id)
        items: list[dict[str, Any]] = []
        seen_client_ids: set[str] = set()

        for row in rows:
            client_id = str(row.get("client_id") or "")
            if not client_id or client_id in seen_client_ids:
                continue
            seen_client_ids.add(client_id)

            days_left = int(row.get("days_left") or 0)
            decision_matrix_status = str(row.get("decision_matrix_status") or "").strip()
            urgency = self._derive_urgency(days_left, row.get("investment") is not None)
            quadrant = self._resolve_matrix_quadrant(
                decision_matrix_status,
                days_left=days_left,
                urgency=urgency,
            )
            ltv = int(float(row.get("investment") or 0))
            items.append(
                {
                    "id": client_id,
                    "name": str(row.get("client_name") or ""),
                    "programName": str(row.get("product_name") or ""),
                    "progress": 0.0,
                    "engagement": 0.0,
                    "quadrant": quadrant,
                    "daysLeft": days_left,
                    "ltv": ltv,
                    "decisionMatrixStatus": decision_matrix_status,
                    "urgency": urgency,
                }
            )

        normalized_filter = filter_mode if filter_mode in {"all", "topRight", "critical", "rescue"} else "all"
        if normalized_filter == "topRight":
            filtered = [item for item in items if item["quadrant"] == "topRight"]
        elif normalized_filter == "critical":
            filtered = [item for item in items if str(item["decisionMatrixStatus"]).strip().lower() == "critical"]
        elif normalized_filter == "rescue":
            filtered = [item for item in items if str(item["decisionMatrixStatus"]).strip().lower() == "rescue"]
        else:
            filtered = items

        return {
            "filter": normalized_filter,
            "items": filtered,
            "kpis": {
                "totalLTV": sum(int(item["ltv"]) for item in items),
                "criticalRenewals": sum(
                    1
                    for item in items
                    if str(item["decisionMatrixStatus"]).strip().lower() in {"critical", "rescue"}
                ),
                "rescueCount": sum(
                    1 for item in items if str(item["decisionMatrixStatus"]).strip().lower() == "rescue"
                ),
                "avgEngagement": 0.0,
            },
            "context": {},
        }
