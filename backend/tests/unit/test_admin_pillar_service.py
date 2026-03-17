from app.services.admin_pillar_service import AdminPillarService, EntityNotFoundError, ValidationError


class _FakeOrganizationRepository:
    def __init__(self) -> None:
        self.items = {
            "org_1": {
                "id": "org_1",
                "name": "Acelerador Medico Premium",
                "code": "AMP-PREMIUM",
                "is_active": True,
            }
        }

    def get_by_id(self, product_id: str) -> dict | None:
        return self.items.get(product_id)


class _FakeProtocolRepository:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def list_by_organization(self, organization_id: str) -> list[dict]:
        return [item for item in self.items if item["organization_id"] == organization_id]

    def create(self, **payload) -> dict:
        item = {
            "id": f"prt_{len(self.items) + 1}",
            "is_active": True,
            "metadata": {},
            **payload,
        }
        self.items.append(item)
        return item


class _FakePillarRepository:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def list_pillars(self) -> list[dict]:
        return list(self.items)

    def create(self, **payload) -> dict:
        if any(
            item["protocol_id"] == payload["protocol_id"] and item["code"] == (payload.get("code") or payload["name"]).strip().lower().replace(" ", "-")
            for item in self.items
        ):
            raise ValueError("pillar code already exists in protocol")

        item = {
            "id": f"plr_{len(self.items) + 1}",
            "is_active": True,
            "metadata": {},
            **payload,
        }
        item["code"] = (payload.get("code") or payload["name"]).strip().lower().replace(" ", "-")
        self.items.append(item)
        return item


def test_service_creates_first_pillar_and_protocol_for_product() -> None:
    protocols = _FakeProtocolRepository()
    service = AdminPillarService(_FakeOrganizationRepository(), protocols, _FakePillarRepository())

    created = service.create_pillar(product_id="org_1", name="Performance")

    assert created["name"] == "Performance"
    assert created["protocol_id"] == "prt_1"
    assert protocols.items[0]["organization_id"] == "org_1"


def test_service_lists_pillars_sorted_by_order_and_name() -> None:
    organizations = _FakeOrganizationRepository()
    protocols = _FakeProtocolRepository()
    pillars = _FakePillarRepository()
    protocols.create(organization_id="org_1", name="Metodo A", code="org_1-metodo")
    pillars.items.extend(
        [
            {"id": "plr_1", "protocol_id": "prt_1", "name": "Retencao", "code": "retencao", "order_index": 2, "is_active": True},
            {"id": "plr_2", "protocol_id": "prt_1", "name": "Aquisicao", "code": "aquisicao", "order_index": 1, "is_active": True},
        ]
    )
    service = AdminPillarService(organizations, protocols, pillars)

    listed = service.list_pillars_by_product("org_1")

    assert [item["name"] for item in listed] == ["Aquisicao", "Retencao"]


def test_service_rejects_blank_pillar_name() -> None:
    service = AdminPillarService(_FakeOrganizationRepository(), _FakeProtocolRepository(), _FakePillarRepository())

    try:
        service.create_pillar(product_id="org_1", name=" ")
    except ValidationError as exc:
        assert str(exc) == "name is required"
    else:
        raise AssertionError("ValidationError was expected")


def test_service_requires_existing_product() -> None:
    service = AdminPillarService(_FakeOrganizationRepository(), _FakeProtocolRepository(), _FakePillarRepository())

    try:
        service.list_pillars_by_product("org_missing")
    except EntityNotFoundError as exc:
        assert str(exc) == "product not found"
    else:
        raise AssertionError("EntityNotFoundError was expected")
