from pathlib import Path

from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.student_repository import StudentRepository


def test_student_and_enrollment_persistence(tmp_path: Path) -> None:
    student_repo = StudentRepository(tmp_path / "students.json")
    enrollment_repo = EnrollmentRepository(tmp_path / "enrollments.json")

    student = student_repo.create(
        full_name="Aluno Um",
        initials="AU",
        email="aluno1@swaif.local",
    )
    enrollment = enrollment_repo.create(
        student_id=student["id"],
        organization_id="org_1",
        progress_score=0.35,
        engagement_score=0.8,
        urgency_status="watch",
        day=12,
        total_days=90,
        days_left=78,
        ltv_cents=150000,
    )

    assert student_repo.get_by_id(student["id"]) is not None
    assert enrollment["student_id"] == student["id"]

    by_organization = enrollment_repo.list_by_organization("org_1")
    assert len(by_organization) == 1
    assert by_organization[0]["id"] == enrollment["id"]
    assert by_organization[0]["progress_score"] == 0.35
