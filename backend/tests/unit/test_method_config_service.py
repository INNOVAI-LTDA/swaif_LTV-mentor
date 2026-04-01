from app.services.method_config_service import ConsistencyError, EntityNotFoundError, MethodConfigService


class _FakeProtocolRepository:
    def __init__(self) -> None:
        self.items: dict[str, dict] = {}
        self._seq = 0

    def create(
        self,
        *,
        organization_id: str,
        name: str,
        code: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        self._seq += 1
        protocol = {
            "id": f"prt_{self._seq}",
            "organization_id": organization_id,
            "name": name,
            "code": code or f"protocol-{self._seq}",
            "metadata": metadata or {},
            "is_active": True,
        }
        self.items[protocol["id"]] = protocol
        return protocol

    def get_by_id(self, protocol_id: str) -> dict | None:
        return self.items.get(protocol_id)


class _FakePillarRepository:
    def __init__(self) -> None:
        self.items: dict[str, dict] = {}
        self._seq = 0

    def create(
        self,
        *,
        protocol_id: str,
        name: str,
        code: str | None = None,
        order_index: int = 0,
        metadata: dict | None = None,
    ) -> dict:
        self._seq += 1
        pillar = {
            "id": f"plr_{self._seq}",
            "protocol_id": protocol_id,
            "name": name,
            "code": code or f"pillar-{self._seq}",
            "order_index": order_index,
            "metadata": metadata or {},
            "is_active": True,
        }
        self.items[pillar["id"]] = pillar
        return pillar

    def get_by_id(self, pillar_id: str) -> dict | None:
        return self.items.get(pillar_id)

    def list_pillars(self) -> list[dict]:
        return list(self.items.values())


class _FakeMetricRepository:
    def __init__(self) -> None:
        self.items: dict[str, dict] = {}
        self._seq = 0

    def create(
        self,
        *,
        protocol_id: str,
        pillar_id: str,
        name: str,
        code: str | None = None,
        direction: str = "higher_better",
        unit: str | None = None,
        # metadata: dict | None = None,  # removed
        scoring_rules=None,
        score_type=None,
        min_score=None,
        max_score=None,
        mcv_score=None,
        max_basis_score=None,
    ) -> dict:
        self._seq += 1
        metric = {
            "id": f"met_{self._seq}",
            "protocol_id": protocol_id,
            "pillar_id": pillar_id,
            "name": name,
            "code": code or f"metric-{self._seq}",
            "direction": direction,
            "unit": unit,
            "is_active": True,
            "scoring_rules": scoring_rules or [{"type": "static", "score": 1}],
            "score_type": score_type or "static",
            "min_score": min_score if min_score is not None else 0,
            "max_score": max_score if max_score is not None else 1,
            "mcv_score": mcv_score if mcv_score is not None else 1,
            "max_basis_score": max_basis_score if max_basis_score is not None else 1,
        }
        self.items[metric["id"]] = metric
        return metric

    def list_metrics(self) -> list[dict]:
        return list(self.items.values())


def test_method_config_creation_flow() -> None:
    service = MethodConfigService(
        protocols=_FakeProtocolRepository(),
        pillars=_FakePillarRepository(),
        metrics=_FakeMetricRepository(),
    )

    protocol = service.create_protocol(organization_id="org_1", name="Metodo Mentoria")
    pillar = service.create_pillar(protocol_id=protocol["id"], name="Clareza")
    metric = service.create_metric(protocol_id=protocol["id"], pillar_id=pillar["id"], name="Aderencia")

    assert protocol["organization_id"] == "org_1"
    assert pillar["protocol_id"] == protocol["id"]
    assert metric["pillar_id"] == pillar["id"]


def test_method_config_consistency_validation() -> None:
    service = MethodConfigService(
        protocols=_FakeProtocolRepository(),
        pillars=_FakePillarRepository(),
        metrics=_FakeMetricRepository(),
    )
    protocol_a = service.create_protocol(organization_id="org_1", name="Metodo A")
    protocol_b = service.create_protocol(organization_id="org_2", name="Metodo B")
    pillar = service.create_pillar(protocol_id=protocol_a["id"], name="Foco")

    try:
        service.create_metric(protocol_id=protocol_b["id"], pillar_id=pillar["id"], name="Execucao")
        assert False, "expected ConsistencyError"
    except ConsistencyError:
        assert True

    try:
        service.create_pillar(protocol_id="prt_missing", name="Missing")
        assert False, "expected EntityNotFoundError"
    except EntityNotFoundError:
        assert True


def test_method_config_structure_listing() -> None:
    service = MethodConfigService(
        protocols=_FakeProtocolRepository(),
        pillars=_FakePillarRepository(),
        metrics=_FakeMetricRepository(),
    )
    protocol = service.create_protocol(organization_id="org_1", name="Metodo A")
    pillar_b = service.create_pillar(protocol_id=protocol["id"], name="Resultados", order_index=2)
    pillar_a = service.create_pillar(protocol_id=protocol["id"], name="Consistencia", order_index=1)
    service.create_metric(protocol_id=protocol["id"], pillar_id=pillar_a["id"], name="Frequencia")
    service.create_metric(protocol_id=protocol["id"], pillar_id=pillar_b["id"], name="Entrega")

    structure = service.get_protocol_structure(protocol_id=protocol["id"])

    assert structure["protocol"]["id"] == protocol["id"]
    assert len(structure["pillars"]) == 2
    assert structure["pillars"][0]["order_index"] == 1
    assert len(structure["pillars"][0]["metrics"]) == 1
