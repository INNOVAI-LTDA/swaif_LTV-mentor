from app.services.admin_product_service import AdminProductService, EntityNotFoundError, ValidationError


class _FakeClientRepository:
    def __init__(self) -> None:
        self.items = {
            "cli_1": {
                "id": "cli_1",
                "name": "Clinica Horizonte",
                "brand_name": "Horizonte",
                "is_active": True,
            }
        }

    def get_by_id(self, client_id: str) -> dict | None:
        return self.items.get(client_id)


class _FakeOrganizationRepository:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def list_by_client(self, client_id: str) -> list[dict]:
        return [item for item in self.items if item["client_id"] == client_id]

    def create(self, **payload) -> dict:
        if any(
            item["client_id"] == payload["client_id"] and item["code"] == payload["code"].upper()
            for item in self.items
        ):
            raise ValueError("organization code already exists")

        item = {
            "id": f"org_{len(self.items) + 1}",
            "status": "active",
            "is_active": True,
            "mentor_id": None,
            "created_at": "2026-03-15T00:00:00Z",
            "updated_at": "2026-03-15T00:00:00Z",
            **payload,
        }
        item["code"] = item["code"].upper()
        item["slug"] = payload.get("slug") or "produto"
        item["delivery_model"] = payload.get("delivery_model") or "live"
        self.items.append(item)
        return item

    def get_by_id(self, product_id: str) -> dict | None:
        for item in self.items:
            if item["id"] == product_id:
                return item
        return None


def test_service_creates_product_linked_to_client() -> None:
    service = AdminProductService(_FakeClientRepository(), _FakeOrganizationRepository())

    created = service.create_product(
        client_id="cli_1",
        name="Acelerador Medico Premium",
        code="amp-premium",
    )

    assert created["client_id"] == "cli_1"
    assert created["code"] == "AMP-PREMIUM"


def test_service_rejects_blank_name_or_code() -> None:
    service = AdminProductService(_FakeClientRepository(), _FakeOrganizationRepository())

    try:
        service.create_product(client_id="cli_1", name=" ", code=" ")
    except ValidationError as exc:
        assert str(exc) == "name and code are required"
    else:
        raise AssertionError("ValidationError was expected")


def test_service_requires_existing_client() -> None:
    service = AdminProductService(_FakeClientRepository(), _FakeOrganizationRepository())

    try:
        service.list_products_by_client("cli_missing")
    except EntityNotFoundError as exc:
        assert str(exc) == "client not found"
    else:
        raise AssertionError("EntityNotFoundError was expected")
