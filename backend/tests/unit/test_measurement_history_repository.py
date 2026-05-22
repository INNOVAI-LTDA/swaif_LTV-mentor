from __future__ import annotations

from app.storage.measurement_history_repository import MeasurementHistoryRepository


def test_append_and_list_measurement_history_events(tmp_path) -> None:
    repository = MeasurementHistoryRepository(tmp_path / "measurement_history.json")

    inserted = repository.append_event(
        {
            "measurement_id": "mea_1",
            "enrollment_id": "enr_1",
            "metric_id": "met_1",
            "actor_user_id": "usr_1",
            "actor_role": "client",
            "value_absolute_before": 5,
            "value_absolute_after": 7,
            "value_relative_before": 0.5,
            "value_relative_after": 0.7,
            "rule_version": "2",
        }
    )

    assert inserted["id"]
    assert inserted["measurement_id"] == "mea_1"
    assert inserted["value_absolute_before"] == 5.0
    assert inserted["value_absolute_after"] == 7.0

    events = repository.list_events()
    assert len(events) == 1
    assert events[0]["measurement_id"] == "mea_1"

    by_measurement = repository.list_by_measurement("mea_1")
    assert len(by_measurement) == 1
    assert by_measurement[0]["rule_version"] == "2"
