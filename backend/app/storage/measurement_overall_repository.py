from __future__ import annotations

import csv
import hashlib
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from app.storage.json_repository import JsonRepository
from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.protocol_repository import ProtocolRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.metric_repository import MetricRepository
from app.storage.student_repository import StudentRepository


PRD_THR = 0.7
ENG_THR = 0.7
PRODUCT_PILLARS_BY_PROTOCOL = {
    "prt_3": {"plr_6", "plr_7", "plr_9", "plr_10"},
}
ENGAGEMENT_PILLAR_BY_PROTOCOL = {
    "prt_3": "plr_8",
}
FIRST_LOAD_TEMPERATURE_SCORE = {
    "FRIO": 0.18,
    "MORNO": 0.76,
    "QUENTE": 0.92,
}
FIRST_LOAD_STATUS_SCORE = {
    "ATIVO": 0.84,
    "A RENOVAR": 0.2,
}
FIRST_LOAD_CALL_COLUMNS = ("1ª CALL", "2ª CALL", "3ª CALL", "4ª CALL", "5ª CALL")


def default_measurement_overall_store_path() -> Path:
    configured = os.getenv("MEASUREMENT_OVERALL_STORE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data" / "measurement_overalls.json"


def default_first_load_student_source_path() -> Path:
    configured = os.getenv("MASTER_ACCMED_STUDENTS_TSV_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "data_ops" / "master_accmed_students.tsv"


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _normalize_lookup_key(value: Any) -> str:
    return "".join(char.lower() for char in str(value or "") if char.isalnum())


def _deterministic_uniform(seed: str, channel: str) -> float:
    digest = hashlib.sha256(f"{seed}:{channel}".encode("utf-8")).digest()
    number = int.from_bytes(digest[:8], "big")
    return (number + 1) / float((1 << 64) + 1)


def _deterministic_gaussian(seed: str, channel: str, scale: float) -> float:
    if scale <= 0:
        return 0.0
    u1 = max(_deterministic_uniform(seed, f"{channel}:u1"), 1e-9)
    u2 = _deterministic_uniform(seed, f"{channel}:u2")
    z_score = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return z_score * scale


def _parse_iso_date(value: Any):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw[:10]).date()
    except ValueError:
        return None


class MeasurementOverallRepository:
    def __init__(self, file_path: str | Path | None = None) -> None:
        self._store = JsonRepository(file_path or default_measurement_overall_store_path())
        if not self._store.file_path.exists():
            self._store.write({"version": 1, "items": []})

    def _read_items(self) -> list[dict[str, Any]]:
        payload = self._store.read()
        items = payload.get("items", [])
        return [item for item in items if isinstance(item, dict)]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        self._store.write({"version": 1, "items": items})

    def list_all(self) -> list[dict[str, Any]]:
        return self._read_items()

    def upsert_for_enrollment(self, enrollment_id: str, data: dict[str, Any]) -> None:
        items = self._read_items()
        items = [item for item in items if item.get("enrollment_id") != enrollment_id]
        items.append(data)
        self._write_items(items)

    def generate_for_all_enrollments(self):
        enrollments = EnrollmentRepository().list_enrollments()
        protocols = ProtocolRepository().list_protocols()
        pillars = PillarRepository().list_pillars()
        metrics = MetricRepository().list_metrics()
        students = StudentRepository().list_students()

        def derive_metric_tuple(metric: dict[str, Any]) -> dict[str, float]:
            max_score = float(metric.get("max_score") or 0)
            mcv = float(metric.get("mcv") or 0)

            if max_score <= 0:
                return {"goal": 0.0, "base": 0.0, "real": 0.0}

            normalized_mcv = max(0.0, min(mcv / max_score, 1.0))
            return {
                "goal": 1.0,
                "base": normalized_mcv,
                "real": normalized_mcv,
            }

        def load_first_load_profiles() -> dict[str, dict[str, Any]]:
            source_path = default_first_load_student_source_path()
            if not source_path.exists():
                return {}

            student_id_by_email = {
                str(student.get("email") or "").strip().lower(): str(student.get("id"))
                for student in students
                if student.get("id") and student.get("email")
            }
            student_id_by_name = {
                _normalize_lookup_key(student.get("full_name")): str(student.get("id"))
                for student in students
                if student.get("id") and student.get("full_name")
            }

            profiles: dict[str, dict[str, Any]] = {}
            with source_path.open("r", encoding="utf-8", errors="replace") as handle:
                reader = csv.DictReader(handle, delimiter="\t")
                for row in reader:
                    email_key = str(row.get("E-MAIL") or "").strip().lower()
                    student_id = student_id_by_email.get(email_key)
                    if not student_id:
                        student_id = student_id_by_name.get(_normalize_lookup_key(row.get("Nome")))
                    if not student_id:
                        continue

                    call_count = sum(1 for column in FIRST_LOAD_CALL_COLUMNS if str(row.get(column) or "").strip())
                    profiles[student_id] = {
                        "lead_temperature": str(row.get("TEMPERATURA LEAD") or "").strip().upper(),
                        "status_label": str(row.get("STATUS") or "").strip().upper(),
                        "call_count": call_count,
                    }
            return profiles

        def derive_cycle_score(student: dict[str, Any]) -> float:
            start_date = _parse_iso_date(student.get("start_enrollment_date"))
            end_date = _parse_iso_date(student.get("end_enrollment_date"))
            if not start_date or not end_date or end_date <= start_date:
                return 0.4

            today = datetime.now(timezone.utc).date()
            if today < start_date:
                return 0.45
            if today <= end_date:
                total_days = max((end_date - start_date).days, 1)
                elapsed_ratio = (today - start_date).days / total_days
                return max(0.58, min(0.86, 0.6 + elapsed_ratio * 0.22))

            overdue_days = (today - end_date).days
            return max(0.1, 0.4 - min(overdue_days / 365, 1.0) * 0.3)

        def derive_engagement_anchor(student: dict[str, Any], profile: dict[str, Any] | None, *, seed_key: str) -> float:
            if not profile:
                status_value = str(student.get("status") or "").strip().lower()
                if status_value == "renewing":
                    base_value = 0.28
                    return _clamp01(base_value + _deterministic_gaussian(seed_key, "engagement_fallback", 0.035))
                if status_value == "active":
                    base_value = 0.72
                    return _clamp01(base_value + _deterministic_gaussian(seed_key, "engagement_fallback", 0.035))
                return _clamp01(0.5 + _deterministic_gaussian(seed_key, "engagement_fallback", 0.035))
            lead_temperature = FIRST_LOAD_TEMPERATURE_SCORE.get(str(profile.get("lead_temperature") or "").upper(), 0.45)
            call_score = min(float(profile.get("call_count") or 0) / 5.0, 1.0)
            anchor = 0.82 * lead_temperature + 0.08 * call_score + 0.08
            return _clamp01(anchor + _deterministic_gaussian(seed_key, "engagement_anchor", 0.04))

        def derive_product_anchor(student: dict[str, Any], profile: dict[str, Any] | None, *, seed_key: str) -> float:
            if profile:
                status_label = str(profile.get("status_label") or "").upper()
            else:
                status_value = str(student.get("status") or "").strip().lower()
                status_label = "A RENOVAR" if status_value == "renewing" else "ATIVO"
            status_score = FIRST_LOAD_STATUS_SCORE.get(status_label, 0.5)
            cycle_score = derive_cycle_score(student)
            anchor = 0.85 * status_score + 0.15 * cycle_score
            return _clamp01(anchor + _deterministic_gaussian(seed_key, "product_anchor", 0.04))

        def derive_pillar_targets(*, student: dict[str, Any], profile: dict[str, Any] | None, seed_key: str) -> dict[str, float]:
            product_anchor = derive_product_anchor(student, profile, seed_key=seed_key)
            engagement_anchor = derive_engagement_anchor(student, profile, seed_key=seed_key)
            cycle_score = derive_cycle_score(student)
            return {
                "plr_6": _clamp01(product_anchor - 0.03 + _deterministic_gaussian(seed_key, "pillar_plr_6", 0.03)),
                "plr_7": _clamp01(product_anchor + 0.03 + _deterministic_gaussian(seed_key, "pillar_plr_7", 0.03)),
                "plr_8": _clamp01(engagement_anchor + _deterministic_gaussian(seed_key, "pillar_plr_8", 0.025)),
                "plr_9": _clamp01(product_anchor + (cycle_score - 0.5) * 0.08 + _deterministic_gaussian(seed_key, "pillar_plr_9", 0.03)),
                "plr_10": _clamp01(product_anchor - 0.02 + _deterministic_gaussian(seed_key, "pillar_plr_10", 0.03)),
            }

        def derive_metric_from_pillar(*, pillar_target: float, index: int, total: int, seed_key: str) -> dict[str, float]:
            if total <= 1:
                metric_value = pillar_target
            else:
                spread = ((index + 0.5) / total) - 0.5
                metric_value = _clamp01(
                    pillar_target
                    + spread * 0.08
                    + _deterministic_gaussian(seed_key, f"metric_{index}", 0.018)
                )
            return {"goal": 1.0, "base": metric_value, "real": metric_value}

        def aggregate_pillar(metric_values: list[dict[str, float]]) -> dict[str, float]:
            if not metric_values:
                return {"goal": 0.0, "base": 0.0, "real": 0.0}
            return {
                "goal": max(item["goal"] for item in metric_values),
                "base": sum(item["base"] for item in metric_values) / len(metric_values),
                "real": sum(item["real"] for item in metric_values) / len(metric_values),
            }

        # Map for quick lookup
        protocol_by_org = {p["organization_id"]: p for p in protocols}
        students_by_id = {str(student.get("id")): student for student in students if student.get("id")}
        first_load_profiles = load_first_load_profiles()
        pillars_by_protocol = {}
        for pillar in pillars:
            pillars_by_protocol.setdefault(pillar["protocol_id"], []).append(pillar)
        metrics_by_protocol = {}
        for metric in metrics:
            metrics_by_protocol.setdefault(metric["protocol_id"], []).append(metric)

        items = []
        for enr in enrollments:
            org_id = enr["organization_id"]
            protocol = protocol_by_org.get(org_id)
            if not protocol:
                continue
            protocol_id = protocol["id"]

            protocol_metrics = metrics_by_protocol.get(protocol_id, [])
            protocol_pillars = pillars_by_protocol.get(protocol_id, [])
            student = students_by_id.get(str(enr.get("student_id") or ""), {})
            first_load_profile = first_load_profiles.get(str(enr.get("student_id") or ""))
            seed_key = f"{enr.get('id', '')}:{enr.get('student_id', '')}"
            pillar_targets = derive_pillar_targets(student=student, profile=first_load_profile, seed_key=seed_key) if student else {}

            metric_tuples = []
            metric_values_by_id: dict[str, dict[str, float]] = {}
            metrics_by_pillar: dict[str, list[dict[str, Any]]] = {}
            for metric in protocol_metrics:
                metrics_by_pillar.setdefault(str(metric.get("pillar_id") or ""), []).append(metric)

            for pillar_metrics in metrics_by_pillar.values():
                total_metrics = len(pillar_metrics)
                for index, metric in enumerate(pillar_metrics):
                    pillar_id = str(metric.get("pillar_id") or "")
                    if pillar_id in pillar_targets:
                        values = derive_metric_from_pillar(
                            pillar_target=pillar_targets[pillar_id],
                            index=index,
                            total=total_metrics,
                            seed_key=f"{seed_key}:{metric.get('id', '')}",
                        )
                    else:
                        values = derive_metric_tuple(metric)
                    metric_tuples.append({
                        "metric_id": metric["id"],
                        "values": values
                    })
                    metric_values_by_id[metric["id"]] = values

            pillar_tuples = []
            pillar_overalls: dict[str, float] = {}
            for pillar in protocol_pillars:
                pillar_metric_values = [
                    metric_values_by_id[metric["id"]]
                    for metric in protocol_metrics
                    if metric.get("pillar_id") == pillar.get("id") and metric.get("id") in metric_values_by_id
                ]
                pillar_tuple = aggregate_pillar(pillar_metric_values)
                pillar_tuples.append({
                    "pillar_id": pillar["id"],
                    "metric_average": pillar_tuple
                })
                pillar_overalls[pillar["id"]] = pillar_tuple["real"]

            product_pillars = PRODUCT_PILLARS_BY_PROTOCOL.get(protocol_id, set())
            engagement_pillar = ENGAGEMENT_PILLAR_BY_PROTOCOL.get(protocol_id)
            product_pillar_values = [pillar_overalls.get(pid, 0.0) for pid in product_pillars]
            decision_matrix = {
                "product_score": (
                    sum(product_pillar_values) / len(product_pillar_values)
                    if product_pillar_values
                    else 0.0
                ),
                "engagement_score": pillar_overalls.get(engagement_pillar, 0.0) if engagement_pillar else 0.0,
                "thresholds": {"prd_thr": PRD_THR, "eng_thr": ENG_THR},
            }

            items.append({
                "enrollment_id": enr["id"],
                "protocol_id": protocol_id,
                "metrics": metric_tuples,
                "pillars": pillar_tuples,
                "decision_matrix": decision_matrix
            })
        self._write_items(items)
