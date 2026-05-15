from __future__ import annotations

import pytest

from app.services.metric_score_service import calculate_metric_score


def test_calculate_metric_score_v2_static_uses_rule_points_and_max_score_basis() -> None:
    metric = {
        "score_type": "static",
        "max_score": 20,
        "max_score_basis": "MAX_VALUE",
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "number"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {"when": {"op": "lt", "value": 100000}, "then": {"assign": 5}},
                    {"when": {"range": {"min": 100000, "max": 500000}}, "then": {"assign": 10}},
                    {"when": {"op": "gt", "value": 500000}, "then": {"assign": 20}},
                ],
            },
            "normalization": {"basis": "max_score", "value": 20},
        },
    }

    result = calculate_metric_score(metric, 500000.50)

    assert result.score == 20.0
    assert result.normalized_score == 1.0
    assert result.normalization_basis == 20.0


def test_calculate_metric_score_v2_range_uses_upper_bound_for_non_numeric_match() -> None:
    metric = {
        "score_type": "range",
        "max_score": 4,
        "max_score_basis": "MAX_RVALUE",
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "string"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {
                        "when": {"op": "eq", "value": "respondeu"},
                        "then": {"assign_range": {"min": 1, "max": 4, "policy": "max"}},
                    },
                    {"when": {"op": "eq", "value": "não respondeu"}, "then": {"assign": 0}},
                ],
            },
            "normalization": {"basis": "max_range", "value": 4},
        },
    }

    result = calculate_metric_score(metric, "respondeu")

    assert result.score == 4.0
    assert result.normalized_score == 1.0
    assert result.normalization_basis == 4.0


def test_calculate_metric_score_v2_accumulative_sums_matching_rules() -> None:
    metric = {
        "score_type": "accumulative",
        "max_score": 15,
        "max_score_basis": "MAX_OPT",
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "set"},
            "scoring": {
                "mode": "sum_matches",
                "rules": [
                    {"when": {"contains_any": ["medical_record", "prontuário", "prontuario"]}, "then": {"assign": 5}},
                    {"when": {"contains_any": ["crm"]}, "then": {"assign": 5}},
                    {"when": {"contains_any": ["cash_flow_dre", "fluxo de caixa/dre"]}, "then": {"assign": 5}},
                ],
            },
            "normalization": {"basis": "max_score", "value": 15},
        },
    }

    result = calculate_metric_score(metric, ["CRM", "Prontuário"])

    assert result.score == 10.0
    assert result.normalized_score == pytest.approx(10 / 15, rel=0, abs=1e-6)


def test_calculate_metric_score_v2_supports_field_based_sum_matches() -> None:
    metric = {
        "score_type": "static",
        "max_score": 10,
        "max_score_basis": "MAX_VALUE",
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "object"},
            "scoring": {
                "mode": "sum_matches",
                "rules": [
                    {"when": {"field": "presencas", "op": "gt", "value": 4}, "then": {"assign": 5}},
                    {"when": {"field": "feedback", "op": "gt", "value": 4}, "then": {"assign": 5}},
                ],
            },
            "normalization": {"basis": "max_score", "value": 10},
        },
    }

    result = calculate_metric_score(metric, {"presencas": 5, "feedback": 2})

    assert result.score == 5.0
    assert result.normalized_score == 0.5


def test_calculate_metric_score_v2_per_unit_normalizes_by_mcv() -> None:
    metric = {
        "score_type": "unrestricted_sum",
        "max_score": 10,
        "max_score_basis": "MCV",
        "mcv": 6,
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "number"},
            "scoring": {"mode": "per_unit", "points_per_unit": 2},
            "normalization": {"basis": "mcv", "value": 6},
        },
    }

    result = calculate_metric_score(metric, 4)

    assert result.score == 8.0
    assert result.normalization_basis == 6.0
    assert result.normalized_score == 1.0


def test_calculate_metric_score_legacy_v1_static_remains_supported() -> None:
    metric = {
        "score_type": "static",
        "max_score": 20,
        "max_score_basis": "MAX_VALUE",
        "scoring_rules": [
            {"points": 5, "condition": {"operator": "lt", "value": 100000}},
            {"points": 10, "condition": {"operator": "and", "min": 100000, "max": 500000}},
            {"points": 20, "condition": {"operator": "gt", "value": 500000}},
        ],
    }

    result = calculate_metric_score(metric, 500000.50)

    assert result.score == 20.0
    assert result.normalized_score == 1.0