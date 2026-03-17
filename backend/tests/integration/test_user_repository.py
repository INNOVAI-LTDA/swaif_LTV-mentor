from pathlib import Path

from app.storage.user_repository import UserRepository


def test_user_repository_creates_seed_users(tmp_path: Path) -> None:
    users_file = tmp_path / "users.json"

    repo = UserRepository(users_file)
    users = repo.list_users()

    roles = {user["role"] for user in users}
    assert "admin" in roles
    assert "mentor" in roles

    admin_user = repo.get_by_email("admin@swaif.local")
    assert admin_user is not None
    assert admin_user["role"] == "admin"
