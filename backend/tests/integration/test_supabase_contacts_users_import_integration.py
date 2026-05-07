from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "supabase" / "import_contacts_users_v2.py"
SPEC = spec_from_file_location("import_contacts_users_v2", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FakeCursor:
    def __init__(self):
        self._result = None
        self.inserted_email = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params):
        if query.startswith("SELECT id FROM contacts_users_v2"):
            self._result = ("existing-1",)
        elif query.startswith("SELECT 1 FROM contacts_users_v2"):
            self._result = None
        elif query.strip().startswith("INSERT INTO contacts_users_v2"):
            self.inserted_email = params[1]
            self._result = None

    def fetchone(self):
        return self._result


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self._cursor

    def commit(self):
        return None


def test_apply_upsert_reports_destination_duplicate_email_conflict(monkeypatch):
    fake_cursor = FakeCursor()

    class FakePsycopg:
        @staticmethod
        def connect(_database_url):
            return FakeConnection(fake_cursor)

    monkeypatch.setattr(MODULE, "psycopg", FakePsycopg)

    row = MODULE.UserRow(
        id="new-id",
        email="  DUPLICATE@Example.com ",
        role="client",
        full_name="Teste",
        is_active=True,
        organization_id=None,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        password_hash=None,
    )

    stats = MODULE.apply_upsert("postgres://fake", [row])

    assert stats.inserted == 0
    assert stats.updated == 0
    assert stats.rejected == 1
    assert stats.conflicts == [
        {
            "reason": "duplicate_email_in_destination_case_insensitive",
            "record": {"id": "new-id", "email": "duplicate@example.com"},
            "conflict_with_id": "existing-1",
        }
    ]
