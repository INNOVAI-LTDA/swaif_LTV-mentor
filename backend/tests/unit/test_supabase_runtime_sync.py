from __future__ import annotations

import json

from app.operations.sync_runtime_stores_from_supabase import SupabaseSyncConfig, _build_runtime_payloads
from app.operations.sync_runtime_stores_from_supabase import (
    _backfill_runtime_indicator_tables,
    sync_runtime_stores_from_supabase,
)


def test_build_runtime_payloads_maps_supabase_data_to_runtime_stores() -> None:
    source = {
        "users": [
            {
                "id": 1,
                "email": "mentor@example.com",
                "role": "provider",
                "full_name": "Mentor One",
                "is_active": True,
                "organization_id": None,
                "created_at": "2026-05-01T10:00:00Z",
                "updated_at": "2026-05-01T10:00:00Z",
                "password_hash": None,
            },
            {
                "id": 2,
                "email": "student@example.com",
                "role": "client",
                "full_name": "Student Two",
                "is_active": True,
                "organization_id": None,
                "created_at": "2026-05-01T10:00:00Z",
                "updated_at": "2026-05-01T10:00:00Z",
                "password_hash": None,
            },
        ],
        "organizations": [
            {
                "id": 99,
                "name": "Org Legacy",
                "brand_name": "Org Legacy",
                "slug": "org-legacy",
                "status": "active",
                "is_active": True,
                "created_at": "2026-05-01T10:00:00Z",
                "updated_at": "2026-05-01T10:00:00Z",
            }
        ],
        "products": [
            {
                "id": 10,
                "organization_id": 99,
                "name": "Mentoria Alpha",
                "slug": "mentoria-alpha",
                "status": "active",
                "created_at": "2026-05-01T10:00:00Z",
                "updated_at": "2026-05-01T10:00:00Z",
            }
        ],
        "pillars": [
            {
                "id": 20,
                "product_id": 10,
                "name": "Capacidade",
                "slug": "capacidade",
                "order_index": 1,
                "metadata": {},
                "is_active": True,
            }
        ],
        "metrics": [
            {
                "id": 30,
                "pillar_id": 20,
                "name": "Consultas",
                "slug": "consultas",
                "direction": "higher_better",
                "unit": None,
                "scoring_rules": {"version": 2},
                "score_type": "static",
                "min_score": 0,
                "max_score": 10,
                "max_score_basis": "MAX_VALUE",
                "mcv": 8,
                "is_active": True,
            }
        ],
        "enrollments": [
            {
                "id": 40,
                "provider_user_id": 1,
                "client_user_id": 2,
                "product_id": 10,
                "days_left": 30,
                "investment": 1500.5,
                "status": "active",
                "created_at": "2026-05-01T10:00:00Z",
                "updated_at": "2026-05-01T10:00:00Z",
            }
        ],
    }

    payloads = _build_runtime_payloads(
        source,
        SupabaseSyncConfig(
            database_url="postgres://fake",
            default_admin_password="admin123",
            default_provider_password="mentor123",
            default_client_password="aluno_accmed",
        ),
    )

    organizations = payloads["organizations"]["items"]
    protocols = payloads["protocols"]["items"]
    pillars = payloads["pillars"]["items"]
    metrics = payloads["metrics"]["items"]
    enrollments = payloads["enrollments"]["items"]
    measurements = payloads["measurements"]["items"]
    contacts = payloads["contacts_users_v2"]["items"]
    users = payloads["users"]["items"]

    assert len(organizations) == 1
    assert organizations[0]["id"] == "org_10"
    assert organizations[0]["name"] == "Mentoria Alpha"

    assert len(protocols) == 1
    assert protocols[0]["id"] == "prt_10"

    assert len(pillars) == 1
    assert pillars[0]["id"] == "plr_20"
    assert pillars[0]["protocol_id"] == "prt_10"

    assert len(metrics) == 1
    assert metrics[0]["id"] == "met_30"
    assert metrics[0]["pillar_id"] == "plr_20"

    assert len(enrollments) == 1
    assert enrollments[0]["id"] == "enr_40"
    assert enrollments[0]["mentor_id"] == "mtr_1"
    assert enrollments[0]["student_id"] == "std_2"
    assert enrollments[0]["organization_id"] == "org_10"
    assert enrollments[0]["ltv_cents"] == 150050

    assert len(measurements) == 1
    assert measurements[0]["enrollment_id"] == "enr_40"
    assert measurements[0]["metric_id"] == "met_30"
    assert measurements[0]["value_projected"] >= measurements[0]["value_current"]

    provider_contact = next(item for item in contacts if item["email"] == "mentor@example.com")
    assert provider_contact["role"] == "provider"
    assert str(provider_contact["password_hash"]).startswith("pbkdf2_sha256$")

    provider_user = next(item for item in users if item["email"] == "mentor@example.com")
    assert provider_user["role"] == "mentor"


class _FakeInsertMissingMeasurementRepo:
    def __init__(self) -> None:
        self._seen: set[tuple[str, str]] = set()

    def insert_missing_for_enrollment(self, enrollment_id: str, rows: list[dict]) -> dict[str, int]:
        inserted = 0
        for row in rows:
            key = (enrollment_id, str(row.get("metric_id") or ""))
            if key in self._seen:
                continue
            self._seen.add(key)
            inserted += 1
        candidates = len(rows)
        return {"candidates": candidates, "inserted": inserted, "skipped": candidates - inserted}


class _FakeInsertMissingCheckpointRepo:
    def __init__(self) -> None:
        self._seen: set[tuple[str, int]] = set()

    def insert_missing_for_enrollment(self, enrollment_id: str, rows: list[dict]) -> dict[str, int]:
        inserted = 0
        for row in rows:
            key = (enrollment_id, int(row.get("week") or 0))
            if key in self._seen:
                continue
            self._seen.add(key)
            inserted += 1
        candidates = len(rows)
        return {"candidates": candidates, "inserted": inserted, "skipped": candidates - inserted}


def test_runtime_backfill_targets_only_active_enrollments_and_is_idempotent() -> None:
    payloads = {
        "enrollments": {
            "version": 1,
            "items": [
                {"id": "enr_active", "is_active": True},
                {"id": "enr_inactive", "is_active": False},
            ],
        },
        "measurements": {
            "version": 1,
            "items": [
                {"id": "mea_1", "enrollment_id": "enr_active", "metric_id": "met_1", "value_baseline": 10, "value_current": 11},
                {"id": "mea_2", "enrollment_id": "enr_inactive", "metric_id": "met_2", "value_baseline": 20, "value_current": 19},
            ],
        },
        "checkpoints": {
            "version": 1,
            "items": [
                {"id": "chk_1", "enrollment_id": "enr_active", "week": 1, "status": "green"},
                {"id": "chk_2", "enrollment_id": "enr_inactive", "week": 1, "status": "yellow"},
            ],
        },
    }
    measurements_repo = _FakeInsertMissingMeasurementRepo()
    checkpoints_repo = _FakeInsertMissingCheckpointRepo()

    first = _backfill_runtime_indicator_tables(
        database_url="postgres://fake",
        payloads=payloads,
        measurements_repo=measurements_repo,
        checkpoints_repo=checkpoints_repo,
    )
    second = _backfill_runtime_indicator_tables(
        database_url="postgres://fake",
        payloads=payloads,
        measurements_repo=measurements_repo,
        checkpoints_repo=checkpoints_repo,
    )

    assert first["active_enrollments"] == 1
    assert first["measurement_candidates"] == 1
    assert first["measurement_inserted"] == 1
    assert first["measurement_skipped"] == 0
    assert first["checkpoint_candidates"] == 1
    assert first["checkpoint_inserted"] == 1
    assert first["checkpoint_skipped"] == 0

    assert second["active_enrollments"] == 1
    assert second["measurement_candidates"] == 1
    assert second["measurement_inserted"] == 0
    assert second["measurement_skipped"] == 1
    assert second["checkpoint_candidates"] == 1
    assert second["checkpoint_inserted"] == 0
    assert second["checkpoint_skipped"] == 1


def test_sync_runtime_exposes_backfill_counters_in_result_and_report(monkeypatch, tmp_path) -> None:
    source = {
        "users": [],
        "organizations": [],
        "products": [],
        "pillars": [],
        "metrics": [],
        "enrollments": [],
    }
    backfill = {
        "active_enrollments": 3,
        "measurement_candidates": 9,
        "measurement_inserted": 7,
        "measurement_skipped": 2,
        "checkpoint_candidates": 3,
        "checkpoint_inserted": 3,
        "checkpoint_skipped": 0,
    }

    monkeypatch.setattr(
        "app.operations.sync_runtime_stores_from_supabase._fetch_source_rows",
        lambda _: source,
    )
    monkeypatch.setattr(
        "app.operations.sync_runtime_stores_from_supabase._backfill_runtime_indicator_tables",
        lambda **_: backfill,
    )

    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(tmp_path / "contacts_users_v2.json"))
    monkeypatch.setenv("USER_STORE_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("ORG_STORE_PATH", str(tmp_path / "organizations.json"))
    monkeypatch.setenv("MENTOR_STORE_PATH", str(tmp_path / "mentors.json"))
    monkeypatch.setenv("STUDENT_STORE_PATH", str(tmp_path / "students.json"))
    monkeypatch.setenv("PROTOCOL_STORE_PATH", str(tmp_path / "protocols.json"))
    monkeypatch.setenv("PILLAR_STORE_PATH", str(tmp_path / "pillars.json"))
    monkeypatch.setenv("METRIC_STORE_PATH", str(tmp_path / "metrics.json"))
    monkeypatch.setenv("ENROLLMENT_STORE_PATH", str(tmp_path / "enrollments.json"))
    monkeypatch.setenv("MEASUREMENT_STORE_PATH", str(tmp_path / "measurements.json"))
    monkeypatch.setenv("CHECKPOINT_STORE_PATH", str(tmp_path / "checkpoints.json"))
    monkeypatch.setenv("MEASUREMENT_OVERALL_STORE_PATH", str(tmp_path / "measurement_overalls.json"))
    monkeypatch.setenv("SUPABASE_RUNTIME_SYNC_REPORT_PATH", str(tmp_path / "supabase_runtime_sync_report.json"))

    result = sync_runtime_stores_from_supabase(SupabaseSyncConfig(database_url="postgres://fake"))

    assert result.counters["runtime_backfill_active_enrollments"] == 3
    assert result.counters["runtime_backfill_measurement_candidates"] == 9
    assert result.counters["runtime_backfill_measurement_inserted"] == 7
    assert result.counters["runtime_backfill_measurement_skipped"] == 2
    assert result.counters["runtime_backfill_checkpoint_candidates"] == 3
    assert result.counters["runtime_backfill_checkpoint_inserted"] == 3
    assert result.counters["runtime_backfill_checkpoint_skipped"] == 0

    report = json.loads((tmp_path / "supabase_runtime_sync_report.json").read_text(encoding="utf-8"))
    assert report["runtime_backfill"]["active_enrollments"] == 3
    assert report["runtime_backfill"]["measurement_inserted"] == 7
    assert report["runtime_backfill"]["checkpoint_inserted"] == 3
