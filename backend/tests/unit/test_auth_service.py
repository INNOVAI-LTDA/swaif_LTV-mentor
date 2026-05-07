from pathlib import Path

from app.core.security import hash_password, verify_access_token
from app.services.auth_service import AuthService
from app.storage.contact_user_repository import ContactUserRepository
from app.storage.student_repository import StudentRepository
from app.storage.user_repository import UserRepository


def _build_service(tmp_path: Path) -> tuple[AuthService, UserRepository, StudentRepository]:
    users = UserRepository(tmp_path / "users.json")
    students = StudentRepository(tmp_path / "students.json")
    contacts = ContactUserRepository(tmp_path / "contacts.json")
    service = AuthService(users=users, students=students, contacts=contacts, secret="test-secret")
    return service, users, students


def test_provisions_client_role_from_active_student(tmp_path: Path) -> None:
    service, users, students = _build_service(tmp_path)
    students.create(full_name="Aluno X", initials="AX", email="aluno.x@swaif.local")

    token = service.login("aluno.x@swaif.local", "aluno_accmed")

    assert token is not None
    user = users.get_by_email("aluno.x@swaif.local")
    assert user is not None
    assert user["role"] == "client"


def test_login_accepts_legacy_aliases_and_emits_canonical_claim_roles(tmp_path: Path) -> None:
    service, users, _ = _build_service(tmp_path)
    users.create(
        id="usr_aluno",
        email="legacy.aluno@swaif.local",
        password_hash=hash_password("legacy123"),
        role="aluno",
        is_active=True,
    )
    users.create(
        id="usr_student",
        email="legacy.student@swaif.local",
        password_hash=hash_password("legacy123"),
        role="student",
        is_active=True,
    )
    users.create(
        id="usr_mentor_alias",
        email="legacy.mentor@swaif.local",
        password_hash=hash_password("legacy123"),
        role="mentor",
        is_active=True,
    )

    aluno_token = service.login("legacy.aluno@swaif.local", "legacy123")
    student_token = service.login("legacy.student@swaif.local", "legacy123")
    mentor_token = service.login("legacy.mentor@swaif.local", "legacy123")

    assert aluno_token is not None
    assert student_token is not None
    assert mentor_token is not None
    assert verify_access_token(aluno_token, "test-secret")["role"] == "client"
    assert verify_access_token(student_token, "test-secret")["role"] == "client"
    assert verify_access_token(mentor_token, "test-secret")["role"] == "provider"
