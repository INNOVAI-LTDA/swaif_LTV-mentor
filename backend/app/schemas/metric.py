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
    metadata: dict | None = None


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
    metadata: dict
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
