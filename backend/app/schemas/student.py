from __future__ import annotations

from pydantic import BaseModel


class StudentCreate(BaseModel):
    full_name: str
    initials: str | None = None
    email: str | None = None


class AdminStudentCreate(BaseModel):
    full_name: str
    cpf: str
    email: str | None = None
    phone: str | None = None
    notes: str | None = None


class StudentOut(BaseModel):
    id: str
    full_name: str
    initials: str
    email: str | None = None
    cpf: str | None = None
    phone: str | None = None
    notes: str | None = None
    status: str
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None


class AdminStudentOut(StudentOut):
    mentor_id: str | None = None
    organization_id: str | None = None
    enrollment_id: str | None = None
