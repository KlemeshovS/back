from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, Request, status

from app.core.admin_auth import hash_admin_access_token
from app.core.errors import ApiError, ApiErrorCode
from app.core.rate_limit import rate_limiter
from app.services import admin_service, session_service


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def enforce_rate_limit(key: str, limit: int, window_seconds: int, detail: str) -> None:
    allowed, retry_after = rate_limiter.check(key, limit, window_seconds)
    if allowed:
        return

    raise ApiError(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        code=ApiErrorCode.RATE_LIMIT_EXCEEDED,
        message=detail,
        headers={"Retry-After": str(retry_after)},
    )


def get_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.MISSING_AUTHORIZATION_HEADER,
            message="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.INVALID_AUTHORIZATION_HEADER,
            message="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


def get_current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    token = get_bearer_token(authorization)
    user = session_service.resolve_current_user_by_access_token(token)

    if user is None:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.INVALID_TOKEN,
            message="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_user_session(authorization: Optional[str] = Header(default=None)) -> dict:
    return get_current_user(authorization)


def get_current_admin(authorization: Optional[str] = Header(default=None)) -> dict:
    token = get_bearer_token(authorization)
    token_hash = hash_admin_access_token(token)
    return admin_service.get_admin_by_token_hash(token_hash)


current_admin_dependency = Depends(get_current_admin)


def require_owner(current_admin: dict = current_admin_dependency) -> dict:
    if current_admin["role"] != "owner":
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ApiErrorCode.FORBIDDEN,
            message="Not enough permissions",
        )

    return current_admin
