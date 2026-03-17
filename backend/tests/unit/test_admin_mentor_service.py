from app.services.admin_mentor_service import AdminMentorService, EntityNotFoundError, ValidationError


class _FakeOrganizationRepository:
    def __init__(self) -> None:
        self.items = {
            "org_1": {
                "id": "org_1",
                "client_id": "cli_1",
                "name": "Acelerador Medico Premium",
                "mentor_id": None,
                "is_active": True,
            }
        }

    def get_by_id(self, product_id: str) -> dict | None:
        return self.items.get(product_id)

    def set_mentor(self, product_id: str, mentor_id: str) -> dict:
        self.items[product_id]["mentor_id"] = mentor_id
        return self.items[product_id]


class _FakeMentorRepository:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def list_by_organization(self, organization_id: str) -> list[dict]:
        return [item for item in self.items if item["organization_id"] == organization_id]

    def create(self, **payload) -> dict:
        if any(item["email"] == payload["email"] for item in self.items):
            raise ValueError("mentor email already exists")
        if any(item["cpf"] == payload["cpf"] for item in self.items):
            raise ValueError("mentor cpf already exists")

        item = {
            "id": f"mtr_{len(self.items) + 1}",
            "status": "active",
            "is_active": True,
            "created_at": "2026-03-15T00:00:00Z",
            "updated_at": "2026-03-15T00:00:00Z",
            **payload,
        }
        self.items.append(item)
        return item


def test_service_creates_mentor_linked_to_product() -> None:
    organizations = _FakeOrganizationRepository()
    mentors = _FakeMentorRepository()
    service = AdminMentorService(organizations, mentors)

    created = service.create_mentor(
        product_id="org_1",
        full_name="Ana Mentora",
        cpf="123.456.789-00",
        email="ana@swaif.local",
    )

    assert created["organization_id"] == "org_1"
    assert created["cpf"] == "12345678900"
    assert organizations.items["org_1"]["mentor_id"] == created["id"]


def test_service_rejects_blank_required_fields() -> None:
    service = AdminMentorService(_FakeOrganizationRepository(), _FakeMentorRepository())

    try:
        service.create_mentor(product_id="org_1", full_name=" ", cpf=" ", email=" ")
    except ValidationError as exc:
        assert str(exc) == "full_name, cpf and email are required"
    else:
        raise AssertionError("ValidationError was expected")


def test_service_requires_existing_product() -> None:
    service = AdminMentorService(_FakeOrganizationRepository(), _FakeMentorRepository())

    try:
        service.list_mentors_by_product("org_missing")
    except EntityNotFoundError as exc:
        assert str(exc) == "product not found"
    else:
        raise AssertionError("EntityNotFoundError was expected")
