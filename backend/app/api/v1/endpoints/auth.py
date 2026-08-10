from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.dependencies import get_auth_service
from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.common import MessageResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService, AuthenticationResult


router = APIRouter()


def _set_refresh_cookie(response: Response, result: AuthenticationResult, settings: Settings) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=result.refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path=f"{settings.api_v1_prefix}/auth",
    )


def _token_response(result: AuthenticationResult) -> TokenResponse:
    return TokenResponse(
        access_token=result.access_token,
        expires_in=result.access_expires_in,
        user=UserResponse.from_domain(result.user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    result = await service.register(payload.name, str(payload.email), payload.password, payload.locale)
    _set_refresh_cookie(response, result, settings)
    return _token_response(result)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    result = await service.login(str(payload.email), payload.password)
    _set_refresh_cookie(response, result, settings)
    return _token_response(result)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_token:
        raise AuthenticationError("Refresh cookie is missing")
    result = await service.refresh(refresh_token)
    _set_refresh_cookie(response, result, settings)
    return _token_response(result)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> MessageResponse:
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    if refresh_token:
        await service.logout(refresh_token)
    response.delete_cookie(
        settings.refresh_cookie_name,
        path=f"{settings.api_v1_prefix}/auth",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return MessageResponse(message="Logged out")
