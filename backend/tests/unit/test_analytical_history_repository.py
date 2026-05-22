from __future__ import annotations

from pathlib import Path

from app.storage.analytical_history_repository import AnalyticalHistoryRepository


def test_append_and_filter_analytical_history_events(tmp_path: Path) -> None:
    repository = AnalyticalHistoryRepository(tmp_path / "analytical_history.json")

    repository.append_event(
        {
            "event_type": "assignment_score_snapshot",
            "enrollment_id": "enr_1",
            "product_id": "org_1",
            "payload": {"product_score": 0.7, "engagement_score": 0.8},
        }
    )
    repository.append_event(
        {
            "event_type": "product_radar_snapshot",
            "product_id": "org_1",
            "pillar_id": "plr_1",
            "payload": {"current_score": 0.75, "sample_size": 3},
        }
    )

    all_events = repository.list_events()
    assert len(all_events) == 2

    enrollment_events = repository.list_by_enrollment("enr_1")
    assert len(enrollment_events) == 1
    assert enrollment_events[0]["event_type"] == "assignment_score_snapshot"

    product_events = repository.list_by_product("org_1")
    assert len(product_events) == 2
    assert any(event["event_type"] == "product_radar_snapshot" for event in product_events)
