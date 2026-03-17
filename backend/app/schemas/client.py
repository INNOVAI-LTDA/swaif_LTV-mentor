from __future__ import annotations

from pydantic import BaseModel


class ClientCreate(BaseModel):
    name: str
    cnpj: str
    slug: str | None = None
    brand_name: str | None = None
    timezone: str | None = "America/Sao_Paulo"
    currency: str | None = "BRL"
    notes: str | None = None


class ClientOut(BaseModel):
    id: str
    name: str
    brand_name: str
    cnpj: str
    slug: str
    status: str
    is_active: bool
    timezone: str
    currency: str
    notes: str | None = None
    created_at: str
    updated_at: str
