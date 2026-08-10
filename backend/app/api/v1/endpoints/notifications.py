from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import CurrentUser, get_notification_service
from app.schemas.common import MessageResponse
from app.schemas.notification import (NotificationListResponse, NotificationPreferences,
    NotificationPreferencesUpdate, NotificationResponse, NotificationUnreadResponse)
from app.services.notification_service import NotificationService


router = APIRouter()


def _response(item) -> NotificationResponse:
    return NotificationResponse(id=item.id, event_type=item.event_type, category=item.category, severity=item.severity,
        title=item.title, message=item.message, action_url=item.action_url, metadata=item.metadata,
        is_read=item.is_read, created_at=item.created_at)


@router.get("", response_model=NotificationListResponse)
async def list_notifications(current_user: CurrentUser, service: Annotated[NotificationService, Depends(get_notification_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 30, offset: Annotated[int, Query(ge=0, le=1_000_000)] = 0,
    unread_only: bool = False) -> NotificationListResponse:
    items, total, unread = await service.list_owned(current_user.id, limit, offset, unread_only)
    return NotificationListResponse(items=[_response(item) for item in items], total=total, limit=limit, offset=offset,
        has_more=offset + len(items) < total, unread_count=unread)


@router.get("/unread-count", response_model=NotificationUnreadResponse)
async def unread_count(current_user: CurrentUser, service: Annotated[NotificationService, Depends(get_notification_service)]) -> NotificationUnreadResponse:
    return NotificationUnreadResponse(unread_count=await service.unread_count(current_user.id))


@router.get("/preferences", response_model=NotificationPreferences)
async def get_preferences(current_user: CurrentUser, service: Annotated[NotificationService, Depends(get_notification_service)]) -> NotificationPreferences:
    return NotificationPreferences(**await service.preferences(current_user.id))


@router.patch("/preferences", response_model=NotificationPreferences)
async def update_preferences(payload: NotificationPreferencesUpdate, current_user: CurrentUser,
    service: Annotated[NotificationService, Depends(get_notification_service)]) -> NotificationPreferences:
    return NotificationPreferences(**await service.update_preferences(current_user.id, payload))


@router.post("/read-all", response_model=MessageResponse)
async def mark_all_read(current_user: CurrentUser, service: Annotated[NotificationService, Depends(get_notification_service)]) -> MessageResponse:
    await service.mark_all_read(current_user.id)
    return MessageResponse(message="All notifications marked as read")


@router.post("/{notification_id}/read", response_model=MessageResponse)
async def mark_read(notification_id: str, current_user: CurrentUser,
    service: Annotated[NotificationService, Depends(get_notification_service)]) -> MessageResponse:
    await service.mark_read(notification_id, current_user.id)
    return MessageResponse(message="Notification marked as read")


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(notification_id: str, current_user: CurrentUser,
    service: Annotated[NotificationService, Depends(get_notification_service)]) -> Response:
    await service.delete_owned(notification_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
