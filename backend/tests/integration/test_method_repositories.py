from pathlib import Path

from app.storage.metric_repository import MetricRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository


def test_protocol_pillar_metric_persistence(tmp_path: Path) -> None:
    protocol_repo = ProtocolRepository(tmp_path / "protocols.json")
    pillar_repo = PillarRepository(tmp_path / "pillars.json")
    metric_repo = MetricRepository(tmp_path / "metrics.json")

    protocol = protocol_repo.create(organization_id="org_1", name="Metodo Base", code="metodo-base")
    pillar = pillar_repo.create(protocol_id=protocol["id"], name="Compromisso", code="compromisso", order_index=1)
    metric = metric_repo.create(
        protocol_id=protocol["id"],
        pillar_id=pillar["id"],
        name="Presenca",
        code="presenca",
        direction="higher_better",
        unit="%",
    )

    assert protocol_repo.get_by_id(protocol["id"]) is not None
    assert pillar_repo.get_by_id(pillar["id"]) is not None
    assert metric_repo.get_by_id(metric["id"]) is not None
    assert metric["protocol_id"] == protocol["id"]
    assert metric["pillar_id"] == pillar["id"]
