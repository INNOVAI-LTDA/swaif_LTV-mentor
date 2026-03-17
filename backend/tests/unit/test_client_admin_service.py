from app.services.client_admin_service import ClientAdminService, EntityNotFoundError, ValidationError


class _FakeClientRepository:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def list_clients(self) -> list[dict]:
        return list(self.items)

    def create(self, **payload) -> dict:
        if any(item["cnpj"] == payload["cnpj"] for item in self.items):
            raise ValueError("client cnpj already exists")
        item = {
            "id": f"cli_{len(self.items) + 1}",
            "status": "active",
            "is_active": True,
            "created_at": "2026-03-15T00:00:00Z",
            "updated_at": "2026-03-15T00:00:00Z",
            **payload,
        }
        self.items.append(item)
        return item

    def get_by_id(self, client_id: str) -> dict | None:
        for item in self.items:
            if item["id"] == client_id:
                return item
        return None


def test_service_creates_client_with_normalized_cnpj() -> None:
    service = ClientAdminService(_FakeClientRepository())

    created = service.create_client(
        name="Clinica Horizonte",
        brand_name="Horizonte",
        cnpj="12.345.678/0001-99",
    )

    assert created["cnpj"] == "12345678000199"
    assert created["brand_name"] == "Horizonte"
    assert created["currency"] == "BRL"


def test_service_rejects_invalid_cnpj() -> None:
    service = ClientAdminService(_FakeClientRepository())

    try:
        service.create_client(name="Clinica Horizonte", cnpj="123")
    except ValidationError as exc:
        assert str(exc) == "cnpj must contain 14 digits"
    else:
        raise AssertionError("ValidationError was expected")


def test_service_raises_when_client_is_missing() -> None:
    service = ClientAdminService(_FakeClientRepository())

    try:
        service.get_client_detail("cli_missing")
    except EntityNotFoundError as exc:
        assert str(exc) == "client not found"
    else:
        raise AssertionError("EntityNotFoundError was expected")
