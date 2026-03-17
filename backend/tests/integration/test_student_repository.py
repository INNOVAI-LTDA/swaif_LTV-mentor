from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.student_repository import StudentRepository


def test_student_repository_creates_student_with_cpf(tmp_path) -> None:
    repo = StudentRepository(tmp_path / "students.json")

    created = repo.create(full_name="Aluno Um", cpf="123.456.789-00", email="aluno1@swaif.local")

    assert created["id"] == "std_1"
    assert created["cpf"] == "12345678900"
    assert repo.get_by_id("std_1") is not None


def test_student_repository_rejects_duplicate_cpf(tmp_path) -> None:
    repo = StudentRepository(tmp_path / "students.json")
    repo.create(full_name="Aluno Um", cpf="12345678900", email="aluno1@swaif.local")

    try:
        repo.create(full_name="Aluno Dois", cpf="123.456.789-00")
    except ValueError as exc:
        assert str(exc) == "student cpf already exists"
    else:
        raise AssertionError("ValueError was expected")


def test_enrollment_repository_lists_by_mentor(tmp_path) -> None:
    repo = EnrollmentRepository(tmp_path / "enrollments.json")
    repo.create(
        student_id="std_1",
        organization_id="org_1",
        mentor_id="mtr_1",
        progress_score=0,
        engagement_score=0,
    )

    assert len(repo.list_by_mentor("mtr_1")) == 1
