from __future__ import annotations

from typing import Any

from app.core.security import create_access_token, hash_password, verify_access_token, verify_password
from app.storage.student_repository import StudentRepository
from app.storage.user_repository import UserRepository


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        students: StudentRepository,
        secret: str,
        ttl_seconds: int = 3600,
        default_student_password: str = "aluno_accmed",
    ) -> None:
        self._users = users
        self._students = students
        self._secret = secret
        self._ttl_seconds = ttl_seconds
        self._default_student_password = default_student_password

    def _provision_student_user(self, email: str, password: str) -> dict[str, Any] | None:
        normalized_email = email.strip().lower()
        if not normalized_email:
            return None
        if password != self._default_student_password:
            return None

        for student in self._students.list_students():
            if not student.get("is_active", False):
                continue
            student_email = str(student.get("email", "")).strip().lower()
            if student_email != normalized_email:
                continue

            student_id = str(student.get("id", "")).strip() or "student"
            user_id = f"usr_{student_id}"
            try:
                return self._users.create(
                    id=user_id,
                    email=normalized_email,
                    password_hash=hash_password(self._default_student_password),
                    role="aluno",
                    is_active=True,
                )
            except ValueError:
                return self._users.get_by_email(normalized_email)
        return None

    def login(self, email: str, password: str) -> str | None:
        user = self._users.get_by_email(email)
        if not user:
            user = self._provision_student_user(email, password)
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
