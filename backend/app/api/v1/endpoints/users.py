from typing import Annotated
from fastapi import APIRouter, Depends, Response

from app.api.dependencies import CurrentUser, get_profile_service
from app.core.config import Settings, get_settings
from app.schemas.common import MessageResponse
from app.schemas.profile import LocaleUpdateRequest, PasswordChangeRequest, ProfileUpdateRequest
from app.schemas.user import UserResponse
from app.services.profile_service import ProfileService


router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.from_domain(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(payload: ProfileUpdateRequest, current_user: CurrentUser, service: Annotated[ProfileService, Depends(get_profile_service)]) -> UserResponse:
    return UserResponse.from_domain(await service.update_name(current_user.id, payload.name))


@router.post("/me/password", response_model=MessageResponse)
async def change_password(payload: PasswordChangeRequest, response: Response, current_user: CurrentUser,
                          service: Annotated[ProfileService, Depends(get_profile_service)], settings: Annotated[Settings, Depends(get_settings)]) -> MessageResponse:
    await service.change_password(current_user, payload.current_password, payload.new_password)
    response.delete_cookie(settings.refresh_cookie_name, path=f"{settings.api_v1_prefix}/auth", secure=settings.cookie_secure, httponly=True, samesite="lax")
    return MessageResponse(message="Password changed. Sign in again on all devices.")


@router.patch("/me/locale", response_model=UserResponse)
async def update_locale(payload: LocaleUpdateRequest, current_user: CurrentUser,
                        service: Annotated[ProfileService, Depends(get_profile_service)]) -> UserResponse:
    return UserResponse.from_domain(await service.update_locale(current_user.id, payload.locale))
