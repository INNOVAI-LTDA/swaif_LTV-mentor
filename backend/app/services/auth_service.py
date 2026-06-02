from __future__ import annotations

from typing import Any

from app.core.security import create_access_token, verify_access_token, verify_password
from app.storage.contact_user_repository import ContactUserRepository
from app.storage.user_repository import UserRepository


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        contacts: ContactUserRepository,
        secret: str,
        ttl_seconds: int = 3600,
    ) -> None:
        self._users = users
        self._contacts = contacts
        self._secret = secret
        self._ttl_seconds = ttl_seconds

    def login_with_status(self, email: str, password: str) -> tuple[str | None, str | None]:
        fallback_user = self._users.get_by_email(email)
        user = self._contacts.get_by_email(email)
        if not user:
            user = fallback_user
        if not user:
            return None, "AUTH_INVALID_CREDENTIALS"
        if not user.get("is_active", False):
            return None, "AUTH_INVALID_CREDENTIALS"

        user_password_hash = str(user.get("password_hash") or "")
        fallback_password_hash = str(fallback_user.get("password_hash") or "") if fallback_user else ""

        if not user_password_hash and not fallback_password_hash:
            return None, "AUTH_PASSWORD_NOT_CONFIGURED"

        authenticated_user = user
        if not verify_password(password, user_password_hash):
            if not fallback_user or not fallback_user.get("is_active", False):
                return None, "AUTH_INVALID_CREDENTIALS"
            if not fallback_password_hash:
                return None, "AUTH_PASSWORD_NOT_CONFIGURED"
            if not verify_password(password, fallback_password_hash):
                return None, "AUTH_INVALID_CREDENTIALS"
            authenticated_user = fallback_user

        return create_access_token(
            user_id=str(authenticated_user["id"]),
            role=str(authenticated_user["role"]),
            secret=self._secret,
            ttl_seconds=self._ttl_seconds,
        ), None

    def login(self, email: str, password: str) -> str | None:
        token, _ = self.login_with_status(email, password)
        return token

    def get_current_user(self, token: str) -> dict[str, Any] | None:
        payload = verify_access_token(token, self._secret)
        if not payload:
            return None
        user = self._contacts.get_by_id(str(payload["sub"]))
        if not user:
            for candidate in self._users.list_users():
                if str(candidate.get("id") or "") == str(payload["sub"]):
                    user = candidate
                    break
        if not user or not user.get("is_active", False):
            return None
        return user
