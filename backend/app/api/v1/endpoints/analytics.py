from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import CurrentUser, get_analytics_service
from app.schemas.analytics import AnalyticsOverviewResponse
from app.services.analytics.analytics_service import AnalyticsService


router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def analytics_overview(
    current_user: CurrentUser,
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    period: Annotated[Literal["7d", "30d", "90d", "12m"], Query()] = "30d",
    qr_id: Annotated[str | None, Query(max_length=24)] = None,
) -> AnalyticsOverviewResponse:
    return AnalyticsOverviewResponse(**await service.overview(current_user.id, period, qr_id))
