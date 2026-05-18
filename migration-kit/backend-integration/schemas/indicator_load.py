from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


CheckpointStatus = Literal["green", "yellow", "red"]


class IndicatorValueIn(BaseModel):
    metric_id: str
    value_baseline: float
    value_current: float
    value_projected: float | None = None
    improving_trend: bool | None = None


class CheckpointIn(BaseModel):
    week: int
    status: CheckpointStatus
    label: str | None = None


class IndicatorLoadRequest(BaseModel):
    metric_values: list[IndicatorValueIn]
    checkpoints: list[CheckpointIn] = []


class IndicatorLoadResult(BaseModel):
    student_id: str
    enrollment_id: str
    measurement_count: int
    checkpoint_count: int
