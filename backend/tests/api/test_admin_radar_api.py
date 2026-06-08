from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.api.routes.admin_students import get_admin_provider_workspace_service
from app.core.security import hash_password
from app.main import app
from app.storage.contact_user_repository import ContactUserRepository


class _FakeAdminRadarService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def get_student_radar(self, *, provider_user_id: str, client_user_id: str) -> dict[str, Any]:
        self.calls.append((provider_user_id, client_user_id))
        if provider_user_id != "2" or client_user_id != "182":
            raise ValueError("enrollment_not_found")
        return {
            "studentId": client_user_id,
            "axisScores": [
                {
                    "axisId": "1",
                    "axisKey": "cap",
                    "axisLabel": "Captacao",
                    "axisSub": "",
                    "baseline": 0.2,
                    "current": 0.4,
                    "projected": 0.6,
                    "insight": "",
                }
            ],
            "avgBaseline": 0.2,
            "avgCurrent": 0.4,
            "avgProjected": 0.6,
            "context": {},
        }


def _seed_admin(contacts_file: Path) -> None:
    repo = ContactUserRepository(contacts_file)
    repo.create(
        id="usr_admin",
        full_name="Admin",
        email="admin@example.com",
        role="admin",
        is_active=True,
        password_hash=hash_password("admin123"),
    )


def test_admin_mentor_student_radar_normalizes_prefixed_ids(monkeypatch, tmp_path: Path) -> None:
    contacts_file = tmp_path / "contacts_users_v2.json"
    monkeypatch.setenv("CONTACT_USER_STORE_PATH", str(contacts_file))
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "local")
    _seed_admin(contacts_file)
    service = _FakeAdminRadarService()

    app.dependency_overrides[get_admin_provider_workspace_service] = lambda: service
    try:
        client = TestClient(app)
        login_response = client.post("/auth/login", json={"email": "admin@example.com", "password": "admin123"})
        assert login_response.status_code == 200

        response = client.get(
            "/admin/mentores/usr_2/alunos/std_182/radar",
            headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["studentId"] == "182"
        assert len(payload["axisScores"]) == 1
        assert service.calls == [("2", "182")]
    finally:
        app.dependency_overrides.pop(get_admin_provider_workspace_service, None)
