from pathlib import Path

from app.core.security import hash_password, verify_access_token
from app.services.auth_service import AuthService
from app.storage.contact_user_repository import ContactUserRepository
from app.storage.user_repository import UserRepository


def _build_service(tmp_path: Path) -> tuple[AuthService, UserRepository]:
    users = UserRepository(tmp_path / "users.json")
    contacts = ContactUserRepository(tmp_path / "contacts.json")
    service = AuthService(users=users, contacts=contacts, secret="test-secret")
    return service, users


def test_does_not_provision_client_from_student_email(tmp_path: Path) -> None:
    service, users = _build_service(tmp_path)

    token = service.login("aluno.x@swaif.local", "aluno_accmed")

    assert token is None
    user = users.get_by_email("aluno.x@swaif.local")
    assert user is None


def test_login_accepts_legacy_aliases_and_emits_canonical_claim_roles(tmp_path: Path) -> None:
    service, users = _build_service(tmp_path)
    users.create(
        email="legacy.aluno@swaif.local",
        password_hash=hash_password("legacy123"),
        role="aluno",
        is_active=True,
    )
    users.create(
        email="legacy.student@swaif.local",
        password_hash=hash_password("legacy123"),
        role="student",
        is_active=True,
    )
    users.create(
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


def test_login_with_status_returns_password_not_configured_for_existing_user_without_hash(tmp_path: Path) -> None:
    service, users = _build_service(tmp_path)
    users.create(
        email="sem.hash@swaif.local",
        password_hash="",
        role="provider",
        is_active=True,
    )

    token, error_code = service.login_with_status("sem.hash@swaif.local", "qualquer")
    assert token is None
    assert error_code == "AUTH_PASSWORD_NOT_CONFIGURED"
