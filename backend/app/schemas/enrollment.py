from __future__ import annotations

from pydantic import BaseModel

from app.schemas.student import StudentOut


class LinkStudentMentoriaRequest(BaseModel):
    organization_id: str
    mentor_id: str | None = None
    progress_score: float
    engagement_score: float
    urgency_status: str = "normal"
    day: int = 0
    total_days: int = 0
    days_left: int = 0
    ltv_cents: int = 0


class EnrollmentOut(BaseModel):
    id: str
    student_id: str
    organization_id: str
    mentor_id: str | None = None
    progress_score: float
    engagement_score: float
    urgency_status: str
    day: int
    total_days: int
    days_left: int
    ltv_cents: int
    link_reason: str | None = None
    source_enrollment_id: str | None = None
    created_by: str | None = None
    deactivated_at: str | None = None
    deactivated_reason: str | None = None
    deactivated_by: str | None = None
    reassigned_to_mentor_id: str | None = None
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None


class ReassignStudentRequest(BaseModel):
    target_mentor_id: str
    justificativa: str


class UnlinkStudentRequest(BaseModel):
    justificativa: str


class EnrollmentWithStudentOut(EnrollmentOut):
    student: StudentOut
