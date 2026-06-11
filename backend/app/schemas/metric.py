from __future__ import annotations

from typing import Any
from typing import Literal

from pydantic import BaseModel


# `target_range` is accepted at the schema boundary for forward
# compatibility, but the scoring engine (metric_score_service)
# treats it as `higher_better`. The "value within a baseline-centered
# band" semantics for `target_range` is only applied by
# `indicator_carga_service._is_anomaly` (anomaly detection) and
# `_build_anomaly_texts` (copy). Adding a dedicated branch in the
# scoring engine for `target_range` is a product decision, not a
# bug fix — see the session-2026-05-08 diagnostic and the
# decisions recorded in this repo's cycle history.
MetricDirection = Literal["higher_better", "lower_better", "target_range"]


class MetricCreate(BaseModel):
    protocol_id: str
    pillar_id: str
    name: str
    code: str | None = None
    direction: MetricDirection = "higher_better"
    unit: str | None = None
    scoring_rules: list[dict[str, Any]] | dict[str, Any] | None = None
    score_type: str | None = None
    min_score: int | None = None
    max_score: int | None = None
    mcv_score: int | None = None
    max_basis_score: str | None = None


class AdminMetricCreate(BaseModel):
    name: str
    code: str | None = None
    direction: MetricDirection = "higher_better"
    unit: str | None = None


class MetricOut(BaseModel):
    id: int
    protocol_id: int
    pillar_id: int
    name: str
    code: str
    direction: MetricDirection
    unit: str | None = None
    scoring_rules: list[dict[str, Any]] | dict[str, Any]
    score_type: str
    min_score: int
    max_score: int
    mcv_score: int
    max_basis_score: str
    is_active: bool


class AdminMetricOut(BaseModel):
    id: str
    protocol_id: str
    pillar_id: str
    name: str
    code: str
    direction: MetricDirection
    unit: str | None = None
    is_active: bool
