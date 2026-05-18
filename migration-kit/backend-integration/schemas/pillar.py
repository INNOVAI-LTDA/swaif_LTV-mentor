from __future__ import annotations

from pydantic import BaseModel


class PillarCreate(BaseModel):
    protocol_id: str
    name: str
    code: str | None = None
    order_index: int = 0
    metadata: dict | None = None


class AdminPillarCreate(BaseModel):
    name: str
    code: str | None = None
    order_index: int = 0


class PillarOut(BaseModel):
    id: str
    protocol_id: str
    name: str
    code: str
    order_index: int
    metadata: dict
    is_active: bool


class AdminPillarOut(BaseModel):
    id: str
    protocol_id: str
    name: str
    code: str
    order_index: int
    is_active: bool
