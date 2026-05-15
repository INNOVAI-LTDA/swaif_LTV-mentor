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
