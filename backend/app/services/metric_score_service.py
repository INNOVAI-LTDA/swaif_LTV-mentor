from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ScoreCalculationError(ValueError):
    pass


@dataclass(frozen=True)
class MetricScoreResult:
    raw_value: Any
    score: float
    normalized_score: float
    normalization_basis: float
    matched_rule_indexes: tuple[int, ...]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        normalized = value.strip().replace("R$", "").replace("%", "")
        normalized = normalized.replace(".", "").replace(",", ".") if "," in normalized else normalized
        try:
            return float(normalized)
        except ValueError:
            return None
    return None


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _normalize_sequence(values: list[Any] | tuple[Any, ...] | set[Any]) -> list[str]:
    return [_normalize_text(value) for value in values]


def _text_equals(left: Any, right: Any) -> bool:
    left_num = _coerce_float(left)
    right_num = _coerce_float(right)
    if left_num is not None and right_num is not None:
        return left_num == right_num
    return _normalize_text(left) == _normalize_text(right)


def _matches_description(description: str, raw_value: Any) -> bool:
    normalized_description = _normalize_text(description)
    if not normalized_description:
        return False

    if isinstance(raw_value, dict):
        for key, value in raw_value.items():
            if _normalize_text(key) != normalized_description:
                continue
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return float(value) > 0
            return bool(value)
        return False

    if isinstance(raw_value, (list, tuple, set)):
        return any(_normalize_text(item) == normalized_description for item in raw_value)

    if isinstance(raw_value, str):
        normalized_raw = _normalize_text(raw_value)
        if normalized_raw == normalized_description:
            return True
        tokens = [token.strip() for token in normalized_raw.replace(";", ",").split(",") if token.strip()]
        return normalized_description in tokens

    return False


def _extract_subject(raw_value: Any, predicate: dict[str, Any]) -> Any:
    field_name = predicate.get("field")
    if field_name is not None and isinstance(raw_value, dict):
        return raw_value.get(str(field_name))
    return raw_value


def _matches_contains(expected: Any, raw_value: Any) -> bool:
    normalized_expected = _normalize_text(expected)
    if not normalized_expected:
        return False

    if isinstance(raw_value, dict):
        for key, value in raw_value.items():
            if _normalize_text(key) != normalized_expected:
                continue
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return float(value) > 0
            return bool(value)
        return False

    if isinstance(raw_value, (list, tuple, set)):
        return normalized_expected in _normalize_sequence(raw_value)

    return _normalize_text(raw_value) == normalized_expected


def _matches_range(range_definition: dict[str, Any], raw_value: Any) -> bool:
    raw_number = _coerce_float(raw_value)
    if raw_number is None:
        return False

    minimum = _coerce_float(range_definition.get("min"))
    maximum = _coerce_float(range_definition.get("max"))
    inclusive_min = bool(range_definition.get("inclusive_min", True))
    inclusive_max = bool(range_definition.get("inclusive_max", True))

    if minimum is not None:
        if inclusive_min and raw_number < minimum:
            return False
        if not inclusive_min and raw_number <= minimum:
            return False

    if maximum is not None:
        if inclusive_max and raw_number > maximum:
            return False
        if not inclusive_max and raw_number >= maximum:
            return False

    return minimum is not None or maximum is not None


def _matches_predicate(predicate: dict[str, Any], raw_value: Any) -> bool:
    if not predicate:
        return False

    if "all" in predicate:
        entries = predicate.get("all") or []
        return all(isinstance(entry, dict) and _matches_predicate(entry, raw_value) for entry in entries)

    if "any" in predicate:
        entries = predicate.get("any") or []
        return any(isinstance(entry, dict) and _matches_predicate(entry, raw_value) for entry in entries)

    if "not" in predicate:
        nested = predicate.get("not")
        return isinstance(nested, dict) and not _matches_predicate(nested, raw_value)

    subject = _extract_subject(raw_value, predicate)

    if "contains" in predicate:
        return _matches_contains(predicate.get("contains"), subject)

    if "contains_any" in predicate:
        values = predicate.get("contains_any") or []
        return any(_matches_contains(value, subject) for value in values)

    if "range" in predicate and isinstance(predicate.get("range"), dict):
        return _matches_range(predicate["range"], subject)

    if "op" in predicate:
        return _condition_matches(predicate, subject)

    return False


def _condition_matches(condition: dict[str, Any], raw_value: Any) -> bool:
    operator = _normalize_text(condition.get("operator") or condition.get("op"))
    if not operator:
        description = str(condition.get("description") or "")
        return _matches_description(description, raw_value)

    if operator in {"eq", "="}:
        return _text_equals(raw_value, condition.get("value"))

    raw_number = _coerce_float(raw_value)
    if raw_number is None:
        return False

    if operator == "and":
        minimum = _coerce_float(condition.get("min"))
        maximum = _coerce_float(condition.get("max"))
        if minimum is not None and raw_number < minimum:
            return False
        if maximum is not None and raw_number > maximum:
            return False
        return minimum is not None or maximum is not None

    if operator == "range":
        return _matches_range(
            {
                "min": condition.get("min"),
                "max": condition.get("max"),
                "inclusive_min": condition.get("inclusive_min", True),
                "inclusive_max": condition.get("inclusive_max", True),
            },
            raw_value,
        )
    if operator == "lt":
        expected = _coerce_float(condition.get("value"))
        return expected is not None and raw_number < expected
    if operator == "lte":
        expected = _coerce_float(condition.get("value"))
        return expected is not None and raw_number <= expected
    if operator == "gt":
        expected = _coerce_float(condition.get("value"))
        return expected is not None and raw_number > expected
    if operator == "gte":
        expected = _coerce_float(condition.get("value"))
        return expected is not None and raw_number >= expected

    return False


def _evaluate_assign_range(action: dict[str, Any], raw_value: Any) -> float:
    minimum = _coerce_float(action.get("min"))
    maximum = _coerce_float(action.get("max"))
    if minimum is None or maximum is None:
        raise ScoreCalculationError("assign_range requires numeric min and max")

    lower = min(minimum, maximum)
    upper = max(minimum, maximum)
    policy = _normalize_text(action.get("policy") or "max")
    if policy == "min":
        return lower
    if policy == "clamp_input":
        numeric_raw = _coerce_float(raw_value)
        if numeric_raw is None:
            raise ScoreCalculationError("assign_range clamp_input requires numeric raw value")
        return max(lower, min(upper, numeric_raw))
    return upper


def _evaluate_action(action: dict[str, Any], raw_value: Any) -> float:
    if "assign" in action:
        assigned = _coerce_float(action.get("assign"))
        if assigned is None:
            raise ScoreCalculationError("assign action requires numeric value")
        return assigned

    if "assign_range" in action and isinstance(action.get("assign_range"), dict):
        return _evaluate_assign_range(action["assign_range"], raw_value)

    if "multiply_input" in action:
        factor = _coerce_float(action.get("multiply_input"))
        numeric_raw = _coerce_float(raw_value)
        if factor is None or numeric_raw is None:
            raise ScoreCalculationError("multiply_input requires numeric factor and raw value")
        return numeric_raw * factor

    raise ScoreCalculationError("unsupported v2 action")


def _resolve_v2_per_unit_quantity(raw_value: Any) -> float:
    if isinstance(raw_value, (int, float)):
        return max(float(raw_value), 0.0)
    if isinstance(raw_value, dict):
        return max(sum(float(value) for value in raw_value.values() if isinstance(value, (int, float))), 0.0)
    raise ScoreCalculationError("per_unit requires numeric or count_map raw value")


def _extract_range_basis_from_v2(matched_rules: list[tuple[int, dict[str, Any]]]) -> float | None:
    for _, rule in matched_rules:
        action = rule.get("then")
        if not isinstance(action, dict):
            continue
        assign_range = action.get("assign_range")
        if not isinstance(assign_range, dict):
            continue
        maximum = _coerce_float(assign_range.get("max"))
        if maximum is not None and maximum > 0:
            return maximum
    return None


def _resolve_v2_normalization_basis(
    metric: dict[str, Any],
    *,
    normalization: dict[str, Any],
    matched_rules: list[tuple[int, dict[str, Any]]],
    score: float,
) -> float:
    basis = _normalize_text(normalization.get("basis") or metric.get("max_score_basis") or metric.get("max_basis_score"))
    explicit_value = _coerce_float(normalization.get("value"))
    max_score = _coerce_float(metric.get("max_score"))
    mcv = _coerce_float(metric.get("mcv") if metric.get("mcv") is not None else metric.get("mcv_score"))

    if basis == "explicit" and explicit_value is not None and explicit_value > 0:
        return explicit_value
    if basis == "mcv":
        if explicit_value is not None and explicit_value > 0:
            return explicit_value
        if mcv is not None and mcv > 0:
            return mcv
    if basis == "max_range":
        if explicit_value is not None and explicit_value > 0:
            return explicit_value
        range_basis = _extract_range_basis_from_v2(matched_rules)
        if range_basis is not None:
            return range_basis
    if basis == "max_score":
        if explicit_value is not None and explicit_value > 0:
            return explicit_value
        if max_score is not None and max_score > 0:
            return max_score

    return _resolve_normalization_basis(metric, matched_rules=matched_rules, score=score)


def _calculate_metric_score_v2(metric: dict[str, Any], raw_value: Any, definition: dict[str, Any]) -> MetricScoreResult:
    scoring = definition.get("scoring") if isinstance(definition.get("scoring"), dict) else {}
    normalization = definition.get("normalization") if isinstance(definition.get("normalization"), dict) else {}
    mode = _normalize_text(scoring.get("mode") or "first_match")

    matched_rules: list[tuple[int, dict[str, Any]]] = []

    if mode == "per_unit":
        points_per_unit = _coerce_float(scoring.get("points_per_unit"))
        if points_per_unit is None:
            raise ScoreCalculationError("per_unit scoring requires points_per_unit")
        score = _resolve_v2_per_unit_quantity(raw_value) * points_per_unit
    else:
        rules = scoring.get("rules") or []
        if not isinstance(rules, list):
            raise ScoreCalculationError("v2 scoring rules must be a list")
        matched_rules = [
            (index, rule)
            for index, rule in enumerate(rules)
            if isinstance(rule, dict) and _matches_predicate(rule.get("when") or {}, raw_value)
        ]

        if not matched_rules:
            fallback = scoring.get("fallback")
            if isinstance(fallback, dict):
                score = _evaluate_action(fallback, raw_value)
            else:
                raise ScoreCalculationError("no scoring rule matched")
        elif mode == "sum_matches":
            score = sum(_evaluate_action(rule.get("then") or {}, raw_value) for _, rule in matched_rules)
        elif mode == "max_match":
            score = max(_evaluate_action(rule.get("then") or {}, raw_value) for _, rule in matched_rules)
        else:
            first_match = matched_rules[0][1]
            score = _evaluate_action(first_match.get("then") or {}, raw_value)
            matched_rules = [matched_rules[0]]

    basis = _resolve_v2_normalization_basis(metric, normalization=normalization, matched_rules=matched_rules, score=score)
    normalized_score = 0.0 if basis <= 0 else _clamp01(score / basis)
    if _normalize_text(metric.get("direction") or "higher_better") == "lower_better":
        normalized_score = 1.0 - normalized_score
    return MetricScoreResult(
        raw_value=raw_value,
        score=round(float(score), 6),
        normalized_score=round(float(normalized_score), 6),
        normalization_basis=round(float(basis), 6),
        matched_rule_indexes=tuple(index for index, _ in matched_rules),
    )


def _rule_points(rule: dict[str, Any], raw_value: Any, *, score_type: str) -> float:
    points = _coerce_float(rule.get("points"))
    if points is not None:
        return points

    points_range = rule.get("points_range")
    if score_type == "range" and isinstance(points_range, list) and len(points_range) == 2:
        lower = _coerce_float(points_range[0])
        upper = _coerce_float(points_range[1])
        if lower is None or upper is None:
            raise ScoreCalculationError("invalid points range")
        range_min = min(lower, upper)
        range_max = max(lower, upper)
        numeric_raw = _coerce_float(raw_value)
        if numeric_raw is not None:
            return max(range_min, min(range_max, numeric_raw))
        return range_max

    raise ScoreCalculationError("rule has no supported points definition")


def _range_basis(metric: dict[str, Any], matched_rules: list[tuple[int, dict[str, Any]]]) -> float | None:
    for _, rule in matched_rules:
        points_range = rule.get("points_range")
        if isinstance(points_range, list) and len(points_range) == 2:
            upper = _coerce_float(points_range[1])
            if upper is not None and upper > 0:
                return upper
    return None


def _resolve_normalization_basis(metric: dict[str, Any], *, matched_rules: list[tuple[int, dict[str, Any]]], score: float) -> float:
    basis_mode = _normalize_text(metric.get("max_score_basis") or metric.get("max_basis_score")).upper()
    max_score = _coerce_float(metric.get("max_score"))
    mcv = _coerce_float(metric.get("mcv") if metric.get("mcv") is not None else metric.get("mcv_score"))

    if basis_mode == "MCV" and mcv is not None and mcv > 0:
        return mcv

    if basis_mode == "MAX_RVALUE":
        range_basis = _range_basis(metric, matched_rules)
        if range_basis is not None:
            return range_basis

    if max_score is not None and max_score > 0:
        return max_score

    if mcv is not None and mcv > 0:
        return mcv

    return max(score, 0.0)


def _calculate_unrestricted_sum(metric: dict[str, Any], rules: list[dict[str, Any]], raw_value: Any) -> tuple[float, tuple[int, ...]]:
    if not rules:
        raise ScoreCalculationError("unrestricted_sum requires scoring rules")

    if isinstance(raw_value, (int, float)):
        quantity = max(float(raw_value), 0.0)
        unit_points = _coerce_float(rules[0].get("points"))
        if unit_points is None:
            raise ScoreCalculationError("unrestricted_sum rule requires points")
        return quantity * unit_points, (0,)

    if isinstance(raw_value, dict):
        total = 0.0
        matched_indexes: list[int] = []
        for index, rule in enumerate(rules):
            description = str((rule.get("condition") or {}).get("description") or "")
            if not description:
                continue
            quantity = _coerce_float(raw_value.get(description))
            if quantity is None or quantity <= 0:
                continue
            points = _coerce_float(rule.get("points"))
            if points is None:
                continue
            total += quantity * points
            matched_indexes.append(index)
        return total, tuple(matched_indexes)

    if isinstance(raw_value, (list, tuple, set)):
        total = 0.0
        matched_indexes: list[int] = []
        for item in raw_value:
            for index, rule in enumerate(rules):
                if not _condition_matches(rule.get("condition") or {}, item):
                    continue
                points = _coerce_float(rule.get("points"))
                if points is None:
                    continue
                total += points
                matched_indexes.append(index)
        return total, tuple(matched_indexes)

    raise ScoreCalculationError("unsupported raw value for unrestricted_sum")


def calculate_metric_score(metric: dict[str, Any], raw_value: Any) -> MetricScoreResult:
    scoring_rules = metric.get("scoring_rules") or []

    if isinstance(scoring_rules, dict) and int(scoring_rules.get("version") or 0) == 2:
        return _calculate_metric_score_v2(metric, raw_value, scoring_rules)

    score_type = _normalize_text(metric.get("score_type") or "static")
    if not isinstance(scoring_rules, list):
        raise ScoreCalculationError("invalid scoring rules")

    if score_type == "unrestricted_sum":
        score, matched_indexes = _calculate_unrestricted_sum(metric, scoring_rules, raw_value)
        matched_rules = [(index, scoring_rules[index]) for index in matched_indexes if index < len(scoring_rules)]
    elif scoring_rules:
        matched_rules = [
            (index, rule)
            for index, rule in enumerate(scoring_rules)
            if isinstance(rule, dict) and _condition_matches(rule.get("condition") or {}, raw_value)
        ]

        if not matched_rules:
            raise ScoreCalculationError("no scoring rule matched")

        if score_type == "accumulative":
            score = sum(_rule_points(rule, raw_value, score_type=score_type) for _, rule in matched_rules)
        else:
            score = max(_rule_points(rule, raw_value, score_type=score_type) for _, rule in matched_rules)
    else:
        numeric_raw = _coerce_float(raw_value)
        if numeric_raw is None:
            raise ScoreCalculationError("metric has no scoring rules")
        score = numeric_raw
        matched_rules = []

    basis = _resolve_normalization_basis(metric, matched_rules=matched_rules, score=score)
    normalized_score = 0.0 if basis <= 0 else _clamp01(score / basis)
    if _normalize_text(metric.get("direction") or "higher_better") == "lower_better":
        normalized_score = 1.0 - normalized_score
    return MetricScoreResult(
        raw_value=raw_value,
        score=round(float(score), 6),
        normalized_score=round(float(normalized_score), 6),
        normalization_basis=round(float(basis), 6),
        matched_rule_indexes=tuple(index for index, _ in matched_rules),
    )


def calculate_measurement_score_values(metric: dict[str, Any], measurement: dict[str, Any]) -> dict[str, float]:
    baseline = calculate_metric_score(metric, measurement.get("value_baseline"))
    current = calculate_metric_score(metric, measurement.get("value_current"))
    projected_raw = measurement.get("value_projected")
    projected_value = measurement.get("value_current") if projected_raw is None else projected_raw
    projected = calculate_metric_score(metric, projected_value)
    return {
        "goal": projected.normalized_score,
        "base": baseline.normalized_score,
        "real": current.normalized_score,
    }