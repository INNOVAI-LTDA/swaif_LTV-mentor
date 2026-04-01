from app.services.admin_metric_service import AdminMetricService, EntityNotFoundError, ValidationError


class _FakeProtocolRepository:
    def __init__(self) -> None:
        self.items = {
            "prt_1": {
                "id": "prt_1",
                "organization_id": "org_1",
                "name": "Metodo Produto",
                "is_active": True,
            }
        }

    def get_by_id(self, protocol_id: str) -> dict | None:
        return self.items.get(protocol_id)

    def list_by_organization(self, organization_id: str) -> list[dict]:
        return [item for item in self.items.values() if item["organization_id"] == organization_id]


class _FakePillarRepository:
    def __init__(self) -> None:
        self.items = {
            "plr_1": {
                "id": "plr_1",
                "protocol_id": "prt_1",
                "name": "Performance",
                "is_active": True,
            }
        }

    def get_by_id(self, pillar_id: str) -> dict | None:
        return self.items.get(pillar_id)

    def list_pillars(self) -> list[dict]:
        return list(self.items.values())


class _FakeMetricRepository:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def list_metrics(self) -> list[dict]:
        return list(self.items)

    def list_by_pillar(self, pillar_id: str) -> list[dict]:
        return [item for item in self.items if item["pillar_id"] == pillar_id]

    def create(self, **payload) -> dict:
        final_code = (payload.get("code") or payload["name"]).strip().lower().replace(" ", "-")
        if any(item["pillar_id"] == payload["pillar_id"] and item["code"] == final_code for item in self.items):
            raise ValueError("metric code already exists in pillar")

        # Remove legacy metadata, add new fields if not present
        item = {
            "id": f"met_{len(self.items) + 1}",
            "code": final_code,
            "is_active": True,
            **payload,
        }
        item.pop("metadata", None)
        # Add required new fields with dummy values if missing
        item.setdefault("scoring_rules", [{"type": "static", "score": 1}])
        item.setdefault("score_type", "static")
        item.setdefault("min_score", 0)
        item.setdefault("max_score", 1)
        item.setdefault("mcv_score", 1)
        item.setdefault("max_basis_score", 1)
        self.items.append(item)
        return item


def test_service_creates_metric_for_active_pillar() -> None:
    service = AdminMetricService(_FakeProtocolRepository(), _FakePillarRepository(), _FakeMetricRepository())

    created = service.create_metric(pillar_id="plr_1", name="Comparecimento", unit="%")

    assert created["pillar_id"] == "plr_1"
    assert created["protocol_id"] == "prt_1"
    assert created["unit"] == "%"


def test_service_lists_metrics_sorted_by_name() -> None:
    metrics = _FakeMetricRepository()
    metrics.items.extend(
        [
            {"id": "met_1", "protocol_id": "prt_1", "pillar_id": "plr_1", "name": "Engajamento", "code": "engajamento", "direction": "higher_better", "unit": "%", "is_active": True},
            {"id": "met_2", "protocol_id": "prt_1", "pillar_id": "plr_1", "name": "Comparecimento", "code": "comparecimento", "direction": "higher_better", "unit": "%", "is_active": True},
        ]
    )
    service = AdminMetricService(_FakeProtocolRepository(), _FakePillarRepository(), metrics)

    listed = service.list_metrics_by_pillar("plr_1")

    assert [item["name"] for item in listed] == ["Comparecimento", "Engajamento"]


def test_service_rejects_blank_metric_name() -> None:
    service = AdminMetricService(_FakeProtocolRepository(), _FakePillarRepository(), _FakeMetricRepository())

    try:
        service.create_metric(pillar_id="plr_1", name=" ")
    except ValidationError as exc:
        assert str(exc) == "name is required"
    else:
        raise AssertionError("ValidationError was expected")


def test_service_requires_existing_pillar() -> None:
    service = AdminMetricService(_FakeProtocolRepository(), _FakePillarRepository(), _FakeMetricRepository())

    try:
        service.list_metrics_by_pillar("plr_missing")
    except EntityNotFoundError as exc:
        assert str(exc) == "pillar not found"
    else:
        raise AssertionError("EntityNotFoundError was expected")


def test_service_lists_metrics_by_product() -> None:
    metrics = _FakeMetricRepository()
    metrics.items.extend(
        [
            {"id": "met_1", "protocol_id": "prt_1", "pillar_id": "plr_1", "name": "Comparecimento", "code": "comparecimento", "direction": "higher_better", "unit": "%", "is_active": True},
            {"id": "met_2", "protocol_id": "prt_1", "pillar_id": "plr_1", "name": "Engajamento", "code": "engajamento", "direction": "higher_better", "unit": "%", "is_active": True},
        ]
    )
    service = AdminMetricService(_FakeProtocolRepository(), _FakePillarRepository(), metrics)

    listed = service.list_metrics_by_product("org_1")

    assert len(listed) == 2
    assert listed[0]["pillar_name"] == "Performance"
