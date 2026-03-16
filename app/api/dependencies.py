from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException, Request, status

from app.core.auth import hash_access_token
from app.core.rate_limit import rate_limiter
from app.db.database import get_connection


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

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=detail,
        headers={"Retry-After": str(retry_after)},
    )


def get_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


def get_current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    token = get_bearer_token(authorization)
    token_hash = hash_access_token(token)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, score, is_rating_enabled
                FROM users
                WHERE auth_token_hash = %s;
                """,
                (token_hash,),
            )
            user = cur.fetchone()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
