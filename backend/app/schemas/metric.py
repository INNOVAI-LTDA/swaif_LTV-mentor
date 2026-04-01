from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


MetricDirection = Literal["higher_better", "lower_better", "target_range"]


class MetricCreate(BaseModel):
    protocol_id: str
    pillar_id: str
    name: str
    code: str | None = None
    direction: MetricDirection = "higher_better"
    unit: str | None = None
    scoring_rules: list[dict] | None = None
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
    id: str
    protocol_id: str
    pillar_id: str
    name: str
    code: str
    direction: MetricDirection
    unit: str | None = None
    scoring_rules: list[dict]
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
