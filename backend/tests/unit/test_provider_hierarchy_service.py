from __future__ import annotations

from app.services.provider_hierarchy_service import ProviderHierarchyService


class _FakeHierarchyRepository:
    def __init__(self, rows):
        self._rows = rows

    def list_active_provider_hierarchy(self, provider_user_id: str):
        _ = provider_user_id
        return list(self._rows)


def test_get_provider_hierarchy_deduplicates_products_and_clients() -> None:
    rows = [
        {
            "enrollment_id": "enr-1",
            "enrollment_status": "active",
            "start_day": "2026-01-01",
            "days_left": 20,
            "investment": 10000.0,
            "decision_matrix_status": "rescue",
            "provider_id": "10",
            "provider_name": "Provider A",
            "provider_email": "provider.a@example.com",
            "provider_organization_id": "1",
            "client_id": "100",
            "client_name": "Client A",
            "client_email": "client.a@example.com",
            "product_id": "1000",
            "product_name": "Produto A",
            "product_slug": "produto-a",
            "product_category": "mentoria",
            "organization_id": "1",
            "organization_name": "Org A",
            "organization_slug": "org-a",
        },
        {
            "enrollment_id": "enr-2",
            "enrollment_status": "active",
            "start_day": "2026-01-02",
            "days_left": 18,
            "investment": 11000.0,
            "decision_matrix_status": "topRight",
            "provider_id": "10",
            "provider_name": "Provider A",
            "provider_email": "provider.a@example.com",
            "provider_organization_id": "1",
            "client_id": "101",
            "client_name": "Client B",
            "client_email": "client.b@example.com",
            "product_id": "1000",
            "product_name": "Produto A",
            "product_slug": "produto-a",
            "product_category": "mentoria",
            "organization_id": "1",
            "organization_name": "Org A",
            "organization_slug": "org-a",
        },
    ]

    service = ProviderHierarchyService(_FakeHierarchyRepository(rows))
    payload = service.get_provider_hierarchy("10")

    assert payload["provider"]["id"] == "10"
    assert payload["organization"]["id"] == "1"
    assert len(payload["enrollments"]) == 2
    assert len(payload["products"]) == 1
    assert payload["products"][0]["id"] == "1000"
    assert len(payload["clients"]) == 2
    assert {item["id"] for item in payload["clients"]} == {"100", "101"}
