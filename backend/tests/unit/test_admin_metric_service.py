from pathlib import Path

from app.services.admin_metric_service import AdminMetricService
from app.storage.metric_repository import MetricRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository


def test_list_metrics_by_product_uses_strict_product_links(tmp_path: Path) -> None:
    protocols = ProtocolRepository(tmp_path / "protocols.json")
    pillars = PillarRepository(tmp_path / "pillars.json")
    metrics = MetricRepository(tmp_path / "metrics.json")

    protocol = protocols.create(organization_id="prd_A", name="Metodo A")
    pillars._write_items(
        [
            {"id": "plr_a", "protocol_id": protocol["id"], "product_id": "prd_A", "name": "Pilar A", "is_active": True},
            {"id": "plr_b", "protocol_id": protocol["id"], "product_id": "prd_B", "name": "Pilar B", "is_active": True},
        ]
    )
    metrics._write_items(
        [
            {"id": "mtr_a", "pillar_id": "plr_a", "product_id": "prd_A", "name": "Metrica A", "is_active": True},
            {"id": "mtr_b", "pillar_id": "plr_b", "product_id": "prd_B", "name": "Metrica B", "is_active": True},
        ]
    )

    service = AdminMetricService(protocols=protocols, pillars=pillars, metrics=metrics)

    result = service.list_metrics_by_product("prd_A")

    assert [item["id"] for item in result] == ["mtr_a"]
