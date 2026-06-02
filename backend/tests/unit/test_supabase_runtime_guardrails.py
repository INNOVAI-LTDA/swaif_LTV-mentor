from __future__ import annotations

import pytest

from app.config.runtime import require_supabase_runtime_database_url


def test_require_supabase_runtime_database_url_allows_empty_when_not_required(monkeypatch) -> None:
    monkeypatch.delenv("SUPABASE_RUNTIME_REQUIRED", raising=False)
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)

    assert require_supabase_runtime_database_url(flow_name="mentor-runtime") == ""


def test_require_supabase_runtime_database_url_raises_when_required_without_db_url(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_RUNTIME_REQUIRED", "true")
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)

    with pytest.raises(RuntimeError, match="SUPABASE_DB_URL is required for mentor-runtime"):
        require_supabase_runtime_database_url(flow_name="mentor-runtime")


def test_require_supabase_runtime_database_url_returns_url_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_RUNTIME_REQUIRED", "true")
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://accmed:secret@localhost:5432/accmed")

    assert (
        require_supabase_runtime_database_url(flow_name="mentor-runtime")
        == "postgresql://accmed:secret@localhost:5432/accmed"
    )
