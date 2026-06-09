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


def test_calculate_metric_score_v2_lower_better_inverts_normalized_only() -> None:
    """`lower_better` flips the normalized score (1 - score / basis) but leaves
    the pre-normalization `score` untouched. This is the byte-for-byte
    contract for the direction policy.
    """
    metric = {
        "score_type": "static",
        "max_score": 1.0,
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

    # high raw input → score=1.0 → inverted to 0.0
    high = calculate_metric_score(metric, 200)
    assert high.score == pytest.approx(1.0, abs=1e-6)
    assert high.normalized_score == pytest.approx(0.0, abs=1e-6)

    # low raw input → score=0.0 → inverted to 1.0
    low = calculate_metric_score(metric, 0)
    assert low.score == pytest.approx(0.0, abs=1e-6)
    assert low.normalized_score == pytest.approx(1.0, abs=1e-6)


def test_calculate_metric_score_v2_higher_better_unaffected_by_direction_fix() -> None:
    """The auto-inversion must be a no-op for `higher_better` and missing
    `direction` (defaults to higher_better). This is the byte-for-byte
    compatibility guard for the live corpus.
    """
    base_metric = {
        "score_type": "static",
        "max_score": 20,
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "number"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {"when": {"range": {"min": 15, "max": 30}}, "then": {"assign": 10}},
                ],
            },
            "normalization": {"basis": "max_score", "value": 20},
        },
    }

    higher = dict(base_metric, direction="higher_better")
    missing = dict(base_metric)  # no direction key

    assert calculate_metric_score(higher, 20).normalized_score == pytest.approx(10 / 20, abs=1e-6)
    assert calculate_metric_score(missing, 20).normalized_score == pytest.approx(10 / 20, abs=1e-6)


def test_calculate_metric_score_v2_multiply_input_action_supported() -> None:
    """The v2 `multiply_input` action returns raw * factor as the score."""
    metric = {
        "score_type": "static",
        "max_score": 50,
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

    result = calculate_metric_score(metric, 80)

    assert result.score == pytest.approx(40.0, abs=1e-6)  # 80 * 0.5
    assert result.normalization_basis == pytest.approx(50.0, abs=1e-6)
    assert result.normalized_score == pytest.approx(0.8, abs=1e-6)


# ---------- Commit 1: isolated v2 branch coverage ----------


def test_calculate_metric_score_v2_max_match_picks_largest_match() -> None:
    """v2 `max_match` mode returns the largest action score among all
    matching rules, not the first. Three rules, two or three match —
    the largest of the matched ones must win. Direct test of the
    `max_match` branch in `_calculate_metric_score_v2` that the
    parity sweep exercises but the unit file did not.
    """
    metric = {
        "score_type": "static",
        "max_score": 20,
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "number"},
            "scoring": {
                "mode": "max_match",
                "rules": [
                    {"when": {"op": "gte", "value": 0}, "then": {"assign": 3}},
                    {"when": {"op": "lt", "value": 50}, "then": {"assign": 7}},
                    {"when": {"op": "lt", "value": 10}, "then": {"assign": 9}},
                ],
            },
            "normalization": {"basis": "explicit", "value": 9},
        },
    }

    # raw=25 matches rules 0 and 1; max(3, 7) = 7.
    result = calculate_metric_score(metric, 25)
    assert result.score == pytest.approx(7.0, abs=1e-6)
    assert result.normalized_score == pytest.approx(7 / 9, abs=1e-6)

    # raw=5 matches all three; max(3, 7, 9) = 9.
    result_low = calculate_metric_score(metric, 5)
    assert result_low.score == pytest.approx(9.0, abs=1e-6)
    assert result_low.normalized_score == pytest.approx(1.0, abs=1e-6)


def test_calculate_metric_score_v2_fallback_fires_when_no_rule_matches() -> None:
    """When no rule matches and a `fallback` action is configured, the
    fallback is evaluated instead of raising ScoreCalculationError.
    Regression guard for the fallback branch in
    `_calculate_metric_score_v2`.
    """
    metric = {
        "score_type": "static",
        "max_score": 10,
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "number"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {"when": {"op": "gt", "value": 1000}, "then": {"assign": 1}},
                ],
                "fallback": {"assign": 5},
            },
            "normalization": {"basis": "max_score", "value": 10},
        },
    }

    result = calculate_metric_score(metric, 0)

    assert result.score == pytest.approx(5.0, abs=1e-6)
    assert result.normalized_score == pytest.approx(0.5, abs=1e-6)
    assert result.matched_rule_indexes == ()


def test_calculate_metric_score_v2_assign_range_policy_min_returns_lower_bound() -> None:
    """`assign_range` with `policy: "min"` returns the smaller of the
    two bounds, ignoring the raw value. Symmetric twin of the default
    `policy: "max"`. Untouched by the parity sweep.
    """
    metric = {
        "score_type": "static",
        "max_score": 10,
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "number"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {"when": {"op": "gte", "value": 0}, "then": {"assign_range": {"min": 2, "max": 8, "policy": "min"}}},
                ],
            },
            "normalization": {"basis": "explicit", "value": 8},
        },
    }

    # raw=100 is above max, but policy=min ignores raw and returns the lower bound.
    result = calculate_metric_score(metric, 100)
    assert result.score == pytest.approx(2.0, abs=1e-6)
    assert result.normalization_basis == pytest.approx(8.0, abs=1e-6)
    assert result.normalized_score == pytest.approx(0.25, abs=1e-6)


def test_calculate_metric_score_v2_assign_range_clamp_input_raises_on_non_numeric_raw() -> None:
    """`assign_range` with `policy: "clamp_input"` requires a numeric
    raw value; a list that does not coerce to float must raise
    `ScoreCalculationError` rather than silently returning a bound.

    The rule's `contains` predicate is what lets the list reach the
    action layer; without it, the rule would never match and the
    engine would raise 'no scoring rule matched' instead.
    """
    from app.services.metric_score_service import ScoreCalculationError

    metric = {
        "score_type": "static",
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "set"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {"when": {"contains": "trigger"}, "then": {"assign_range": {"min": 0, "max": 100, "policy": "clamp_input"}}},
                ],
            },
            "normalization": {"basis": "explicit", "value": 100},
        },
    }

    with pytest.raises(ScoreCalculationError, match="clamp_input requires numeric raw value"):
        calculate_metric_score(metric, ["trigger"])


def test_calculate_metric_score_v2_contains_singular_matches_list_member() -> None:
    """`contains` (singular) on a list raw value should match if any
    element of the list equals the expected value (after normalization).
    Distinct from `contains_any` which iterates the expected list.
    """
    metric = {
        "score_type": "static",
        "max_score": 10,
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "set"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {"when": {"contains": "medical_record"}, "then": {"assign": 10}},
                ],
            },
            "normalization": {"basis": "max_score", "value": 10},
        },
    }

    result = calculate_metric_score(metric, ["other", "medical_record", "third"])
    assert result.score == pytest.approx(10.0, abs=1e-6)
    assert result.normalized_score == pytest.approx(1.0, abs=1e-6)
    assert result.matched_rule_indexes == (0,)


def test_calculate_metric_score_v2_range_exclusive_inclusive_min() -> None:
    """`range` with `inclusive_min: False` excludes the lower bound.
    A raw value equal to min must NOT match; min+1 must.
    """
    metric = {
        "score_type": "static",
        "max_score": 10,
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "number"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {"when": {"range": {"min": 10, "max": 20, "inclusive_min": False}}, "then": {"assign": 5}},
                ],
                "fallback": {"assign": 0},
            },
            "normalization": {"basis": "max_score", "value": 10},
        },
    }

    boundary = calculate_metric_score(metric, 10)
    assert boundary.matched_rule_indexes == ()
    assert boundary.score == pytest.approx(0.0, abs=1e-6)

    inside = calculate_metric_score(metric, 11)
    assert inside.score == pytest.approx(5.0, abs=1e-6)
    assert inside.matched_rule_indexes == (0,)


def test_calculate_metric_score_v2_range_with_only_min_bound() -> None:
    """A `range` with only `min` (no `max`) accepts any value >= min.
    A value below min does not match (and falls through to the
    fallback). Regression guard for the
    `minimum is not None or maximum is not None` final return in
    `_matches_range`.
    """
    metric = {
        "score_type": "static",
        "max_score": 10,
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "number"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {"when": {"range": {"min": 10}}, "then": {"assign": 4}},
                ],
                "fallback": {"assign": 0},
            },
            "normalization": {"basis": "max_score", "value": 10},
        },
    }

    assert calculate_metric_score(metric, 15).matched_rule_indexes == (0,)
    assert calculate_metric_score(metric, 10).matched_rule_indexes == (0,)  # boundary inclusive
    assert calculate_metric_score(metric, 5).matched_rule_indexes == ()    # below min → fallback


def test_calculate_metric_score_v2_field_extraction_falls_back_when_raw_is_not_dict() -> None:
    """When `field` is set in the predicate but the raw value is not
    a dict, `_extract_subject` returns the raw value itself. This is
    the regression guard for the `isinstance(raw_value, dict)` check
    in `_extract_subject`.
    """
    metric = {
        "score_type": "static",
        "max_score": 10,
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "number"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {"when": {"field": "presencas", "op": "gt", "value": 4}, "then": {"assign": 5}},
                ],
                "fallback": {"assign": 0},
            },
            "normalization": {"basis": "max_score", "value": 10},
        },
    }

    # 5 > 4 → match (the `field` is set but the raw is not a dict; subject falls back to 5).
    assert calculate_metric_score(metric, 5).matched_rule_indexes == (0,)
    # 3 > 4 → no match → fallback
    assert calculate_metric_score(metric, 3).matched_rule_indexes == ()


def test_calculate_metric_score_v2_basis_explicit_with_zero_value_falls_through() -> None:
    """`normalization.basis: "explicit"` with `value: 0` does NOT
    short-circuit; the resolver falls through to the metric's
    `max_score`. Guards the `> 0` guard on the explicit branch in
    `_resolve_v2_normalization_basis`.
    """
    metric = {
        "score_type": "static",
        "max_score": 20,
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "number"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {"when": {"op": "gte", "value": 0}, "then": {"assign": 5}},
                ],
            },
            "normalization": {"basis": "explicit", "value": 0},
        },
    }

    result = calculate_metric_score(metric, 1)
    assert result.normalization_basis == pytest.approx(20.0, abs=1e-6)
    assert result.normalized_score == pytest.approx(5 / 20, abs=1e-6)


def test_calculate_metric_score_v2_basis_mcv_with_missing_mcv_falls_through_to_max_score() -> None:
    """`normalization.basis: "mcv"` with no `mcv` on the metric falls
    through to the v1-style `_resolve_normalization_basis` and
    ultimately returns `max_score`. Guards the
    `mcv is not None and mcv > 0` short-circuit on the mcv branch.
    """
    metric = {
        "score_type": "static",
        "max_score": 30,
        # intentionally no mcv / mcv_score on the metric
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "number"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {"when": {"op": "gte", "value": 0}, "then": {"assign": 6}},
                ],
            },
            "normalization": {"basis": "mcv", "value": 0},
        },
    }

    result = calculate_metric_score(metric, 1)
    assert result.normalization_basis == pytest.approx(30.0, abs=1e-6)
    assert result.normalized_score == pytest.approx(6 / 30, abs=1e-6)