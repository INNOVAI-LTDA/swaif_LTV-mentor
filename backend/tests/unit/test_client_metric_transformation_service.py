from __future__ import annotations

import pytest

from app.services.client_metric_transformation_service import (
    build_mock_client_absolute_metrics,
    load_supabase_metric_rules_by_id,
    mock_metric_rules_as_strings,
    process_mock_client_absolute_metrics,
    score_relative_python_from_metric,
    transform_client_absolute_metrics,
    transform_client_absolute_metrics_python_with_rules,
)


def test_transform_client_absolute_metrics_python_covers_all_supabase_rules() -> None:
    rules = load_supabase_metric_rules_by_id()
    rows = build_mock_client_absolute_metrics(rules)
    result = transform_client_absolute_metrics_python_with_rules(rows=rows, metric_rules_by_id=rules)

    assert result["errors"] == []
    assert len(result["clients"]) == 1

    covered_metric_count = sum(
        len(pillar.get("metrics") or [])
        for pillar in result["clients"][0]["pillars"]
    )
    assert covered_metric_count == len(rules)


def test_process_mock_client_absolute_metrics_includes_rules_and_rows() -> None:
    rules = load_supabase_metric_rules_by_id()
    payload = process_mock_client_absolute_metrics()

    assert len(payload["sourceRows"]) == len(rules)
    assert payload["rulesAsString"] == mock_metric_rules_as_strings(rules)
    assert payload["processingMode"] == "python_rules"
    assert payload["metricsCovered"] == len(rules)
    assert payload["parityWithDeclarative"] is True


def test_python_rules_match_declarative_rules_for_all_supabase_metrics() -> None:
    rules = load_supabase_metric_rules_by_id()
    rows = build_mock_client_absolute_metrics(rules)
    declarative = transform_client_absolute_metrics(rows=rows, metric_rules_by_id=rules)
    python_rules = transform_client_absolute_metrics_python_with_rules(rows=rows, metric_rules_by_id=rules)

    assert python_rules == declarative


def test_python_engine_supports_multiply_input_action() -> None:
    """The python engine must accept `multiply_input` and return raw * factor.

    Before the backport in step 1, this raised
    `ScoreCalculationError("unsupported action for python rule scoring")`.
    """
    metric = {
        "id": "met_multiply",
        "direction": "higher_better",
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "number"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {"when": {"op": "gte", "value": 0}, "then": {"multiply_input": 0.5}},
                ],
            },
            "normalization": {"basis": "explicit", "value": 50},
        },
    }

    result = score_relative_python_from_metric(metric, 20)

    # 20 * 0.5 = 10; normalized = 10 / 50 = 0.2
    assert result == pytest.approx(0.2, abs=1e-6)


def test_python_engine_inverts_lower_better_direction() -> None:
    """The python engine must apply the same direction inversion as the live
    engine for `lower_better` metrics.
    """
    metric = {
        "id": "met_lower",
        "direction": "lower_better",
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "number"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {"when": {"op": "gte", "value": 100}, "then": {"assign": 1.0}},
                    {"when": {"op": "gte", "value": 0}, "then": {"assign": 0.0}},
                ],
            },
            "normalization": {"basis": "explicit", "value": 1.0},
        },
    }

    assert score_relative_python_from_metric(metric, 0) == pytest.approx(1.0, abs=1e-6)
    assert score_relative_python_from_metric(metric, 100) == pytest.approx(0.0, abs=1e-6)
