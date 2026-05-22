from pathlib import Path

from app.storage.checkpoint_repository import CheckpointRepository
from app.storage.measurement_repository import MeasurementRepository


def test_measurements_and_checkpoints_persistence(tmp_path: Path) -> None:
    measurement_repo = MeasurementRepository(tmp_path / "measurements.json")
    checkpoint_repo = CheckpointRepository(tmp_path / "checkpoints.json")

    measurement_repo.replace_for_enrollment(
        "enr_1",
        [
            {"metric_id": "met_1", "value_baseline": 50, "value_current": 65, "value_projected": 72, "improving_trend": True},
            {"metric_id": "met_2", "value_baseline": 3, "value_current": 4, "value_projected": None, "improving_trend": None},
        ],
    )
    checkpoint_repo.replace_for_enrollment(
        "enr_1",
        [
            {"week": 1, "status": "green", "label": "Inicio"},
            {"week": 2, "status": "yellow", "label": "Ajuste"},
        ],
    )

    measurements = measurement_repo.list_by_enrollment("enr_1")
    checkpoints = checkpoint_repo.list_by_enrollment("enr_1")

    assert len(measurements) == 2
    measurements_by_metric = {item["metric_id"]: item for item in measurements}
    assert set(measurements_by_metric.keys()) == {"met_1", "met_2"}
    assert measurements_by_metric["met_2"]["value_projected"] is None
    assert len(checkpoints) == 2
    assert sorted(item["week"] for item in checkpoints) == [1, 2]
