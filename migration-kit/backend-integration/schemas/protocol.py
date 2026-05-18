from __future__ import annotations

from pydantic import BaseModel


class ProtocolCreate(BaseModel):
    organization_id: str
    name: str
    code: str | None = None
    metadata: dict | None = None


class ProtocolOut(BaseModel):
    id: str
    organization_id: str
    name: str
    code: str
    metadata: dict
    is_active: bool
