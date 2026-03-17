from __future__ import annotations

from typing import Any

from app.core.security import create_access_token, verify_access_token, verify_password
from app.storage.user_repository import UserRepository


class AuthService:
    def __init__(self, users: UserRepository, secret: str, ttl_seconds: int = 3600) -> None:
        self._users = users
        self._secret = secret
        self._ttl_seconds = ttl_seconds

    def login(self, email: str, password: str) -> str | None:
        user = self._users.get_by_email(email)
        if not user:
            return None
        if not user.get("is_active", False):
            return None
        if not verify_password(password, str(user.get("password_hash", ""))):
            return None
        return create_access_token(
            user_id=str(user["id"]),
            role=str(user["role"]),
            secret=self._secret,
            ttl_seconds=self._ttl_seconds,
        )

    def get_current_user(self, token: str) -> dict[str, Any] | None:
        payload = verify_access_token(token, self._secret)
        if not payload:
            return None
        user = self._users.get_by_id(str(payload["sub"]))
        if not user or not user.get("is_active", False):
            return None
        return user
