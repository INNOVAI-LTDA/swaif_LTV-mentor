from __future__ import annotations

from pydantic import BaseModel, Field


class ClientRecord(BaseModel):
    id: str
    name: str
    brand_name: str | None = None
    cnpj: str | None = None
    slug: str | None = None
    status: str | None = None
    is_active: bool = True
    timezone: str | None = None
    currency: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ProductRecord(BaseModel):
    id: str
    client_id: str | None = None
    name: str
    code: str | None = None
    slug: str | None = None
    status: str | None = None
    is_active: bool = True
    description: str | None = None
    delivery_model: str | None = None
    primary_provider_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ProviderRecord(BaseModel):
    id: str
    client_id: str | None = None
    product_id: str | None = None
    full_name: str
    email: str
    cpf: str | None = None
    phone: str | None = None
    bio: str | None = None
    notes: str | None = None
    status: str | None = None
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None


class EndUserRecord(BaseModel):
    id: str
    client_id: str | None = None
    full_name: str
    initials: str | None = None
    email: str | None = None
    cpf: str | None = None
    phone: str | None = None
    notes: str | None = None
    status: str | None = None
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None


class ProductPillarRecord(BaseModel):
    id: str
    product_id: str
    method_version_id: str | None = None
    method_version_name: str | None = None
    method_version_code: str | None = None
    name: str
    code: str | None = None
    order_index: int = 0
    axis_sub: str | None = None
    metadata: dict = Field(default_factory=dict)
    is_active: bool = True


class PillarMetricRecord(BaseModel):
    id: str
    product_id: str
    product_pillar_id: str
    method_version_id: str | None = None
    name: str
    code: str | None = None
    direction: str | None = None
    unit: str | None = None
    metadata: dict = Field(default_factory=dict)
    is_active: bool = True


class ProductAssignmentRecord(BaseModel):
    id: str
    client_id: str | None = None
    product_id: str
    provider_id: str | None = None
    end_user_id: str
    progress_score: float
    engagement_score: float
    urgency_status: str
    day: int = 0
    total_days: int = 0
    days_left: int = 0
    ltv_cents: int = 0
    link_reason: str | None = None
    source_assignment_id: str | None = None
    created_by: str | None = None
    deactivated_at: str | None = None
    deactivated_reason: str | None = None
    deactivated_by: str | None = None
    reassigned_to_provider_id: str | None = None
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None


class MetricMeasureRecord(BaseModel):
    id: str
    product_assignment_id: str
    pillar_metric_id: str
    value_baseline: float | None = None
    value_current: float
    value_projected: float | None = None
    improving_trend: bool | None = None


class JourneyCheckpointRecord(BaseModel):
    id: str
    product_assignment_id: str
    week: int
    status: str
    label: str | None = None


CANONICAL_LEGACY_ENTITY_MAP = {
    "Client": "client",
    "Product": "organization",
    "Provider": "mentor",
    "EndUser": "student",
    "ProductPillar": "pillar + protocol context",
    "PillarMetric": "metric + protocol context",
    "MetricMeasure": "measurement",
    "ProductAssignment": "enrollment",
    "JourneyCheckpoint": "checkpoint",
}


CLIENT_VOCABULARY_DEFAULTS = {
    "accmed": {
        "Client": "Cliente",
        "Product": "Produto",
        "Provider": "Mentor",
        "EndUser": "Aluno",
        "ProductPillar": "Pilar",
        "PillarMetric": "Indicador",
        "MetricMeasure": "Valor do indicador",
    }
}
