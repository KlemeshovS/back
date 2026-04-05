from fastapi import APIRouter, Request, status

from app.api.dependencies import enforce_rate_limit, get_client_ip
from app.core.config import settings
from app.domain.schemas import AnonymousAuthResponse, AuthSessionResponse, GoogleAuthRequest
from app.services import social_auth_service, user_service

router = APIRouter()


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
