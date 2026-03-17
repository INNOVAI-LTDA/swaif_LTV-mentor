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
    assert measurements[0]["metric_id"] == "met_1"
    assert measurements[1]["value_projected"] is None
    assert len(checkpoints) == 2
    assert checkpoints[0]["week"] == 1
