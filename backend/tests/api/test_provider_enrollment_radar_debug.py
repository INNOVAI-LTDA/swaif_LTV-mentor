from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.provider import (
    get_provider_hierarchy_service,
    get_supabase_enrollment_repository,
    get_supabase_product_metric_repository,
    get_supabase_runtime_measurement_repository,
)
from app.core.security import hash_password
from app.main import app
from app.services.provider_hierarchy_service import ProviderHierarchyService
from app.storage.contact_user_repository import ContactUserRepository


class _FakeSupabaseEnrollmentRepository:
    def list_active_by_provider(self, provider_user_id: str):
        if provider_user_id == "101":
            return [
                {
                    "id": "enr-1",
                    "provider_user_id": "101",
                    "client_user_id": "201",
                    "product_id": "301",
                    "status": "active",
                }
            ]
        return []


class _FakeSupabaseProductMetricRepository:
    def list_metric_tree_by_product(self, product_id: str):
        if product_id != "301":
            return []
        return [
            {
                "id": "pillar-1",
                "name": "Pilar 1",
                "slug": "pilar-1",
                "orderIndex": 1,
                "metrics": [
                    {"id": "metric-1", "name": "Metrica 1", "slug": "metrica-1"},
                ],
            }
        ]


class _FakeSupabaseRuntimeMeasurementRepository:
    def list_by_enrollment(self, enrollment_id: str):
        if enrollment_id != "enr-1":
            return []
        return [
            {
                "id": "ms-1",
                "enrollment_id": "enr-1",
                "metric_id": "metric-1",
                "value_baseline": 1.0,
                "value_current": 2.0,
                "value_projected": 3.0,
                "improving_trend": True,
            }
        ]


def _seed_provider(contacts_file: Path) -> None:
    repo = ContactUserRepository(contacts_file)
    repo.create(
        id="101",
        full_name="Provider",
        email="provider@example.com",
        role="provider",
        is_active=True,
        password_hash=hash_password("provider123"),
    )


def _login_provider(client: TestClient) -> str:
    response = client.post("/auth/login", json={"email": "provider@example.com", "password": "provider123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_provider_enrollment_metric_tree_allows_owned_enrollment(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    _seed_provider(contacts_file)

    app.dependency_overrides[get_supabase_enrollment_repository] = lambda: _FakeSupabaseEnrollmentRepository()
    app.dependency_overrides[get_supabase_product_metric_repository] = lambda: _FakeSupabaseProductMetricRepository()
    app.dependency_overrides[get_supabase_runtime_measurement_repository] = lambda: _FakeSupabaseRuntimeMeasurementRepository()
    app.dependency_overrides[get_provider_hierarchy_service] = lambda: ProviderHierarchyService(hierarchy_repository=None)
    try:
        client = TestClient(app)
        token = _login_provider(client)
        response = client.get(
            "/provider/me/enrollments/enr-1/metric-tree",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["enrollmentId"] == "enr-1"
        assert payload["productId"] == "301"
        assert payload["pillars"][0]["metrics"][0]["measurement"]["metric_id"] == "metric-1"
    finally:
        app.dependency_overrides.pop(get_provider_hierarchy_service, None)
        app.dependency_overrides.pop(get_supabase_enrollment_repository, None)
        app.dependency_overrides.pop(get_supabase_product_metric_repository, None)
        app.dependency_overrides.pop(get_supabase_runtime_measurement_repository, None)


def test_provider_enrollment_metric_tree_blocks_other_provider_enrollment(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    _seed_provider(contacts_file)

    app.dependency_overrides[get_supabase_enrollment_repository] = lambda: _FakeSupabaseEnrollmentRepository()
    app.dependency_overrides[get_supabase_product_metric_repository] = lambda: _FakeSupabaseProductMetricRepository()
    app.dependency_overrides[get_supabase_runtime_measurement_repository] = lambda: _FakeSupabaseRuntimeMeasurementRepository()
    app.dependency_overrides[get_provider_hierarchy_service] = lambda: ProviderHierarchyService(hierarchy_repository=None)
    try:
        client = TestClient(app)
        token = _login_provider(client)
        response = client.get(
            "/provider/me/enrollments/enr-outro/metric-tree",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "ENROLLMENT_NOT_FOUND"
    finally:
        app.dependency_overrides.pop(get_provider_hierarchy_service, None)
        app.dependency_overrides.pop(get_supabase_enrollment_repository, None)
        app.dependency_overrides.pop(get_supabase_product_metric_repository, None)
        app.dependency_overrides.pop(get_supabase_runtime_measurement_repository, None)
