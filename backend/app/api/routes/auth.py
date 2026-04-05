from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import enforce_rate_limit, get_client_ip, get_current_user_session
from app.core.config import settings
from app.domain.schemas import (
    AnonymousAuthResponse,
    AppleAuthRequest,
    AuthSessionResponse,
    GoogleAuthRequest,
    LogoutResponse,
    RefreshSessionRequest,
    SessionRestoreResponse,
    YandexAuthRequest,
)
from app.services import session_service, social_auth_service, user_service

router = APIRouter()
current_user_session_dependency = Depends(get_current_user_session)


@router.post(
    "/auth/anonymous",
    response_model=AnonymousAuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_anonymous_user(request: Request) -> AnonymousAuthResponse:
    client_ip = get_client_ip(request)
    enforce_rate_limit(
        key=f"anonymous-auth:ip:{client_ip}",
        limit=settings.register_rate_limit,
        window_seconds=settings.register_window_seconds,
        detail="Too many account creation attempts. Please try again later.",
    )
    return user_service.create_anonymous_user()


@router.post(
    "/auth/google",
    response_model=AuthSessionResponse,
    status_code=status.HTTP_200_OK,
)
def login_with_google(payload: GoogleAuthRequest, request: Request) -> AuthSessionResponse:
    client_ip = get_client_ip(request)
    enforce_rate_limit(
        key=f"google-auth:ip:{client_ip}",
        limit=settings.register_rate_limit,
        window_seconds=settings.register_window_seconds,
        detail="Too many Google login attempts. Please try again later.",
    )
    return social_auth_service.authenticate_google(payload.id_token)


@router.post(
    "/auth/apple",
    response_model=AuthSessionResponse,
    status_code=status.HTTP_200_OK,
)
def login_with_apple(payload: AppleAuthRequest, request: Request) -> AuthSessionResponse:
    client_ip = get_client_ip(request)
    enforce_rate_limit(
        key=f"apple-auth:ip:{client_ip}",
        limit=settings.register_rate_limit,
        window_seconds=settings.register_window_seconds,
        detail="Too many Apple login attempts. Please try again later.",
    )
    return social_auth_service.authenticate_apple(payload.id_token)


@router.post(
    "/auth/yandex",
    response_model=AuthSessionResponse,
    status_code=status.HTTP_200_OK,
)
def login_with_yandex(payload: YandexAuthRequest, request: Request) -> AuthSessionResponse:
    client_ip = get_client_ip(request)
    enforce_rate_limit(
        key=f"yandex-auth:ip:{client_ip}",
        limit=settings.register_rate_limit,
        window_seconds=settings.register_window_seconds,
        detail="Too many Yandex login attempts. Please try again later.",
    )
    return social_auth_service.authenticate_yandex(payload.access_token)


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
    enforce_rate_limit(
        key=f"refresh-auth:ip:{client_ip}",
        limit=settings.register_rate_limit * 2,
        window_seconds=settings.register_window_seconds,
        detail="Too many refresh attempts. Please try again later.",
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
