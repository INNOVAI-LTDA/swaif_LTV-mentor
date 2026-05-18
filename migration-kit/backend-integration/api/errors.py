from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


_DEFAULT_CODE_BY_STATUS = {
    status.HTTP_401_UNAUTHORIZED: "AUTH_UNAUTHORIZED",
    status.HTTP_403_FORBIDDEN: "AUTH_FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "RESOURCE_NOT_FOUND",
    status.HTTP_409_CONFLICT: "CONFLICT",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_ERROR",
}

_DEFAULT_MESSAGE_BY_STATUS = {
    status.HTTP_401_UNAUTHORIZED: "Nao autenticado.",
    status.HTTP_403_FORBIDDEN: "Acesso negado.",
    status.HTTP_404_NOT_FOUND: "Recurso nao encontrado.",
    status.HTTP_409_CONFLICT: "Conflito de estado.",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "Payload de requisicao invalido.",
}


def _default_code(status_code: int) -> str:
    return _DEFAULT_CODE_BY_STATUS.get(status_code, f"HTTP_{status_code}")


def _default_message(status_code: int) -> str:
    return _DEFAULT_MESSAGE_BY_STATUS.get(status_code, "Erro inesperado.")


def build_error_payload(
    *,
    status_code: int,
    code: str | None = None,
    message: str | None = None,
    details: Any = None,
) -> dict[str, Any]:
    return {
        "error": {
            "status": status_code,
            "code": code or _default_code(status_code),
            "message": message or _default_message(status_code),
            "details": details,
        }
    }


def api_error(
    *,
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details},
    )


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    code: str | None = None
    message: str | None = None
    details: Any = None

    if isinstance(exc.detail, dict):
        code = exc.detail.get("code")
        message = exc.detail.get("message")
        details = exc.detail.get("details")
    elif isinstance(exc.detail, list):
        details = exc.detail
    elif exc.detail:
        message = str(exc.detail)

    payload = build_error_payload(
        status_code=int(exc.status_code),
        code=code,
        message=message,
        details=details,
    )
    return JSONResponse(
        status_code=int(exc.status_code),
        content=payload,
        headers=exc.headers,
    )


async def request_validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"loc": err.get("loc"), "msg": err.get("msg"), "type": err.get("type")}
        for err in exc.errors()
    ]
    payload = build_error_payload(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        message="Payload de requisicao invalido.",
        details=details,
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload)
