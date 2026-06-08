"""
Unit tests for the v2 metric rule-author validator and the boot-log helper
that emits per-metric warnings from the MetricRepository.
"""
from __future__ import annotations

import logging

import pytest

from app.services.metric_rule_validator import (
    summarize_validation_warnings,
    validate_v2_scoring_rules,
)


# ---------- the seed ruleset (met_1 shape, known good) ----------

GOOD_V2_MET_1_SHAPE = {
    "id": "met_1",
    "direction": "higher_better",
    "max_score": 20,
    "max_score_basis": "MAX_VALUE",
    "scoring_rules": {
        "version": 2,
        "input": {"kind": "number"},
        "scoring": {
            "mode": "first_match",
            "rules": [
                {"when": {"op": "lt", "value": 15}, "then": {"assign": 5}},
                {"when": {"range": {"min": 15, "max": 30}}, "then": {"assign": 10}},
                {"when": {"op": "gt", "value": 30}, "then": {"assign": 20}},
            ],
        },
        "normalization": {"basis": "max_score", "value": 20},
    },
}


# ---------- validator tests ----------

def test_validator_accepts_well_formed_v2_rules() -> None:
    issues = validate_v2_scoring_rules(
        GOOD_V2_MET_1_SHAPE["scoring_rules"], strict=True, metric=GOOD_V2_MET_1_SHAPE
    )
    assert issues == []


def test_validator_does_not_run_on_v1_list_shaped_rules() -> None:
    v1_rules = [
        {"points": 5, "condition": {"operator": "lt", "value": 15}},
        {"points": 10, "condition": {"operator": "and", "min": 15, "max": 30}},
    ]
    assert validate_v2_scoring_rules(v1_rules, strict=True) == []


def test_validator_rejects_unknown_mode() -> None:
    rules = {
        "version": 2,
        "scoring": {"mode": "weighted_average", "rules": [{"when": {"op": "gte", "value": 0}, "then": {"assign": 1}}]},
        "normalization": {"basis": "max_score", "value": 1},
    }
    issues = validate_v2_scoring_rules(rules, strict=True)
    assert any("unknown_mode" in issue and "weighted_average" in issue for issue in issues)


def test_validator_rejects_unknown_basis() -> None:
    rules = {
        "version": 2,
        "scoring": {"mode": "first_match", "rules": [{"when": {"op": "gte", "value": 0}, "then": {"assign": 1}}]},
        "normalization": {"basis": "median", "value": 1},
    }
    issues = validate_v2_scoring_rules(rules, strict=True)
    assert any("unknown_basis" in issue and "median" in issue for issue in issues)


def test_validator_rejects_unknown_action() -> None:
    rules = {
        "version": 2,
        "scoring": {
            "mode": "first_match",
            "rules": [
                {"when": {"op": "gte", "value": 0}, "then": {"percentile": 0.5}}
            ],
        },
        "normalization": {"basis": "max_score", "value": 1},
    }
    issues = validate_v2_scoring_rules(rules, strict=True)
    assert any("unknown_action" in issue and "percentile" in issue for issue in issues)


def test_validator_flags_per_unit_without_points_per_unit() -> None:
    rules = {
        "version": 2,
        "scoring": {"mode": "per_unit", "rules": []},
        "normalization": {"basis": "max_score", "value": 1},
    }
    issues = validate_v2_scoring_rules(rules, strict=True)
    assert any("per_unit_missing_points_per_unit" in issue for issue in issues)


def test_validator_flags_empty_rules_without_fallback() -> None:
    rules = {
        "version": 2,
        "scoring": {"mode": "first_match", "rules": []},
        "normalization": {"basis": "max_score", "value": 1},
    }
    issues = validate_v2_scoring_rules(rules, strict=True)
    assert any("empty_rules_without_fallback" in issue for issue in issues)


def test_validator_flags_v1_only_predicate_in_v2_rule_as_warning() -> None:
    """A v2 rule with a v1-only `description` key should warn, not error."""
    rules = {
        "version": 2,
        "scoring": {
            "mode": "first_match",
            "rules": [
                {"when": {"description": "high"}, "then": {"assign": 1}}
            ],
        },
        "normalization": {"basis": "max_score", "value": 1},
    }
    issues = validate_v2_scoring_rules(rules, strict=True)
    assert any("v1_predicate_in_v2_rules" in issue for issue in issues)
    # v1-only predicate is a WARN, not an ERROR — must not block
    assert all(not issue.startswith("[ERROR]") for issue in issues if "v1_predicate_in_v2_rules" in issue)


def test_validator_flags_legacy_max_score_basis_as_warning() -> None:
    rules = {
        "version": 2,
        "scoring": {"mode": "first_match", "rules": [{"when": {"op": "gte", "value": 0}, "then": {"assign": 1}}]},
        "normalization": {"basis": "max_score", "value": 1},
    }
    metric = {"id": "met_x", "max_score_basis": "MAX_RVALUE"}
    issues = validate_v2_scoring_rules(rules, strict=True, metric=metric)
    assert any("max_basis_uppercase_legacy" in issue for issue in issues)


# ---------- summarize_validation_warnings tests ----------

def test_summarize_validation_warnings_only_returns_error_pairs() -> None:
    metrics = [
        # bad: unknown action
        {
            "id": "met_bad_1",
            "scoring_rules": {
                "version": 2,
                "scoring": {
                    "mode": "first_match",
                    "rules": [{"when": {"op": "gte", "value": 0}, "then": {"weird": 1}}],
                },
                "normalization": {"basis": "max_score", "value": 1},
            },
        },
        # bad: unknown basis
        {
            "id": "met_bad_2",
            "scoring_rules": {
                "version": 2,
                "scoring": {
                    "mode": "first_match",
                    "rules": [{"when": {"op": "gte", "value": 0}, "then": {"assign": 1}}],
                },
                "normalization": {"basis": "median", "value": 1},
            },
        },
        # good: clean v2
        GOOD_V2_MET_1_SHAPE,
        # v1 list — out of scope, must not appear
        {
            "id": "met_v1",
            "scoring_rules": [
                {"points": 5, "condition": {"operator": "lt", "value": 10}}
            ],
        },
    ]

    findings = summarize_validation_warnings(metrics)
    ids = [pair[0] for pair in findings]

    # Both bad v2 metrics appear; the good one and the v1 list do not.
    assert "met_bad_1" in ids
    assert "met_bad_2" in ids
    assert "met_1" not in ids
    assert "met_v1" not in ids
    # Each entry is (metric_id, issue_code) with no [ERROR] tag
    for _, issue in findings:
        assert not issue.startswith("[ERROR]")
        assert "[" not in issue


def test_metric_repository_list_metrics_emits_validation_warnings_on_first_read(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Drive the MetricRepository read-time hook: the first list_metrics() call
    must emit one warning per bad v2 metric, and no warnings on subsequent calls.
    """
    from app.storage.metric_repository import MetricRepository

    repo = MetricRepository()

    # Seed a known-bad metric directly into the in-memory store for the repo's namespace.
    bad_metric = {
        "id": "met_runtime_bad",
        "scoring_rules": {
            "version": 2,
            "scoring": {
                "mode": "first_match",
                "rules": [{"when": {"op": "gte", "value": 0}, "then": {"not_a_real_action": 1}}],
            },
            "normalization": {"basis": "max_score", "value": 1},
        },
    }
    # Use the protected namespace attribute the same way the test suite already does.
    repo._memory_stores[repo._namespace].append(bad_metric)
    # Reset the per-namespace "validation already ran" flag for this repo instance.
    MetricRepository._validation_done.discard(repo._namespace)

    with caplog.at_level(logging.WARNING, logger="swaif.metrics"):
        first = repo.list_metrics()
        second = repo.list_metrics()

    assert any(m["id"] == "met_runtime_bad" for m in first)
    warning_lines = [record for record in caplog.records if "metric_rule_validation_warning" in record.getMessage()]
    assert len(warning_lines) == 1
    assert "met_runtime_bad" in warning_lines[0].getMessage()
    assert "unknown_action" in warning_lines[0].getMessage()
    # The second call did not add a new warning (one-shot hook).
    assert len(caplog.records) == 1

    # Cleanup so the test does not leak the flag to other tests in the same process.
    MetricRepository._validation_done.discard(repo._namespace)
