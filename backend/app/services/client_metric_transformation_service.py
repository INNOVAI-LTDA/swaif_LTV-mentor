from __future__ import annotations

from typing import Any

from app.services.metric_score_service import ScoreCalculationError, calculate_metric_score
from app.storage.metric_repository import MetricRepository


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 6)


def _coerce_float(value: Any) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace("%", "").replace("R$", "")
        text = text.replace(".", "").replace(",", ".") if "," in text else text
        try:
            return float(text)
        except ValueError as exc:
            raise ScoreCalculationError("absolute metric value must be numeric") from exc
    raise ScoreCalculationError("absolute metric value must be numeric")


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _to_numeric_or_none(value: Any) -> float | None:
    try:
        return _coerce_float(value)
    except ScoreCalculationError:
        return None


def _present_absolute_value(value: Any) -> Any:
    numeric = _to_numeric_or_none(value)
    if numeric is not None:
        return float(numeric)
    return value


def _resolve_condition_subject(raw_value: Any, condition: dict[str, Any]) -> Any:
    field = condition.get("field")
    if field is not None and isinstance(raw_value, dict):
        return raw_value.get(str(field))
    return raw_value


def _match_contains(subject: Any, expected: Any) -> bool:
    expected_text = _normalize_text(expected)
    if not expected_text:
        return False

    if isinstance(subject, (list, tuple, set)):
        return any(_normalize_text(item) == expected_text for item in subject)

    subject_text = _normalize_text(subject)
    if not subject_text:
        return False
    if subject_text == expected_text:
        return True
    tokens = [token.strip() for token in subject_text.replace(";", ",").split(",") if token.strip()]
    return expected_text in tokens


def _match_range(subject: Any, range_definition: dict[str, Any]) -> bool:
    numeric = _to_numeric_or_none(subject)
    if numeric is None:
        return False

    minimum = _to_numeric_or_none(range_definition.get("min"))
    maximum = _to_numeric_or_none(range_definition.get("max"))
    inclusive_min = bool(range_definition.get("inclusive_min", True))
    inclusive_max = bool(range_definition.get("inclusive_max", True))

    if minimum is not None:
        if inclusive_min and numeric < minimum:
            return False
        if not inclusive_min and numeric <= minimum:
            return False

    if maximum is not None:
        if inclusive_max and numeric > maximum:
            return False
        if not inclusive_max and numeric >= maximum:
            return False

    return minimum is not None or maximum is not None


def _match_op(subject: Any, condition: dict[str, Any]) -> bool:
    operator = _normalize_text(condition.get("op") or condition.get("operator"))
    expected = condition.get("value")

    if operator in {"eq", "="}:
        left_num = _to_numeric_or_none(subject)
        right_num = _to_numeric_or_none(expected)
        if left_num is not None and right_num is not None:
            return left_num == right_num
        return _normalize_text(subject) == _normalize_text(expected)

    numeric = _to_numeric_or_none(subject)
    expected_num = _to_numeric_or_none(expected)
    if numeric is None or expected_num is None:
        return False

    if operator == "lt":
        return numeric < expected_num
    if operator == "lte":
        return numeric <= expected_num
    if operator == "gt":
        return numeric > expected_num
    if operator == "gte":
        return numeric >= expected_num
    return False


def _match_when(condition: dict[str, Any], raw_value: Any) -> bool:
    if not condition:
        return False

    if "all" in condition:
        entries = condition.get("all") or []
        return all(isinstance(entry, dict) and _match_when(entry, raw_value) for entry in entries)

    if "any" in condition:
        entries = condition.get("any") or []
        return any(isinstance(entry, dict) and _match_when(entry, raw_value) for entry in entries)

    if "not" in condition:
        nested = condition.get("not")
        return isinstance(nested, dict) and not _match_when(nested, raw_value)

    subject = _resolve_condition_subject(raw_value, condition)

    if "contains" in condition:
        return _match_contains(subject, condition.get("contains"))

    if "contains_any" in condition:
        values = condition.get("contains_any") or []
        return any(_match_contains(subject, value) for value in values)

    if "range" in condition and isinstance(condition.get("range"), dict):
        return _match_range(subject, condition["range"])

    if "op" in condition or "operator" in condition:
        return _match_op(subject, condition)

    return False


def _evaluate_assign_range(assign_range: dict[str, Any], raw_value: Any) -> float:
    minimum = _to_numeric_or_none(assign_range.get("min"))
    maximum = _to_numeric_or_none(assign_range.get("max"))
    if minimum is None or maximum is None:
        raise ScoreCalculationError("assign_range requires numeric min and max")

    lower = min(minimum, maximum)
    upper = max(minimum, maximum)
    policy = _normalize_text(assign_range.get("policy") or "max")
    if policy == "min":
        return lower
    # `clamp_input` is a legacy policy name; behavior is plain
    # clamp (see the matching branch in
    # `metric_score_service._evaluate_assign_range` for the full
    # rationale and the "no rename" decision from 2026-05-08).
    # This parity implementation lets non-numeric raw values
    # surface as a TypeError from `min(upper, None)` rather than
    # a typed ScoreCalculationError; the parity test exercises
    # only numeric inputs so the divergence stays latent.
    if policy == "clamp_input":
        value = _coerce_float(raw_value)
        return max(lower, min(upper, value))
    return upper


def _evaluate_action(action: dict[str, Any], raw_value: Any) -> float:
    if "assign" in action:
        assigned = _to_numeric_or_none(action.get("assign"))
        if assigned is None:
            raise ScoreCalculationError("assign action requires numeric value")
        return assigned

    if "assign_range" in action and isinstance(action.get("assign_range"), dict):
        return _evaluate_assign_range(action["assign_range"], raw_value)

    if "multiply_input" in action:
        factor = _to_numeric_or_none(action.get("multiply_input"))
        numeric_raw = _coerce_float(raw_value)
        if factor is None or numeric_raw is None:
            raise ScoreCalculationError("multiply_input requires numeric factor and raw value")
        return numeric_raw * factor

    raise ScoreCalculationError("unsupported action for python rule scoring")


def _resolve_normalization_basis(
    *,
    metric: dict[str, Any],
    scoring_rules: dict[str, Any],
    matched_rules: list[dict[str, Any]],
    score: float,
) -> float:
    normalization = scoring_rules.get("normalization") if isinstance(scoring_rules.get("normalization"), dict) else {}
    basis_name = _normalize_text(normalization.get("basis") or "max_score")
    explicit_value = _to_numeric_or_none(normalization.get("value"))
    max_score = _to_numeric_or_none(metric.get("max_score"))
    mcv = _to_numeric_or_none(metric.get("mcv") if metric.get("mcv") is not None else metric.get("mcv_score"))

    if basis_name == "explicit" and explicit_value is not None and explicit_value > 0:
        return explicit_value

    if basis_name == "mcv":
        if explicit_value is not None and explicit_value > 0:
            return explicit_value
        if mcv is not None and mcv > 0:
            return mcv

    if basis_name == "max_range":
        if explicit_value is not None and explicit_value > 0:
            return explicit_value
        for rule in matched_rules:
            action = rule.get("then") if isinstance(rule.get("then"), dict) else {}
            assign_range = action.get("assign_range") if isinstance(action.get("assign_range"), dict) else {}
            range_max = _to_numeric_or_none(assign_range.get("max"))
            if range_max is not None and range_max > 0:
                return range_max

    if basis_name == "max_score":
        if explicit_value is not None and explicit_value > 0:
            return explicit_value
        if max_score is not None and max_score > 0:
            return max_score

    if max_score is not None and max_score > 0:
        return max_score
    if mcv is not None and mcv > 0:
        return mcv
    if explicit_value is not None and explicit_value > 0:
        return explicit_value
    return max(score, 0.0)


def score_relative_python_from_metric(metric: dict[str, Any], absolute_value: Any) -> float:
    scoring_rules = metric.get("scoring_rules") if isinstance(metric.get("scoring_rules"), dict) else {}
    if int(scoring_rules.get("version") or 0) != 2:
        raise ScoreCalculationError("only v2 scoring rules are supported")

    scoring = scoring_rules.get("scoring") if isinstance(scoring_rules.get("scoring"), dict) else {}
    mode = _normalize_text(scoring.get("mode") or "first_match")
    matched_rules: list[dict[str, Any]] = []

    if mode == "per_unit":
        points_per_unit = _to_numeric_or_none(scoring.get("points_per_unit"))
        if points_per_unit is None:
            raise ScoreCalculationError("per_unit mode requires points_per_unit")
        if isinstance(absolute_value, dict):
            quantity = max(
                sum(float(value) for value in absolute_value.values() if isinstance(value, (int, float))),
                0.0,
            )
        else:
            numeric = _coerce_float(absolute_value)
            if numeric is None:
                raise ScoreCalculationError("per_unit requires numeric or count_map raw value")
            quantity = max(0.0, numeric)
        score = quantity * points_per_unit
    else:
        rules = scoring.get("rules") if isinstance(scoring.get("rules"), list) else []
        matched_rules = [
            rule
            for rule in rules
            if isinstance(rule, dict) and _match_when(rule.get("when") if isinstance(rule.get("when"), dict) else {}, absolute_value)
        ]

        if not matched_rules:
            fallback = scoring.get("fallback")
            if isinstance(fallback, dict):
                score = _evaluate_action(fallback, absolute_value)
            else:
                raise ScoreCalculationError("no scoring rule matched")
        elif mode == "sum_matches":
            score = sum(
                _evaluate_action(rule.get("then") if isinstance(rule.get("then"), dict) else {}, absolute_value)
                for rule in matched_rules
            )
        elif mode == "max_match":
            score = max(
                _evaluate_action(rule.get("then") if isinstance(rule.get("then"), dict) else {}, absolute_value)
                for rule in matched_rules
            )
        else:
            first = matched_rules[0]
            score = _evaluate_action(first.get("then") if isinstance(first.get("then"), dict) else {}, absolute_value)
            matched_rules = [first]

    basis = _resolve_normalization_basis(
        metric=metric,
        scoring_rules=scoring_rules,
        matched_rules=matched_rules,
        score=float(score),
    )
    normalized = 0.0 if basis <= 0 else _clamp01(float(score) / basis)
    if _normalize_text(metric.get("direction") or "higher_better") == "lower_better":
        normalized = 1.0 - normalized
    return round(float(normalized), 6)


def load_supabase_metric_rules_by_id(metrics: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    source = metrics if metrics is not None else MetricRepository().list_metrics()
    return {
        str(metric.get("id") or ""): metric
        for metric in source
        if str(metric.get("id") or "")
        and isinstance(metric.get("scoring_rules"), dict)
        and int((metric.get("scoring_rules") or {}).get("version") or 0) == 2
    }


def _describe_metric_rule(metric: dict[str, Any]) -> str:
    scoring_rules = metric.get("scoring_rules") if isinstance(metric.get("scoring_rules"), dict) else {}
    scoring = scoring_rules.get("scoring") if isinstance(scoring_rules.get("scoring"), dict) else {}
    normalization = scoring_rules.get("normalization") if isinstance(scoring_rules.get("normalization"), dict) else {}
    mode = str(scoring.get("mode") or "first_match")
    basis = str(normalization.get("basis") or "max_score")
    rules = scoring.get("rules") if isinstance(scoring.get("rules"), list) else []
    if mode == "per_unit":
        return f"mode=per_unit points_per_unit={scoring.get('points_per_unit')} basis={basis}"
    return f"mode={mode} rules={len(rules)} basis={basis}"


def mock_metric_rules_as_strings(metric_rules_by_id: dict[str, dict[str, Any]] | None = None) -> dict[str, str]:
    rules_by_id = metric_rules_by_id if metric_rules_by_id is not None else load_supabase_metric_rules_by_id()
    return {
        metric_id: _describe_metric_rule(metric)
        for metric_id, metric in sorted(rules_by_id.items(), key=lambda item: item[0])
    }


def score_relative_python(
    metric_id: str,
    absolute_value: Any,
    *,
    metric_rules_by_id: dict[str, dict[str, Any]],
) -> float:
    metric = metric_rules_by_id.get(metric_id)
    if metric is None:
        raise ScoreCalculationError("metric rule not found")
    return score_relative_python_from_metric(metric, absolute_value)


def _default_value_for_input_kind(input_kind: str) -> Any:
    normalized = _normalize_text(input_kind)
    if normalized == "object":
        return {}
    if normalized in {"set", "list", "array"}:
        return []
    if normalized == "string":
        return ""
    return 0.0


def _example_value_for_when(condition: dict[str, Any], input_kind: str) -> Any:
    if "any" in condition and isinstance(condition.get("any"), list) and condition["any"]:
        first = condition["any"][0]
        return _example_value_for_when(first, input_kind) if isinstance(first, dict) else _default_value_for_input_kind(input_kind)

    if "all" in condition and isinstance(condition.get("all"), list) and condition["all"]:
        entries = [entry for entry in condition["all"] if isinstance(entry, dict)]
        return _merge_values_for_input_kind(input_kind, [_example_value_for_when(entry, input_kind) for entry in entries])

    if "range" in condition and isinstance(condition.get("range"), dict):
        range_definition = condition["range"]
        minimum = _to_numeric_or_none(range_definition.get("min"))
        maximum = _to_numeric_or_none(range_definition.get("max"))
        if minimum is not None and maximum is not None:
            return (minimum + maximum) / 2.0
        if minimum is not None:
            return minimum
        if maximum is not None:
            return maximum

    if "contains_any" in condition:
        values = condition.get("contains_any") or []
        token = values[0] if values else ""
        if _normalize_text(input_kind) in {"set", "list", "array"}:
            return [token]
        return str(token)

    if "contains" in condition:
        token = condition.get("contains")
        if _normalize_text(input_kind) in {"set", "list", "array"}:
            return [token]
        return str(token)

    operator = _normalize_text(condition.get("op") or condition.get("operator"))
    value = condition.get("value")
    field = condition.get("field")

    if operator in {"eq", "="}:
        if field is not None:
            return {str(field): value}
        return value

    numeric_value = _to_numeric_or_none(value)
    if numeric_value is not None:
        example = numeric_value
        if operator == "gt":
            example = numeric_value + 1.0
        elif operator == "lt":
            example = numeric_value - 1.0
        elif operator in {"gte", "lte"}:
            example = numeric_value

        if field is not None:
            return {str(field): example}
        return example

    return _default_value_for_input_kind(input_kind)


def _merge_values_for_input_kind(input_kind: str, values: list[Any]) -> Any:
    normalized = _normalize_text(input_kind)
    if normalized == "object":
        merged: dict[str, Any] = {}
        for value in values:
            if isinstance(value, dict):
                merged.update(value)
        return merged

    if normalized in {"set", "list", "array"}:
        merged_list: list[Any] = []
        for value in values:
            if isinstance(value, (list, tuple, set)):
                merged_list.extend(list(value))
            elif value not in {None, ""}:
                merged_list.append(value)
        deduped: list[Any] = []
        for item in merged_list:
            if item not in deduped:
                deduped.append(item)
        return deduped

    for value in reversed(values):
        if value is not None:
            return value
    return _default_value_for_input_kind(input_kind)


def _example_value_for_rules(rules: list[dict[str, Any]], input_kind: str) -> Any:
    examples = [
        _example_value_for_when(rule.get("when") if isinstance(rule.get("when"), dict) else {}, input_kind)
        for rule in rules
    ]
    return _merge_values_for_input_kind(input_kind, examples)


def build_mock_client_absolute_metrics(
    metric_rules_by_id: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    rules_by_id = metric_rules_by_id if metric_rules_by_id is not None else load_supabase_metric_rules_by_id()
    rows: list[dict[str, Any]] = []

    for metric_id, metric in sorted(rules_by_id.items(), key=lambda item: item[0]):
        scoring_rules = metric.get("scoring_rules") if isinstance(metric.get("scoring_rules"), dict) else {}
        scoring = scoring_rules.get("scoring") if isinstance(scoring_rules.get("scoring"), dict) else {}
        mode = _normalize_text(scoring.get("mode") or "first_match")
        input_def = scoring_rules.get("input") if isinstance(scoring_rules.get("input"), dict) else {}
        input_kind = str(input_def.get("kind") or "number")
        rules = [rule for rule in (scoring.get("rules") or []) if isinstance(rule, dict)]

        if mode == "per_unit":
            baseline_absolute: Any = 1.0
            current_absolute: Any = 2.0
            goal_absolute: Any = 3.0
        elif not rules:
            baseline_absolute = _default_value_for_input_kind(input_kind)
            current_absolute = _default_value_for_input_kind(input_kind)
            goal_absolute = _default_value_for_input_kind(input_kind)
        elif mode in {"sum_matches", "max_match"}:
            baseline_absolute = _example_value_for_rules(rules[:1], input_kind)
            current_absolute = _example_value_for_rules(rules[: min(2, len(rules))], input_kind)
            goal_absolute = _example_value_for_rules(rules, input_kind)
        else:
            baseline_absolute = _example_value_for_rules([rules[0]], input_kind)
            current_absolute = _example_value_for_rules([rules[len(rules) // 2]], input_kind)
            goal_absolute = _example_value_for_rules([rules[-1]], input_kind)

        rows.append(
            {
                "client_id": "std_supabase_rules",
                "client_name": "Client Supabase Rules",
                "pillar_id": str(metric.get("pillar_id") or ""),
                "pillar_label": str(metric.get("pillar_id") or ""),
                "metric_id": metric_id,
                "metric_label": str(metric.get("name") or metric_id),
                "baseline_absolute": baseline_absolute,
                "current_absolute": current_absolute,
                "goal_absolute": goal_absolute,
            }
        )

    return rows


def _relative_score(metric: dict[str, Any], value: Any) -> float:
    return float(calculate_metric_score(metric, value).normalized_score)


def _transform_rows(
    *,
    rows: list[dict[str, Any]],
    resolve_relative: Any,
) -> dict[str, Any]:
    grouped_clients: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []

    for row in rows:
        metric_id = str(row.get("metric_id") or "")

        try:
            baseline_rel = float(resolve_relative(metric_id, row.get("baseline_absolute")))
            current_rel = float(resolve_relative(metric_id, row.get("current_absolute")))
            goal_rel = float(resolve_relative(metric_id, row.get("goal_absolute")))
        except ScoreCalculationError as exc:
            errors.append(
                {
                    "clientId": str(row.get("client_id") or ""),
                    "metricId": metric_id,
                    "error": str(exc),
                }
            )
            continue

        client_id = str(row.get("client_id") or "")
        client_bucket = grouped_clients.setdefault(
            client_id,
            {
                "clientId": client_id,
                "clientName": str(row.get("client_name") or client_id),
                "pillars": {},
            },
        )

        pillar_id = str(row.get("pillar_id") or "")
        pillar_bucket = client_bucket["pillars"].setdefault(
            pillar_id,
            {
                "pillarId": pillar_id,
                "pillarLabel": str(row.get("pillar_label") or pillar_id),
                "metrics": [],
            },
        )

        pillar_bucket["metrics"].append(
            {
                "metricId": metric_id,
                "metricLabel": str(row.get("metric_label") or metric_id),
                "absolute": {
                    "baseline": _present_absolute_value(row.get("baseline_absolute")),
                    "current": _present_absolute_value(row.get("current_absolute")),
                    "goal": _present_absolute_value(row.get("goal_absolute")),
                },
                "relative": {
                    "baseline": round(baseline_rel, 6),
                    "current": round(current_rel, 6),
                    "goal": round(goal_rel, 6),
                },
            }
        )

    clients: list[dict[str, Any]] = []
    for client in grouped_clients.values():
        pillars_out: list[dict[str, Any]] = []
        for pillar in client["pillars"].values():
            metrics = pillar.get("metrics") if isinstance(pillar.get("metrics"), list) else []
            pillar["metricAverage"] = {
                "baseline": _avg([float(metric["relative"]["baseline"]) for metric in metrics]),
                "current": _avg([float(metric["relative"]["current"]) for metric in metrics]),
                "goal": _avg([float(metric["relative"]["goal"]) for metric in metrics]),
            }
            pillars_out.append(pillar)

        pillars_out.sort(key=lambda item: str(item.get("pillarLabel") or ""))
        clients.append(
            {
                "clientId": str(client.get("clientId") or ""),
                "clientName": str(client.get("clientName") or ""),
                "pillars": pillars_out,
            }
        )

    clients.sort(key=lambda item: str(item.get("clientName") or ""))
    return {
        "clients": clients,
        "errors": errors,
    }


def transform_client_absolute_metrics(
    *,
    rows: list[dict[str, Any]],
    metric_rules_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    def _resolver(metric_id: str, absolute_value: Any) -> float:
        metric = metric_rules_by_id.get(metric_id)
        if metric is None:
            raise ScoreCalculationError("metric rule not found")
        return _relative_score(metric, absolute_value)

    return _transform_rows(rows=rows, resolve_relative=_resolver)


def transform_client_absolute_metrics_python(*, rows: list[dict[str, Any]]) -> dict[str, Any]:
    metric_rules_by_id = load_supabase_metric_rules_by_id()

    def _resolver(metric_id: str, absolute_value: Any) -> float:
        return score_relative_python(
            metric_id,
            absolute_value,
            metric_rules_by_id=metric_rules_by_id,
        )

    return _transform_rows(rows=rows, resolve_relative=_resolver)


def transform_client_absolute_metrics_python_with_rules(
    *,
    rows: list[dict[str, Any]],
    metric_rules_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    def _resolver(metric_id: str, absolute_value: Any) -> float:
        return score_relative_python(
            metric_id,
            absolute_value,
            metric_rules_by_id=metric_rules_by_id,
        )

    return _transform_rows(rows=rows, resolve_relative=_resolver)


def process_mock_client_absolute_metrics() -> dict[str, Any]:
    rules_by_id = load_supabase_metric_rules_by_id()
    source_rows = build_mock_client_absolute_metrics(rules_by_id)
    transformed = transform_client_absolute_metrics_python_with_rules(
        rows=source_rows,
        metric_rules_by_id=rules_by_id,
    )
    transformed_declarative = transform_client_absolute_metrics(
        rows=source_rows,
        metric_rules_by_id=rules_by_id,
    )
    return {
        "rulesAsString": mock_metric_rules_as_strings(rules_by_id),
        "sourceRows": source_rows,
        "processingMode": "python_rules",
        "metricsCovered": len(rules_by_id),
        "parityWithDeclarative": transformed == transformed_declarative,
        "transformed": transformed,
    }
