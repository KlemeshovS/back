from __future__ import annotations

from http import HTTPStatus

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import ApiError, ApiErrorCode, default_http_error_code
from app.domain.schemas import ErrorResponse


def build_error_response(code: ApiErrorCode | str, message: str) -> dict[str, str]:
    return ErrorResponse(code=str(code), message=message).model_dump(by_alias=True)


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(exc.code.value, exc.message),
        headers=exc.headers,
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content=build_error_response(
            ApiErrorCode.VALIDATION_ERROR.value,
            "Invalid request payload",
        ),
    )


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(default_http_error_code(exc.status_code).value, message),
        headers=exc.headers,
    )


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content=build_error_response(
            ApiErrorCode.INTERNAL_SERVER_ERROR.value,
            "Internal server error",
        ),
    )
