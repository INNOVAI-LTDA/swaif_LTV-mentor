from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.product_assignment_repository import ProductAssignmentRepository


def test_product_assignment_repository_persists_authoritative_baseline_fields(tmp_path) -> None:
    enrollments = EnrollmentRepository(tmp_path / "enrollments.json")
    created = enrollments.create(
        student_id="std_1",
        organization_id="org_1",
        mentor_id="mtr_1",
        progress_score=0.2,
        engagement_score=0.3,
        day=10,
        total_days=90,
        days_left=80,
        ltv_cents=12345,
    )

    assignments = ProductAssignmentRepository(
        file_path=tmp_path / "product_assignments.json",
        enrollments=enrollments,
    )

    saved = assignments.upsert_from_enrollment(created)

    assert saved["assignment_id"] == created["id"]
    assert saved["product_id"] == "org_1"
    assert saved["provider_id"] == "mtr_1"
    assert saved["end_user_id"] == "std_1"
    assert saved["status"] == "active"
    assert saved["days_left"] == 80
    assert saved["ltv_cents"] == 12345
    assert saved["created_at"] is not None
    assert saved["updated_at"] is not None


def test_product_assignment_repository_deactivate_updates_status_and_end_at(tmp_path) -> None:
    enrollments = EnrollmentRepository(tmp_path / "enrollments.json")
    created = enrollments.create(
        student_id="std_1",
        organization_id="org_1",
        mentor_id="mtr_1",
        progress_score=0.1,
        engagement_score=0.1,
    )

    assignments = ProductAssignmentRepository(
        file_path=tmp_path / "product_assignments.json",
        enrollments=enrollments,
    )
    assignments.upsert_from_enrollment(created)

    deactivated = assignments.deactivate(
        created["id"],
        justification="Teste de desvinculo",
        performed_by="admin@swaif.local",
        reassigned_to_provider_id="mtr_2",
    )

    assert deactivated is not None
    assert deactivated["is_active"] is False
    assert deactivated["status"] == "inactive"
    assert deactivated["end_at"] is not None
    assert deactivated["deactivated_reason"] == "Teste de desvinculo"
    assert deactivated["reassigned_to_provider_id"] == "mtr_2"


def test_product_assignment_repository_seeds_from_enrollment_source_when_store_empty(tmp_path) -> None:
    enrollments = EnrollmentRepository(tmp_path / "enrollments.json")
    created = enrollments.create(
        student_id="std_42",
        organization_id="org_seed",
        mentor_id="mtr_seed",
        progress_score=0.5,
        engagement_score=0.6,
    )

    assignments = ProductAssignmentRepository(
        file_path=tmp_path / "product_assignments.json",
        enrollments=enrollments,
    )

    rows = assignments.list_assignments()
    assert len(rows) == 1
    assert rows[0]["id"] == created["id"]
    assert rows[0]["product_id"] == "org_seed"
    assert rows[0]["end_user_id"] == "std_42"


def test_product_assignment_repository_backfills_active_provider_and_mentor_ids(tmp_path) -> None:
    enrollments = EnrollmentRepository(tmp_path / "enrollments.json")
    created = enrollments.create(
        student_id="std_42",
        organization_id="org_seed",
        mentor_id=None,
        progress_score=0.5,
        engagement_score=0.6,
    )
    assignments = ProductAssignmentRepository(
        file_path=tmp_path / "product_assignments.json",
        enrollments=enrollments,
    )
    assignments.upsert_from_enrollment(created)

    result = assignments.backfill_active_provider_ids(
        mentor_id_by_assignment={created["id"]: "mtr_seed"},
        mentor_id_by_organization={"org_seed": "mtr_fallback"},
    )
    updated = assignments.get_by_id(created["id"])
    assert updated is not None
    first_updated_at = str(updated["updated_at"])

    second_result = assignments.backfill_active_provider_ids(
        mentor_id_by_assignment={created["id"]: "mtr_seed"},
        mentor_id_by_organization={"org_seed": "mtr_fallback"},
    )
    after_second = assignments.get_by_id(created["id"])
    assert after_second is not None

    assert result["scanned_active"] == 1
    assert result["updated"] == 1
    assert result["conflicts"] == 0
    assert updated["provider_id"] == "mtr_seed"
    assert updated["mentor_id"] == "mtr_seed"
    assert second_result["scanned_active"] == 1
    assert second_result["updated"] == 0
    assert second_result["conflicts"] == 0
    assert str(after_second["updated_at"]) == first_updated_at


def test_product_assignment_repository_backfill_skips_inactive_rows(tmp_path) -> None:
    enrollments = EnrollmentRepository(tmp_path / "enrollments.json")
    created = enrollments.create(
        student_id="std_42",
        organization_id="org_seed",
        mentor_id=None,
        progress_score=0.5,
        engagement_score=0.6,
    )
    assignments = ProductAssignmentRepository(
        file_path=tmp_path / "product_assignments.json",
        enrollments=enrollments,
    )
    assignments.upsert_from_enrollment(created)
    assignments.deactivate(created["id"], justification="historico")

    result = assignments.backfill_active_provider_ids(
        mentor_id_by_assignment={created["id"]: "mtr_seed"},
        mentor_id_by_organization={"org_seed": "mtr_fallback"},
    )

    stored = assignments.get_by_id(created["id"])
    assert stored is not None
    assert result["scanned_active"] == 0
    assert result["updated"] == 0
    assert result["conflicts"] == 0
    assert stored["provider_id"] is None
    assert stored["mentor_id"] is None


def test_product_assignment_repository_backfill_preserves_divergent_alias_conflict(tmp_path) -> None:
    enrollments = EnrollmentRepository(tmp_path / "enrollments.json")
    created = enrollments.create(
        student_id="std_42",
        organization_id="org_seed",
        mentor_id="mtr_seed",
        progress_score=0.5,
        engagement_score=0.6,
    )
    assignments = ProductAssignmentRepository(
        file_path=tmp_path / "product_assignments.json",
        enrollments=enrollments,
    )
    assignments.upsert_from_enrollment(created)

    stored = assignments.get_by_id(created["id"])
    assert stored is not None
    stored["provider_id"] = "mtr_provider_a"
    stored["mentor_id"] = "mtr_mentor_b"
    assignments._write_items([stored])  # test-only fixture setup
    before = assignments.get_by_id(created["id"])
    assert before is not None
    before_updated_at = str(before["updated_at"])

    result = assignments.backfill_active_provider_ids(
        mentor_id_by_assignment={created["id"]: "mtr_seed"},
        mentor_id_by_organization={"org_seed": "mtr_fallback"},
    )

    after = assignments.get_by_id(created["id"])
    assert after is not None
    assert result["scanned_active"] == 1
    assert result["updated"] == 0
    assert result["conflicts"] == 1
    assert after["provider_id"] == "mtr_provider_a"
    assert after["mentor_id"] == "mtr_mentor_b"
    assert str(after["updated_at"]) == before_updated_at
