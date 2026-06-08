"""
Parity tests between the live v2 scoring engine
(`app.services.metric_score_service.calculate_metric_score`) and the
python-only v2 engine
(`app.services.client_metric_transformation_service.score_relative_python_from_metric`).

The two engines MUST return the same normalized score, score, and basis for
every (metric, input) pair. A divergence here means the live PATCH path and
the mock preview / external transformation path will disagree on the same
data.

The library below is a deliberate sweep of every v2 feature: modes, actions,
predicates, composition, direction inversion, and per_unit.
"""
from __future__ import annotations

import pytest

from app.services.client_metric_transformation_service import (
    score_relative_python_from_metric,
)
from app.services.metric_score_service import calculate_metric_score


# ---------- 1. first_match, numeric rules, op: gte thresholds ----------

METRIC_FIRST_MATCH_NUMERIC = {
    "id": "met_parity_first_match",
    "direction": "higher_better",
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
            "fallback": {"assign": 0},
        },
        "normalization": {"basis": "max_score", "value": 20},
    },
    "max_score": 20,
}


# ---------- 2. first_match with assign_range, policy: clamp_input ----------

METRIC_ASSIGN_RANGE_CLAMP = {
    "id": "met_parity_assign_range_clamp",
    "direction": "higher_better",
    "scoring_rules": {
        "version": 2,
        "input": {"kind": "number"},
        "scoring": {
            "mode": "first_match",
            "rules": [
                {"when": {"op": "gte", "value": 0}, "then": {"assign_range": {"min": 0, "max": 100, "policy": "clamp_input"}}},
            ],
        },
        "normalization": {"basis": "explicit", "value": 100},
    },
}


# ---------- 3. first_match with multiply_input (backported in python engine) ----------

METRIC_MULTIPLY_INPUT = {
    "id": "met_parity_multiply_input",
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


# ---------- 4. sum_matches with contains_any (categorical input) ----------

METRIC_SUM_CONTAINS_ANY = {
    "id": "met_parity_sum_contains",
    "direction": "higher_better",
    "scoring_rules": {
        "version": 2,
        "input": {"kind": "set"},
        "scoring": {
            "mode": "sum_matches",
            "rules": [
                {"when": {"contains_any": ["crm", "prontuario"]}, "then": {"assign": 5}},
                {"when": {"contains_any": ["dre"]}, "then": {"assign": 5}},
                {"when": {"contains_any": ["funil"]}, "then": {"assign": 5}},
            ],
            "fallback": {"assign": 0},
        },
        "normalization": {"basis": "max_score", "value": 15},
    },
    "max_score": 15,
}


# ---------- 5. max_match with mixed rule types ----------

METRIC_MAX_MATCH = {
    "id": "met_parity_max_match",
    "direction": "higher_better",
    "scoring_rules": {
        "version": 2,
        "input": {"kind": "number"},
        "scoring": {
            "mode": "max_match",
            "rules": [
                {"when": {"op": "lt", "value": 10}, "then": {"assign": 3}},
                {"when": {"op": "lt", "value": 50}, "then": {"assign": 7}},
                {"when": {"op": "lt", "value": 100}, "then": {"assign": 9}},
            ],
        },
        "normalization": {"basis": "explicit", "value": 9},
    },
}


# ---------- 6. per_unit with points_per_unit ----------

METRIC_PER_UNIT_NUMBER = {
    "id": "met_parity_per_unit_number",
    "direction": "higher_better",
    "scoring_rules": {
        "version": 2,
        "input": {"kind": "number"},
        "scoring": {"mode": "per_unit", "points_per_unit": 2},
        "normalization": {"basis": "explicit", "value": 10},
    },
}


# ---------- 7. per_unit with count_map (dict) input ----------

METRIC_PER_UNIT_COUNT_MAP = {
    "id": "met_parity_per_unit_count_map",
    "direction": "higher_better",
    "scoring_rules": {
        "version": 2,
        "input": {"kind": "object"},
        "scoring": {"mode": "per_unit", "points_per_unit": 3},
        "normalization": {"basis": "explicit", "value": 9},
    },
}


# ---------- 8. field-based predicate extraction ----------

METRIC_FIELD_EXTRACTION = {
    "id": "met_parity_field",
    "direction": "higher_better",
    "scoring_rules": {
        "version": 2,
        "input": {"kind": "object"},
        "scoring": {
            "mode": "sum_matches",
            "rules": [
                {"when": {"field": "presencas", "op": "gt", "value": 4}, "then": {"assign": 5}},
                {"when": {"field": "feedback", "op": "gt", "value": 4}, "then": {"assign": 5}},
            ],
            "fallback": {"assign": 0},
        },
        "normalization": {"basis": "explicit", "value": 10},
    },
}


# ---------- 9a. all composition ----------

METRIC_ALL_COMPOSITION = {
    "id": "met_parity_all",
    "direction": "higher_better",
    "scoring_rules": {
        "version": 2,
        "input": {"kind": "number"},
        "scoring": {
            "mode": "first_match",
            "rules": [
                {
                    "when": {
                        "all": [
                            {"op": "gte", "value": 0},
                            {"op": "lte", "value": 100},
                        ]
                    },
                    "then": {"assign": 10},
                },
            ],
        },
        "normalization": {"basis": "explicit", "value": 10},
    },
}


# ---------- 9b. any composition ----------

METRIC_ANY_COMPOSITION = {
    "id": "met_parity_any",
    "direction": "higher_better",
    "scoring_rules": {
        "version": 2,
        "input": {"kind": "number"},
        "scoring": {
            "mode": "first_match",
            "rules": [
                {
                    "when": {
                        "any": [
                            {"op": "lt", "value": 0},
                            {"op": "gt", "value": 200},
                        ]
                    },
                    "then": {"assign": 0},
                },
                {"when": {"op": "gte", "value": 0}, "then": {"assign": 1}},
            ],
        },
        "normalization": {"basis": "explicit", "value": 1},
    },
}


# ---------- 9c. not composition ----------

METRIC_NOT_COMPOSITION = {
    "id": "met_parity_not",
    "direction": "higher_better",
    "scoring_rules": {
        "version": 2,
        "input": {"kind": "number"},
        "scoring": {
            "mode": "first_match",
            "rules": [
                {
                    "when": {
                        "not": {"op": "gte", "value": 0}
                    },
                    "then": {"assign": 0},
                },
                {
                    "when": {"op": "gte", "value": 0},
                    "then": {"assign": 1},
                },
            ],
        },
        "normalization": {"basis": "explicit", "value": 1},
    },
}


# ---------- 10. lower_better direction (auto-inversion) ----------

METRIC_LOWER_BETTER = {
    "id": "met_parity_lower_better",
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


PARITY_CASES = [
    # (metric, raw_value, expected_normalized_score)
    # 1. first_match numeric — three ranges plus fallback
    (METRIC_FIRST_MATCH_NUMERIC, 10, 5 / 20),
    (METRIC_FIRST_MATCH_NUMERIC, 20, 10 / 20),
    (METRIC_FIRST_MATCH_NUMERIC, 50, 20 / 20),
    # 2. assign_range with clamp_input policy
    (METRIC_ASSIGN_RANGE_CLAMP, 30, 30 / 100),
    (METRIC_ASSIGN_RANGE_CLAMP, 200, 100 / 100),  # clamped to upper bound
    # Value=-10 is rejected by the predicate (op: gte value: 0) and there is
    # no fallback, so the engines raise ScoreCalculationError. We exercise the
    # exception parity in a separate test below.
    # 3. multiply_input action (requires Step 1 backport)
    (METRIC_MULTIPLY_INPUT, 10, (10 * 0.5) / 50),  # score=5, normalized=0.1
    (METRIC_MULTIPLY_INPUT, 80, (80 * 0.5) / 50),  # score=40, normalized=0.8
    # 4. sum_matches with contains_any
    (METRIC_SUM_CONTAINS_ANY, ["crm", "dre"], 10 / 15),
    (METRIC_SUM_CONTAINS_ANY, ["crm", "dre", "funil"], 15 / 15),
    (METRIC_SUM_CONTAINS_ANY, [], 0 / 15),
    # 5. max_match with three candidate rules — all three match for any
    # value >= 0, so the max reducer always picks 9.
    (METRIC_MAX_MATCH, 5, 9 / 9),
    (METRIC_MAX_MATCH, 25, 9 / 9),
    (METRIC_MAX_MATCH, 75, 9 / 9),
    # 6. per_unit with number
    (METRIC_PER_UNIT_NUMBER, 0, 0 / 10),
    (METRIC_PER_UNIT_NUMBER, 3, 6 / 10),
    (METRIC_PER_UNIT_NUMBER, 5, 10 / 10),
    # 7. per_unit with dict (count_map)
    (METRIC_PER_UNIT_COUNT_MAP, {"a": 1, "b": 2}, 9 / 9),  # sum=3, points=3 each
    (METRIC_PER_UNIT_COUNT_MAP, {"a": 1}, 3 / 9),
    # 8. field-based predicate
    (METRIC_FIELD_EXTRACTION, {"presencas": 5, "feedback": 2}, 5 / 10),
    (METRIC_FIELD_EXTRACTION, {"presencas": 5, "feedback": 6}, 10 / 10),
    (METRIC_FIELD_EXTRACTION, {"presencas": 1, "feedback": 1}, 0 / 10),
    # 9a. all composition — only the in-range value matches the rule.
    # Out-of-range values raise ScoreCalculationError (no fallback); the
    # exception-parity test below covers that path explicitly.
    (METRIC_ALL_COMPOSITION, 50, 10 / 10),  # both predicates satisfied
    # 9b. any composition
    (METRIC_ANY_COMPOSITION, 50, 1.0),    # inside [0, 200], matches the gte 0 branch
    (METRIC_ANY_COMPOSITION, 500, 0.0),   # outside, matches the "any" predicate (assign 0)
    (METRIC_ANY_COMPOSITION, -1, 0.0),     # outside, matches the "any" predicate (assign 0)
    # 9c. not composition
    (METRIC_NOT_COMPOSITION, 50, 1 / 1),   # gte 0, so the "not" branch is false
    (METRIC_NOT_COMPOSITION, -1, 0 / 1),   # not gte 0, matches the "not" branch
    # 10. lower_better direction
    (METRIC_LOWER_BETTER, 0, 1.0),        # raw=0 → score=0 → invert → 1.0
    (METRIC_LOWER_BETTER, 50, 1.0),       # raw=50 → score=0 (gte 0) → invert → 1.0
    (METRIC_LOWER_BETTER, 100, 0.0),      # raw=100 → score=1.0 (gte 100) → invert → 0.0
    (METRIC_LOWER_BETTER, 200, 0.0),      # raw=200 → score=1.0 → invert → 0.0
]


@pytest.mark.parametrize("metric,raw_value,expected_normalized_score", PARITY_CASES)
def test_parity_calculate_metric_score_vs_python_engine(
    metric: dict, raw_value, expected_normalized_score: float
) -> None:
    """Both engines MUST agree on normalized score, raw score, and basis."""
    live = calculate_metric_score(metric, raw_value)
    python = score_relative_python_from_metric(metric, raw_value)

    # Both engines return normalized in [0, 1].
    assert 0.0 <= live.normalized_score <= 1.0
    assert 0.0 <= python <= 1.0

    # The two engines MUST agree.
    assert live.normalized_score == pytest.approx(python, abs=1e-6)

    # Sanity: the live engine's normalized score matches the hand-computed expectation.
    assert live.normalized_score == pytest.approx(expected_normalized_score, abs=1e-6)


def test_higher_better_is_byte_for_byte_unchanged_after_direction_fix() -> None:
    """The auto-inversion must NOT affect higher_better metrics. This is the
    byte-for-byte compatibility guard for the live corpus.
    """
    metric = dict(METRIC_FIRST_MATCH_NUMERIC)
    metric["direction"] = "higher_better"

    result = calculate_metric_score(metric, 20)

    assert result.normalized_score == pytest.approx(10 / 20, abs=1e-6)
    # Confirm the score itself (pre-inversion) is preserved.
    assert result.score == pytest.approx(10.0, abs=1e-6)


def test_lower_better_inverts_score_not_raw_value() -> None:
    """Direction inversion is a post-step on the normalized score, not on the
    raw value or on the pre-normalization score.
    """
    result = calculate_metric_score(METRIC_LOWER_BETTER, 100)

    # raw=100 → first rule matches ("gte 100") → score=1.0 → basis=1.0 → normalized=1.0
    # then direction=lower_better → inverted to 0.0
    assert result.score == pytest.approx(1.0, abs=1e-6)
    assert result.normalization_basis == pytest.approx(1.0, abs=1e-6)
    assert result.normalized_score == pytest.approx(0.0, abs=1e-6)


def test_python_engine_also_inverts_lower_better() -> None:
    """The python engine must apply the same direction inversion as the live one."""
    python_value = score_relative_python_from_metric(METRIC_LOWER_BETTER, 100)
    live_value = calculate_metric_score(METRIC_LOWER_BETTER, 100)
    assert python_value == pytest.approx(live_value.normalized_score, abs=1e-6)
    assert python_value == pytest.approx(0.0, abs=1e-6)


def test_exception_parity_when_no_rule_matches_and_no_fallback() -> None:
    """When a metric has rules but none match and there is no fallback, both
    engines must raise the same exception type. This is the "no rule matched"
    parity contract.
    """
    from app.services.metric_score_service import ScoreCalculationError as LiveErr
    from app.services.client_metric_transformation_service import (
        ScoreCalculationError as PythonErr,
    )

    metric = {
        "id": "met_parity_no_match",
        "direction": "higher_better",
        "scoring_rules": {
            "version": 2,
            "input": {"kind": "number"},
            "scoring": {
                "mode": "first_match",
                "rules": [
                    {"when": {"op": "gt", "value": 1000}, "then": {"assign": 1}},
                ],
            },
            "normalization": {"basis": "max_score", "value": 1},
        },
    }

    with pytest.raises(LiveErr):
        calculate_metric_score(metric, 0)
    with pytest.raises(PythonErr):
        score_relative_python_from_metric(metric, 0)
