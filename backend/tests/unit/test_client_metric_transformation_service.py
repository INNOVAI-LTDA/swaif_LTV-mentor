from __future__ import annotations

from app.services.client_metric_transformation_service import (
    build_mock_client_absolute_metrics,
    load_supabase_metric_rules_by_id,
    mock_metric_rules_as_strings,
    process_mock_client_absolute_metrics,
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
