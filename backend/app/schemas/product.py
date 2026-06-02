from __future__ import annotations

from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    code: str
    slug: str | None = None
    description: str | None = None
    delivery_model: str | None = "live"


class ProductOut(BaseModel):
    id: str
    client_id: str
    name: str
    code: str
    slug: str
    status: str
    is_active: bool
    description: str | None = None
    delivery_model: str
    mentor_id: str | None = None
    created_at: str
    updated_at: str
