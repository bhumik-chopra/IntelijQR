from fastapi import APIRouter

from app.api.dependencies import CurrentUser
from app.schemas.user import UserResponse


router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.from_domain(current_user)

