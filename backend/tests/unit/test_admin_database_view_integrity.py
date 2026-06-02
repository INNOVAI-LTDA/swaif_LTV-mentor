from __future__ import annotations

from typing import Any

from app.services.admin_database_view_service import AdminDatabaseViewService


class _FakeRepository:
    def __init__(self, payloads: dict[str, dict[str, Any]]) -> None:
        self._payloads = payloads

    def snapshot_payloads(self) -> dict[str, dict[str, Any]]:
        return self._payloads


def test_database_view_integrity_flags_broken_links() -> None:
    payloads = {
        "contacts_users_v2": {
            "items": [
                {"id": "usr_1", "role": "provider", "password_hash": "x"},
                {"id": "usr_2", "role": "client", "password_hash": "x"},
                {"id": "usr_3", "role": "provider", "password_hash": "x"},
            ]
        },
        "organizations": {"items": [{"id": "org_1"}]},
        "products": {"items": [{"id": "prd_1", "organization_id": ""}]},
        "enrollments": {
            "items": [
                {"id": "enr_1", "provider_user_id": "usr_1", "client_user_id": "usr_2", "product_id": "prd_1"},
                {"id": "enr_2", "provider_user_id": "usr_999", "client_user_id": "", "product_id": "prd_missing"},
            ]
        },
        "pillars": {"items": [{"id": "plr_1", "product_id": ""}]},
        "metrics": {"items": [{"id": "met_1", "pillar_id": "plr_missing"}]},
        "measurements": {"items": [{"id": "mea_1", "enrollment_id": "enr_missing", "metric_id": "met_missing"}]},
        "checkpoints": {"items": [{"id": "chk_1", "enrollment_id": "enr_missing"}]},
    }
    service = AdminDatabaseViewService(_FakeRepository(payloads))

    snapshot = service.get_database_view_snapshot()
    integrity = snapshot["integrity"]

    assert any(item["providerId"] == "3" for item in integrity["providersWithoutEnrollments"])
    assert any(item["enrollmentId"] == "enr_2" for item in integrity["enrollmentsWithoutProvider"])
    assert any(item["enrollmentId"] == "enr_2" for item in integrity["enrollmentsWithoutClient"])
    assert any(item["enrollmentId"] == "enr_2" for item in integrity["enrollmentsWithoutProduct"])
    assert any(item["measurementId"] == "mea_1" for item in integrity["measurementsWithoutEnrollment"])
    assert any(item["measurementId"] == "mea_1" for item in integrity["measurementsWithoutMetric"])
    assert any(item["checkpointId"] == "chk_1" for item in integrity["checkpointsWithoutEnrollment"])
    assert any(item["productId"] == "prd_1" for item in integrity["productsWithoutOrganization"])
    assert any(item["metricId"] == "met_1" for item in integrity["metricsWithoutPillar"])
    assert any(item["pillarId"] == "plr_1" for item in integrity["pillarsWithoutProduct"])
