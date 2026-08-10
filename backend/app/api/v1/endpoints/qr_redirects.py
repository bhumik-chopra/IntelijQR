from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from fastapi.responses import RedirectResponse

from app.api.dependencies import get_analytics_service, get_notification_service, get_qr_generator_service
from app.services.analytics.analytics_service import AnalyticsService
from app.services.qr.generator_service import QrGeneratorService
from app.services.notification_service import NotificationService


router = APIRouter()


@router.get("/{slug}", response_class=RedirectResponse, include_in_schema=True)
async def redirect_dynamic_qr(
    slug: str,
    request: Request,
    background_tasks: BackgroundTasks,
    service: Annotated[QrGeneratorService, Depends(get_qr_generator_service)],
    analytics: Annotated[AnalyticsService, Depends(get_analytics_service)],
    notifications: Annotated[NotificationService, Depends(get_notification_service)],
    grant: Annotated[str | None, Query(max_length=2048)] = None,
) -> RedirectResponse:
    destination, generation = await service.resolve_redirect(slug, grant)
    if generation:
        background_tasks.add_task(
            analytics.record_scan,
            generation,
            request.client.host if request.client else "unknown",
            request.headers.get("user-agent", ""),
        )
        if generation.max_scans is not None and generation.scan_count >= generation.max_scans:
            background_tasks.add_task(notifications.notify, generation.user_id, "qr.scan_limit_reached", "qr", "warning",
                "QR scan limit reached", "A dynamic QR code reached its configured scan limit and is now inactive.",
                "/dashboard", {"qr_id": generation.id, "scan_count": generation.scan_count})
    return RedirectResponse(destination, status_code=307, headers={"Referrer-Policy": "no-referrer", "Cache-Control": "no-store"})
