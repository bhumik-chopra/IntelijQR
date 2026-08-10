from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import AdminUser, get_admin_service
from app.schemas.admin import AdminOverviewResponse, AdminUserListResponse, AdminUserUpdateRequest
from app.schemas.user import UserResponse
from app.services.admin_service import AdminService


router = APIRouter()


@router.get("/overview", response_model=AdminOverviewResponse)
async def admin_overview(
    _: AdminUser,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> AdminOverviewResponse:
    return AdminOverviewResponse(**await service.overview())


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    _: AdminUser,
    service: Annotated[AdminService, Depends(get_admin_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0, le=1_000_000)] = 0,
    search: Annotated[str | None, Query(max_length=100)] = None,
    role: Annotated[Literal["user", "admin"] | None, Query()] = None,
    status: Annotated[Literal["active", "disabled"] | None, Query()] = None,
) -> AdminUserListResponse:
    users, total = await service.list_users(limit, offset, search, role, status)
    return AdminUserListResponse(
        items=[UserResponse.from_domain(user) for user in users],
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + len(users) < total,
    )


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user_access(
    user_id: str,
    payload: AdminUserUpdateRequest,
    admin: AdminUser,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> UserResponse:
    return UserResponse.from_domain(await service.update_user(admin, user_id, payload))
