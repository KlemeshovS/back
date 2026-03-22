from __future__ import annotations

from enum import Enum
from http import HTTPStatus
from typing import Optional


class ApiErrorCode(str, Enum):
    MISSING_AUTHORIZATION_HEADER = "MISSING_AUTHORIZATION_HEADER"
    INVALID_AUTHORIZATION_HEADER = "INVALID_AUTHORIZATION_HEADER"
    INVALID_TOKEN = "INVALID_TOKEN"
    ADMIN_INVALID_CREDENTIALS = "ADMIN_INVALID_CREDENTIALS"
    ADMIN_INVALID_CURRENT_PASSWORD = "ADMIN_INVALID_CURRENT_PASSWORD"
    ADMIN_INACTIVE = "ADMIN_INACTIVE"
    ADMIN_NOT_FOUND = "ADMIN_NOT_FOUND"
    ADMIN_ALREADY_EXISTS = "ADMIN_ALREADY_EXISTS"
    FORBIDDEN = "FORBIDDEN"
    USERNAME_ALREADY_EXISTS = "USERNAME_ALREADY_EXISTS"
    USERNAME_REQUIRED_FOR_RATING = "USERNAME_REQUIRED_FOR_RATING"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    HTTP_ERROR = "HTTP_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"


class ApiError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: ApiErrorCode,
        message: str,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.headers = headers or {}


def default_http_error_code(status_code: int) -> ApiErrorCode:
    if status_code == HTTPStatus.UNAUTHORIZED:
        return ApiErrorCode.HTTP_ERROR
    if status_code == HTTPStatus.CONFLICT:
        return ApiErrorCode.HTTP_ERROR
    if status_code == HTTPStatus.NOT_FOUND:
        return ApiErrorCode.HTTP_ERROR
    if status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        return ApiErrorCode.VALIDATION_ERROR
    if status_code == HTTPStatus.TOO_MANY_REQUESTS:
        return ApiErrorCode.RATE_LIMIT_EXCEEDED
    return ApiErrorCode.HTTP_ERROR
