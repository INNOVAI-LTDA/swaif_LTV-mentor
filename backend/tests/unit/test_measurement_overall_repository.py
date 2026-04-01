from __future__ import annotations

from app.storage.measurement_overall_repository import (
    ENG_THR,
    PRD_THR,
    ENGAGEMENT_PILLAR_BY_PROTOCOL,
    PRODUCT_PILLARS_BY_PROTOCOL,
    MeasurementOverallRepository,
)


def test_generate_measurement_overalls_contract_for_views(monkeypatch, tmp_path) -> None:
    output_path = tmp_path / "measurement_overalls.json"
    monkeypatch.setenv("MEASUREMENT_OVERALL_STORE_PATH", str(output_path))

    repo = MeasurementOverallRepository()
    repo.generate_for_all_enrollments()

    items = repo.list_all()
    assert items, "Expected generated measurement overalls to be non-empty"

    for item in items:
        protocol_id = item["protocol_id"]

        # Command Center and Radar rely on complete metric/pillar tuples per enrollment.
        assert len(item["metrics"]) > 0
        assert len(item["pillars"]) > 0

        # All metric tuples must be normalized percentages for first-load behavior.
        for metric in item["metrics"]:
            values = metric["values"]
            assert 0.0 <= values["goal"] <= 1.0
            assert 0.0 <= values["base"] <= 1.0
            assert 0.0 <= values["real"] <= 1.0

        pillar_real_by_id = {
            pillar["pillar_id"]: pillar["metric_average"]["real"] for pillar in item["pillars"]
        }

        # Radar pillar values must be normalized percentages as well.
        for pillar in item["pillars"]:
            metric_average = pillar["metric_average"]
            assert 0.0 <= metric_average["goal"] <= 1.0
            assert 0.0 <= metric_average["base"] <= 1.0
            assert 0.0 <= metric_average["real"] <= 1.0

        # Matrix values must match the contract and math rules.
        decision = item["decision_matrix"]
        product_pillars = PRODUCT_PILLARS_BY_PROTOCOL.get(protocol_id, set())
        if product_pillars:
            expected_product = sum(pillar_real_by_id.get(pid, 0.0) for pid in product_pillars) / len(product_pillars)
            assert decision["product_score"] == expected_product

        engagement_pillar = ENGAGEMENT_PILLAR_BY_PROTOCOL.get(protocol_id)
        if engagement_pillar:
            assert decision["engagement_score"] == pillar_real_by_id.get(engagement_pillar, 0.0)

        assert decision["thresholds"]["prd_thr"] == PRD_THR
        assert decision["thresholds"]["eng_thr"] == ENG_THR


def test_generate_measurement_overalls_varies_matrix_inputs(monkeypatch, tmp_path) -> None:
    output_path = tmp_path / "measurement_overalls.json"
    monkeypatch.setenv("MEASUREMENT_OVERALL_STORE_PATH", str(output_path))

    repo = MeasurementOverallRepository()
    repo.generate_for_all_enrollments()

    items = repo.list_all()
    assert items, "Expected generated measurement overalls to be non-empty"

    unique_pairs = {
        (
            round(float(item["decision_matrix"]["product_score"]), 3),
            round(float(item["decision_matrix"]["engagement_score"]), 3),
        )
        for item in items
    }
    assert len(unique_pairs) > 10

    quadrants = set()
    for item in items:
        product = float(item["decision_matrix"]["product_score"])
        engagement = float(item["decision_matrix"]["engagement_score"])
        if product >= PRD_THR and engagement >= ENG_THR:
            quadrants.add("topRight")
        elif product < 0.3 and engagement < 0.3:
            quadrants.add("bottomLeft")
        elif product < PRD_THR and engagement >= ENG_THR:
            quadrants.add("topLeft")
        elif product >= PRD_THR and engagement < ENG_THR:
            quadrants.add("bottomRight")

    assert quadrants >= {"topRight", "topLeft", "bottomRight", "bottomLeft"}
