from __future__ import annotations

from pydantic import BaseModel


class MentorCreate(BaseModel):
    full_name: str
    email: str


class AdminMentorCreate(BaseModel):
    full_name: str
    cpf: str
    email: str
    phone: str | None = None
    bio: str | None = None
    notes: str | None = None


class MentorOut(BaseModel):
    id: str
    full_name: str
    email: str
    cpf: str | None = None
    phone: str | None = None
    bio: str | None = None
    notes: str | None = None
    status: str | None = None
    is_active: bool
    organization_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
