from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "supabase" / "import_contacts_users_v2.py"
SPEC = spec_from_file_location("import_contacts_users_v2", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

UserRow = MODULE.UserRow
validate_rows = MODULE.validate_rows


def _row(*, role: str, password_hash: str | None) -> object:
    return UserRow(
        id=f"usr-{role}-{password_hash or 'none'}",
        email=f"{role}.{(password_hash or 'none').replace('$', '_')}@example.com",
        role=role,
        full_name="Teste",
        is_active=True,
        organization_id=None,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        password_hash=password_hash,
    )


def test_validate_rows_rejects_missing_password_hash_for_authenticable_roles() -> None:
    rows = [_row(role="admin", password_hash=None), _row(role="provider", password_hash="")]

    valid, rejected = validate_rows(rows)

    assert valid == []
    assert len(rejected) == 2
    assert all(
        any("invalid_password_hash_for_role" in reason for reason in item["reasons"])
        for item in rejected
    )


def test_validate_rows_rejects_password_hash_for_client_role() -> None:
    rows = [_row(role="client", password_hash="pbkdf2_sha256$120000$abc$hash")]

    valid, rejected = validate_rows(rows)

    assert valid == []
    assert len(rejected) == 1
    assert any("invalid_password_hash_for_role" in reason for reason in rejected[0]["reasons"])


def test_validate_rows_accepts_expected_password_hash_by_role() -> None:
    rows = [
        _row(role="admin", password_hash="pbkdf2_sha256$120000$abc$hash"),
        _row(role="provider", password_hash="pbkdf2_sha256$120000$def$hash"),
        _row(role="client", password_hash=None),
    ]

    valid, rejected = validate_rows(rows)

    assert len(valid) == 3
    assert rejected == []
