from __future__ import annotations

import os

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.errors import api_error
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse
from app.services.auth_service import AuthService
from app.storage.user_repository import UserRepository


router = APIRouter(tags=["auth"])
bearer = HTTPBearer(auto_error=False)


def get_user_repository() -> UserRepository:
    return UserRepository()


def get_auth_service(users: UserRepository = Depends(get_user_repository)) -> AuthService:
    secret = os.getenv("APP_AUTH_SECRET", "dev-auth-secret")
    ttl_seconds = int(os.getenv("APP_AUTH_TTL_SECONDS", "3600"))
    return AuthService(users=users, secret=secret, ttl_seconds=ttl_seconds)


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, auth: AuthService = Depends(get_auth_service)) -> LoginResponse:
    token = auth.login(payload.email, payload.password)
    if not token:
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
        role=str(user["role"]),
    )
