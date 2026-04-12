from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import status

from app.core.config import settings
from app.core.errors import ApiError, ApiErrorCode

ALLOWED_AVATAR_TYPES: dict[str, tuple[str, bytes | tuple[bytes, ...]]] = {
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
    "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
    "image/webp": (".webp", (b"RIFF", b"WEBP")),
}


def ensure_media_directories() -> None:
    avatar_directory().mkdir(parents=True, exist_ok=True)


def build_avatar_url(avatar_path: str | None) -> str | None:
    if not avatar_path:
        return None

    base_url = settings.media_base_url.rstrip("/")
    return f"{base_url}/media/{avatar_path}" if base_url else f"/media/{avatar_path}"


def validate_avatar_image(content_type: str | None, payload: bytes) -> str:
    if not content_type or content_type not in ALLOWED_AVATAR_TYPES:
        raise ApiError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=ApiErrorCode.AVATAR_INVALID_IMAGE,
            message="Avatar must be a JPEG, PNG, or WEBP image",
        )

    extension, signature = ALLOWED_AVATAR_TYPES[content_type]

    if isinstance(signature, tuple):
        if not (payload.startswith(signature[0]) and payload[8:12] == signature[1]):
            raise ApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code=ApiErrorCode.AVATAR_INVALID_IMAGE,
                message="Avatar file is not a valid image",
            )
    elif not payload.startswith(signature):
        raise ApiError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=ApiErrorCode.AVATAR_INVALID_IMAGE,
            message="Avatar file is not a valid image",
        )

    return extension


def build_avatar_storage_path(*, user_id: int, extension: str) -> tuple[str, Path]:
    filename = f"user-{user_id}-{uuid4().hex}{extension}"
    relative_path = f"avatars/{filename}"
    return relative_path, avatar_directory() / filename


def delete_avatar_file(avatar_path: str | None) -> None:
    if not avatar_path:
        return

    target = media_root() / avatar_path
    try:
        target.unlink(missing_ok=True)
    except OSError:
        return


def media_root() -> Path:
    return Path(settings.media_root).expanduser()


def avatar_directory() -> Path:
    return media_root() / "avatars"
