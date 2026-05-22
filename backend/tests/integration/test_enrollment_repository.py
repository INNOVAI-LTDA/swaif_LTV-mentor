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


def test_enrollment_repository_backfills_missing_active_mentor_ids_from_organization_map(tmp_path) -> None:
    repo = EnrollmentRepository(tmp_path / "enrollments.json")
    enrollment = repo.create(
        student_id="std_1",
        organization_id="org_1",
        mentor_id=None,
        progress_score=0.0,
        engagement_score=0.0,
    )

    result = repo.backfill_active_mentor_ids({"org_1": "mtr_1"})
    updated = repo.get_by_id(enrollment["id"])
    assert updated is not None
    first_updated_at = str(updated["updated_at"])

    second_result = repo.backfill_active_mentor_ids({"org_1": "mtr_1"})
    after_second = repo.get_by_id(enrollment["id"])
    assert after_second is not None

    assert result["scanned_active"] == 1
    assert result["updated"] == 1
    assert updated["mentor_id"] == "mtr_1"
    assert second_result["scanned_active"] == 1
    assert second_result["updated"] == 0
    assert str(after_second["updated_at"]) == first_updated_at


def test_enrollment_repository_backfill_skips_inactive_rows(tmp_path) -> None:
    repo = EnrollmentRepository(tmp_path / "enrollments.json")
    enrollment = repo.create(
        student_id="std_1",
        organization_id="org_1",
        mentor_id=None,
        progress_score=0.0,
        engagement_score=0.0,
    )
    repo.deactivate(enrollment["id"], justification="historico")

    result = repo.backfill_active_mentor_ids({"org_1": "mtr_1"})

    stored = repo.get_by_id(enrollment["id"])
    assert stored is not None
    assert result["scanned_active"] == 0
    assert result["updated"] == 0
    assert stored["mentor_id"] is None
