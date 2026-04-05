from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import status

from app.core.config import settings
from app.core.errors import ApiError, ApiErrorCode

YANDEX_INFO_URL = "https://login.yandex.ru/info?format=json"


@dataclass(frozen=True)
class YandexIdentity:
    subject: str
    email: str | None
    email_verified: bool
    payload: dict[str, Any]


def build_yandex_placeholder_username(subject: str) -> str:
    return f"anon_user_{sha256(subject.encode('utf-8')).hexdigest()[:16]}"


def verify_yandex_access_token(access_token: str) -> YandexIdentity:
    request = Request(
        YANDEX_INFO_URL,
        headers={"Authorization": f"OAuth {access_token}"},
    )

    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.YANDEX_AUTH_INVALID,
            message="Invalid Yandex token",
        ) from exc

    subject = payload.get("id")
    client_id = payload.get("client_id")
    default_email = payload.get("default_email")

    if not subject or not isinstance(subject, str):
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.YANDEX_AUTH_INVALID,
            message="Invalid Yandex token",
        )

    allowed_client_ids = settings.yandex_client_ids_list
    if allowed_client_ids and client_id not in allowed_client_ids:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.YANDEX_AUTH_INVALID,
            message="Invalid Yandex token",
        )

    return YandexIdentity(
        subject=subject,
        email=default_email,
        email_verified=default_email is not None,
        payload={
            "client_id": client_id,
            "login": payload.get("login"),
            "display_name": payload.get("display_name"),
            "default_avatar_id": payload.get("default_avatar_id"),
        },
    )
