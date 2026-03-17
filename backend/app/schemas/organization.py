from __future__ import annotations

from pydantic import BaseModel


class OrganizationCreate(BaseModel):
    name: str
    slug: str | None = None


class OrganizationOut(BaseModel):
    id: str
    name: str
    slug: str
    mentor_id: str | None = None
    is_active: bool


class LinkMentorRequest(BaseModel):
    mentor_id: str
