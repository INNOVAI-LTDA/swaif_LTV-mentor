from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

# Ensure test env before app modules are imported.
os.environ.setdefault("APP_ENV", "local")
os.environ.setdefault("CLIENT_CODE", "test-client")


class InMemoryJsonRepository:
    """Test-only replacement for the production JsonRepository.

    The production class raises unconditionally after the Supabase-only
    refactor (commit 864a7d5). The storage repositories that previously
    used JsonRepository now hit a hard RuntimeError during test setup,
    which is the root cause of the API suite regressions in
    tests/api/test_student_workspace_api.py and
    tests/api/test_admin_metrics_api.py.

    This fake mirrors the public surface used by the storage repositories
    (read / write / snapshot_to / restore_from / file_path / _lock) plus
    the static and class-level helpers (default_payload /
    validate_snapshot_payload / load_snapshot_payload). State lives in a
    class-level dict keyed by file path; per-test isolation comes from
    pytest's tmp_path fixture giving each test unique file paths.

    The production json_repository.JsonRepository is patched below, after
    the in-memory class is defined, so that any
    `from app.storage.json_repository import JsonRepository` performed by
    a test module (or a storage repository it instantiates) sees the
    in-memory version.
    """

    _stores: dict[str, dict[str, Any]] = {}
    _locks_guard = threading.Lock()
    _locks_by_file: dict[str, threading.RLock] = {}

    def __init__(self, file_path: str | Path) -> None:
        key = str(file_path)
        self.file_path = Path(file_path)
        self._lock = self._get_lock(self.file_path)
        if key not in self._stores:
            self._stores[key] = self.default_payload()

    @classmethod
    def _get_lock(cls, file_path: Path) -> threading.RLock:
        key = str(file_path)
        with cls._locks_guard:
            existing = cls._locks_by_file.get(key)
            if existing is not None:
                return existing
            created = threading.RLock()
            cls._locks_by_file[key] = created
            return created

    def read(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._stores.get(str(self.file_path), self.default_payload()))

    def write(self, data: dict[str, Any]) -> None:
        with self._lock:
            self._stores[str(self.file_path)] = dict(data)

    def snapshot_to(self, destination: str | Path) -> Path:
        target_path = Path(destination)
        with self._lock:
            data = self._stores.get(str(self.file_path), self.default_payload())
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return target_path

    def restore_from(self, source: str | Path) -> None:
        payload = self.load_snapshot_payload(source)
        self.write(payload)

    @staticmethod
    def default_payload() -> dict[str, Any]:
        return {"version": 1, "items": []}

    @staticmethod
    def validate_snapshot_payload(payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise RuntimeError("Backup snapshot must contain a JSON object payload.")
        version = payload.get("version")
        items = payload.get("items")
        if not isinstance(version, int) or version < 1:
            raise RuntimeError("Backup snapshot payload must contain an integer version >= 1.")
        if not isinstance(items, list):
            raise RuntimeError("Backup snapshot payload must contain an items list.")
        return payload

    @classmethod
    def load_snapshot_payload(cls, source: str | Path) -> dict[str, Any]:
        source_path = Path(source)
        with source_path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        return cls.validate_snapshot_payload(payload)


# Patch the production class so any subsequent
# `from app.storage.json_repository import JsonRepository` resolves
# to the in-memory fake. The production module itself is left
# intact; only the JsonRepository attribute is swapped in this
# test process.
from app.storage import json_repository  # noqa: E402

json_repository.JsonRepository = InMemoryJsonRepository


# ---------- In-memory ClientRepository swap ----------
# The production ClientRepository raises RuntimeError on every public
# read/write path when SUPABASE_DB_URL is not configured. The admin
# suite tests that touch /admin/clientes exercise that path. A
# in-memory subclass with the same public surface keeps the test
# environment self-contained without enabling JSON storage in
# production.
from app.storage import client_repository  # noqa: E402


class _InMemoryClientRepository(client_repository.ClientRepository):
    """Test-only subclass of ClientRepository with in-memory storage.

    The production class's create / get_by_id / _read_items raise
    RuntimeError when SUPABASE_DB_URL is not configured. This subclass
    keeps the same public surface (list_clients, create, get_by_id,
    _read_items) backed by a class-level list, so per-test isolation
    can be enforced by the autouse fixture below.
    """

    _items: list[dict[str, Any]] = []

    def __init__(self) -> None:
        # Skip the parent's __init__ — it sets up DB connection state
        # and would raise if SUPABASE_DB_URL is set without psycopg.
        # The class-level _items list is the only state we need.
        return None

    def _read_items(self) -> list[dict[str, Any]]:
        return list(self._items)

    def get_by_id(self, client_id: str) -> dict[str, Any] | None:
        normalized = client_repository._normalize_client_id(client_id)
        for item in self._items:
            if client_repository._normalize_client_id(item.get("id")) == normalized:
                return item
        return None

    def create(  # type: ignore[override]
        self,
        *,
        name: str,
        cnpj: str,
        slug: str | None = None,
        brand_name: str | None = None,
        timezone_name: str = "America/Sao_Paulo",
        currency: str = "BRL",
        notes: str | None = None,
    ) -> dict[str, Any]:
        import uuid

        new_id = f"cli_{uuid.uuid4().hex[:12]}"
        now = client_repository._now_iso()
        record = {
            "id": new_id,
            "name": name,
            "brand_name": brand_name or name,
            "cnpj": cnpj,
            "slug": client_repository._slugify(slug or name),
            "status": "active",
            "is_active": True,
            "timezone": timezone_name,
            "currency": currency,
            "notes": notes,
            "created_at": now,
            "updated_at": now,
        }
        self._items.append(record)
        return record


# Per-test cleanup. test_admin_metrics_api has 2 tests that both
# create a "Clinica Horizonte" client (CNPJ 12345678000199); without
# this reset, the second test would hit a duplicate before the
# actual assertions run. The JsonRepository stores are also cleared
# defensively even though tmp_path-based file paths already isolate
# them per test.
import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_in_memory_state():
    InMemoryJsonRepository._stores.clear()
    _InMemoryClientRepository._items.clear()
    yield


# Patch the production class.
client_repository.ClientRepository = _InMemoryClientRepository
