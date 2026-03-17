from app.storage.enrollment_repository import EnrollmentRepository


def test_enrollment_repository_can_deactivate_and_keep_history(tmp_path) -> None:
    repo = EnrollmentRepository(tmp_path / "enrollments.json")
    created = repo.create(
        student_id="std_1",
        organization_id="org_1",
        mentor_id="mtr_1",
        progress_score=0,
        engagement_score=0,
        link_reason="Entrada inicial",
        created_by="admin@swaif.local",
    )

    deactivated = repo.deactivate(
        created["id"],
        justification="Redistribuicao operacional",
        performed_by="admin@swaif.local",
        reassigned_to_mentor_id="mtr_2",
    )

    assert deactivated is not None
    assert deactivated["is_active"] is False
    assert deactivated["deactivated_reason"] == "Redistribuicao operacional"
    assert repo.get_active_by_student("std_1") is None
    assert len(repo.list_by_student("std_1")) == 1
