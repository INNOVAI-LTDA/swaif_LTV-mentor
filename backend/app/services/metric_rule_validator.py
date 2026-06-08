"""
Validator for v2 metric scoring rules.

Pure function: no I/O, no logging, no exceptions raised. Returns a list of
issue codes. Strict mode prefixes the [ERROR] tag; warnings are returned as
plain codes. The caller decides what to do with [ERROR] entries (raise 422
at metric create, emit a boot-time log line, etc.).

Issue catalog:

- unknown_mode                              : scoring.mode not in the known set
- unknown_basis                             : normalization.basis not in the known set
- unknown_action                            : then-clause carries a key outside the v2 action set
- per_unit_missing_points_per_unit          : mode == "per_unit" without points_per_unit
- empty_rules_without_fallback              : rules == [] and no fallback
- v1_predicate_in_v2_rules                  : rule uses a v1-only predicate key
                                              (description, operator without op, points/points_range)
- max_basis_uppercase_legacy                : metric.max_score_basis is the v1 UPPERCASE sentinel
- unsupported_input_kind                    : scoring_rules.input.kind is not in the known set

The validator is intentionally permissive: a non-empty list of [WARN] codes
does not block the metric. Only [ERROR] codes are blocking.
"""
from __future__ import annotations

from typing import Any


VALID_MODES = {"first_match", "max_match", "sum_matches", "per_unit"}
VALID_BASES = {"explicit", "mcv", "max_range", "max_score"}
VALID_ACTIONS = {"assign", "assign_range", "multiply_input"}
VALID_INPUT_KINDS = {"number", "string", "set", "list", "array", "object"}
LEGACY_BASIS_TOKENS = {"MCV", "MAX_RVALUE"}


def _is_v2_dict(scoring_rules: Any) -> bool:
    return isinstance(scoring_rules, dict) and int(scoring_rules.get("version") or 0) == 2


def _walk_then_actions(then_clause: Any) -> list[dict[str, Any]]:
    """Return each `then` clause that should be inspected for action keys.

    A v2 rule can have either a single dict `then` or, in degenerate cases, no
    `then` at all. The validator never assumes well-formedness; it walks what
    is there.
    """
    if isinstance(then_clause, dict):
        return [then_clause]
    if isinstance(then_clause, list):
        return [item for item in then_clause if isinstance(item, dict)]
    return []


def _iter_predicates_for_v1_legacy_check(rule: dict[str, Any]) -> list[Any]:
    """Yield nested `when` predicates to scan for v1-only keys.

    Used to flag rules that look like v2 (have a `when` dict) but also use a
    v1-only key like `description` or `operator` without `op`.
    """
    when = rule.get("when")
    if isinstance(when, dict):
        yield when
        for key in ("all", "any"):
            entries = when.get(key)
            if isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, dict):
                        yield entry
        nested = when.get("not")
        if isinstance(nested, dict):
            yield nested
    condition = rule.get("condition")
    if isinstance(condition, dict):
        yield condition


def _predicate_uses_v1_only_key(predicate: dict[str, Any]) -> str | None:
    """Return the v1-only key name if `predicate` uses one, else None."""
    if "description" in predicate:
        return "description"
    # `operator` is v1 only when `op` is not also present. v2 prefers `op`.
    if "operator" in predicate and "op" not in predicate:
        return "operator"
    if "points" in predicate:
        return "points"
    if "points_range" in predicate:
        return "points_range"
    return None


def validate_v2_scoring_rules(
    scoring_rules: Any,
    *,
    strict: bool = True,
    metric: dict[str, Any] | None = None,
) -> list[str]:
    """Validate a v2 `scoring_rules` payload. Returns a list of issue codes.

    When `strict` is True, the function still never raises; it just returns
    issue codes with [ERROR] / [WARN] prefixes so the caller can decide.

    `metric` is optional metadata (used to flag legacy `max_score_basis`
    sentinels on the metric envelope). When omitted, only the rules dict is
    inspected.
    """
    if not _is_v2_dict(scoring_rules):
        # Validator is v2-only. A v1 list-shaped ruleset or a missing rules
        # payload is out of scope; we don't flag it as malformed here.
        return []

    issues: list[str] = []
    err = "[ERROR]" if strict else "[WARN]"

    scoring = scoring_rules.get("scoring") if isinstance(scoring_rules.get("scoring"), dict) else {}
    normalization = scoring_rules.get("normalization") if isinstance(scoring_rules.get("normalization"), dict) else {}

    # input.kind
    input_def = scoring_rules.get("input") if isinstance(scoring_rules.get("input"), dict) else {}
    input_kind = str(input_def.get("kind") or "number")
    if input_kind not in VALID_INPUT_KINDS:
        issues.append(f"{err} unsupported_input_kind kind={input_kind}")

    # mode
    mode = str(scoring.get("mode") or "first_match").strip().lower()
    if mode not in VALID_MODES:
        issues.append(f"{err} unknown_mode mode={mode}")
    elif mode == "per_unit" and scoring.get("points_per_unit") is None:
        issues.append(f"{err} per_unit_missing_points_per_unit")

    # rules & fallback
    rules = scoring.get("rules")
    fallback = scoring.get("fallback")
    if isinstance(rules, list) and not rules and not isinstance(fallback, dict):
        issues.append(f"{err} empty_rules_without_fallback")

    # action coverage: walk every rule's `then` and flag unknown keys
    if isinstance(rules, list):
        for index, rule in enumerate(rules):
            if not isinstance(rule, dict):
                continue
            for action in _walk_then_actions(rule.get("then")):
                if not action:
                    continue
                unknown_keys = sorted(
                    key for key in action.keys() if key not in VALID_ACTIONS
                )
                if unknown_keys:
                    issues.append(
                        f"{err} unknown_action rule_index={index} keys={','.join(unknown_keys)}"
                    )
            # v1 legacy check on the `when` predicate
            for predicate in _iter_predicates_for_v1_legacy_check(rule):
                legacy_key = _predicate_uses_v1_only_key(predicate)
                if legacy_key:
                    issues.append(
                        f"[WARN] v1_predicate_in_v2_rules rule_index={index} key={legacy_key}"
                    )

    # also check the fallback if it has a `then` shape
    for action in _walk_then_actions(fallback):
        if not action:
            continue
        unknown_keys = sorted(
            key for key in action.keys() if key not in VALID_ACTIONS
        )
        if unknown_keys:
            issues.append(f"{err} unknown_action source=fallback keys={','.join(unknown_keys)}")

    # basis
    basis = str(normalization.get("basis") or "max_score").strip().lower()
    if basis not in VALID_BASES:
        issues.append(f"{err} unknown_basis basis={basis}")

    # metric-envelope legacy sentinels (only inspected if metric is provided)
    if isinstance(metric, dict):
        max_basis = str(metric.get("max_score_basis") or "").strip().upper()
        if max_basis in LEGACY_BASIS_TOKENS:
            issues.append(
                f"[WARN] max_basis_uppercase_legacy basis={max_basis}"
            )

    return issues


def summarize_validation_warnings(
    metrics: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    """Walk a list of metrics, run the validator against each, and return
    `(metric_id, issue_code)` pairs for every [ERROR] finding. [WARN] entries
    are intentionally dropped — the boot-log hook only surfaces blocking
    findings.
    """
    findings: list[tuple[str, str]] = []
    for metric in metrics:
        if not isinstance(metric, dict):
            continue
        metric_id = str(metric.get("id") or "")
        if not metric_id:
            continue
        scoring_rules = metric.get("scoring_rules")
        if not isinstance(scoring_rules, dict):
            continue
        issues = validate_v2_scoring_rules(scoring_rules, strict=True, metric=metric)
        for issue in issues:
            if issue.startswith("[ERROR]"):
                # strip the tag so the log line stays compact
                findings.append((metric_id, issue[len("[ERROR] "):].strip()))
    return findings
