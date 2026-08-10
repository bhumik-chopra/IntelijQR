from typing import Annotated
from fastapi import APIRouter, Depends
from app.api.dependencies import CurrentUser, get_dashboard_service
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import DashboardService


router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryResponse)
async def dashboard_summary(current_user: CurrentUser, service: Annotated[DashboardService, Depends(get_dashboard_service)]) -> DashboardSummaryResponse:
    return DashboardSummaryResponse(**await service.summary(current_user.id))
