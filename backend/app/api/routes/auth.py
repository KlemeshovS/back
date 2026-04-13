from typing import Optional

from fastapi import APIRouter, Depends, Header, Request, status

from app.api.dependencies import (
    enforce_rate_limit,
    get_bearer_token,
    get_client_ip,
    get_current_user_session,
)
from app.core.config import settings
from app.domain.schemas import (
    AnonymousAuthResponse,
    AppleAuthRequest,
    AuthSessionResponse,
    GoogleAuthRequest,
    LinkedIdentityListResponse,
    LogoutResponse,
    RefreshSessionRequest,
    SessionRestoreResponse,
    YandexAuthRequest,
)
from app.services import session_service, social_auth_service, user_service

router = APIRouter()
current_user_session_dependency = Depends(get_current_user_session)


def _enforce_auth_rate_limit(action: str, client_ip: str, detail: str, multiplier: int = 1) -> None:
    enforce_rate_limit(
        key=f"{action}:ip:{client_ip}",
        limit=settings.register_rate_limit * multiplier,
        window_seconds=settings.register_window_seconds,
        detail=detail,
    )


@router.post(
    "/auth/anonymous",
    response_model=AnonymousAuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_anonymous_user(request: Request) -> AnonymousAuthResponse:
    client_ip = get_client_ip(request)
    _enforce_auth_rate_limit(
        "anonymous-auth", client_ip, "Too many account creation attempts. Please try again later."
    )
    return user_service.create_anonymous_user()


@router.post(
    "/auth/google",
    response_model=AuthSessionResponse,
    status_code=status.HTTP_200_OK,
)
def login_with_google(
    payload: GoogleAuthRequest,
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> AuthSessionResponse:
    client_ip = get_client_ip(request)
    _enforce_auth_rate_limit(
        "google-auth", client_ip, "Too many Google login attempts. Please try again later."
    )
    guest_access_token = get_bearer_token(authorization) if authorization else None
    return social_auth_service.authenticate_google(payload.id_token, guest_access_token)


@router.post(
    "/auth/apple",
    response_model=AuthSessionResponse,
    status_code=status.HTTP_200_OK,
)
def login_with_apple(
    payload: AppleAuthRequest,
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> AuthSessionResponse:
    client_ip = get_client_ip(request)
    _enforce_auth_rate_limit(
        "apple-auth", client_ip, "Too many Apple login attempts. Please try again later."
    )
    guest_access_token = get_bearer_token(authorization) if authorization else None
    return social_auth_service.authenticate_apple(payload.id_token, guest_access_token)


@router.post(
    "/auth/yandex",
    response_model=AuthSessionResponse,
    status_code=status.HTTP_200_OK,
)
def login_with_yandex(
    payload: YandexAuthRequest,
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> AuthSessionResponse:
    client_ip = get_client_ip(request)
    _enforce_auth_rate_limit(
        "yandex-auth", client_ip, "Too many Yandex login attempts. Please try again later."
    )
    guest_access_token = get_bearer_token(authorization) if authorization else None
    return social_auth_service.authenticate_yandex(payload.access_token, guest_access_token)


@router.get(
    "/auth/providers",
    response_model=LinkedIdentityListResponse,
    status_code=status.HTTP_200_OK,
)
def list_auth_providers(
    current_session: dict = current_user_session_dependency,
) -> LinkedIdentityListResponse:
    return social_auth_service.list_linked_identities(current_session)


@router.post(
    "/auth/providers/google/link",
    response_model=LinkedIdentityListResponse,
    status_code=status.HTTP_200_OK,
)
def link_google_provider(
    payload: GoogleAuthRequest,
    request: Request,
    current_session: dict = current_user_session_dependency,
) -> LinkedIdentityListResponse:
    client_ip = get_client_ip(request)
    _enforce_auth_rate_limit(
        "google-link", client_ip, "Too many Google link attempts. Please try again later."
    )
    return social_auth_service.link_google_identity(current_session, payload.id_token)


@router.post(
    "/auth/providers/apple/link",
    response_model=LinkedIdentityListResponse,
    status_code=status.HTTP_200_OK,
)
def link_apple_provider(
    payload: AppleAuthRequest,
    request: Request,
    current_session: dict = current_user_session_dependency,
) -> LinkedIdentityListResponse:
    client_ip = get_client_ip(request)
    _enforce_auth_rate_limit(
        "apple-link", client_ip, "Too many Apple link attempts. Please try again later."
    )
    return social_auth_service.link_apple_identity(current_session, payload.id_token)


@router.post(
    "/auth/providers/yandex/link",
    response_model=LinkedIdentityListResponse,
    status_code=status.HTTP_200_OK,
)
def link_yandex_provider(
    payload: YandexAuthRequest,
    request: Request,
    current_session: dict = current_user_session_dependency,
) -> LinkedIdentityListResponse:
    client_ip = get_client_ip(request)
    _enforce_auth_rate_limit(
        "yandex-link", client_ip, "Too many Yandex link attempts. Please try again later."
    )
    return social_auth_service.link_yandex_identity(current_session, payload.access_token)


@router.delete(
    "/auth/providers/{provider}",
    response_model=LinkedIdentityListResponse,
    status_code=status.HTTP_200_OK,
)
def unlink_auth_provider(
    provider: str,
    current_session: dict = current_user_session_dependency,
) -> LinkedIdentityListResponse:
    return social_auth_service.unlink_identity(current_session, provider)


@router.get(
    "/auth/session",
    response_model=SessionRestoreResponse,
    status_code=status.HTTP_200_OK,
)
def restore_current_session(
    current_session: dict = current_user_session_dependency,
) -> SessionRestoreResponse:
    return session_service.restore_session(current_session)


@router.post(
    "/auth/refresh",
    response_model=AuthSessionResponse,
    status_code=status.HTTP_200_OK,
)
def refresh_auth_session(payload: RefreshSessionRequest, request: Request) -> AuthSessionResponse:
    client_ip = get_client_ip(request)
    _enforce_auth_rate_limit(
        "refresh-auth",
        client_ip,
        "Too many refresh attempts. Please try again later.",
        multiplier=2,
    )
    return session_service.refresh_authenticated_session(payload.refresh_token)


@router.post(
    "/auth/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
)
def logout_current_session(
    current_session: dict = current_user_session_dependency,
) -> LogoutResponse:
    return session_service.logout_session(current_session)
