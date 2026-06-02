from __future__ import annotations

import os

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.errors import api_error
from app.config.runtime import get_auth_secret
from app.core.security import canonicalize_role
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse
from app.services.auth_service import AuthService
from app.storage.contact_user_repository import ContactUserRepository
from app.storage.user_repository import UserRepository


router = APIRouter(tags=["auth"])
bearer = HTTPBearer(auto_error=False)


def get_user_repository() -> UserRepository:
    return UserRepository()


def get_contact_user_repository() -> ContactUserRepository:
    return ContactUserRepository()


def get_auth_service(
    users: UserRepository = Depends(get_user_repository),
    contacts: ContactUserRepository = Depends(get_contact_user_repository),
) -> AuthService:
    try:
        secret = get_auth_secret()
    except RuntimeError as error:
        raise api_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="AUTH_SECRET_NOT_CONFIGURED",
            message=str(error),
        ) from error
    ttl_seconds = int(os.getenv("APP_AUTH_TTL_SECONDS", "3600"))
    return AuthService(
        users=users,
        contacts=contacts,
        secret=secret,
        ttl_seconds=ttl_seconds,
    )


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, auth: AuthService = Depends(get_auth_service)) -> LoginResponse:
    token, error_code = auth.login_with_status(payload.email, payload.password)
    if not token:
        if error_code == "AUTH_PASSWORD_NOT_CONFIGURED":
            raise api_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="AUTH_PASSWORD_NOT_CONFIGURED",
                message="Senha nao configurada para este usuario.",
            )
        raise api_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTH_INVALID_CREDENTIALS",
            message="Credenciais invalidas.",
        )
    return LoginResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
def me(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    auth: AuthService = Depends(get_auth_service),
) -> MeResponse:
    if credentials is None:
        raise api_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTH_MISSING_TOKEN",
            message="Token de acesso ausente.",
        )

    user = auth.get_current_user(credentials.credentials)
    if not user:
        raise api_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTH_INVALID_TOKEN",
            message="Token de acesso invalido.",
        )

    return MeResponse(
        id=str(user["id"]),
        email=str(user["email"]),
        role=canonicalize_role(str(user["role"])),
    )
