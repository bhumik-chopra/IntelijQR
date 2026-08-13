import logging

from app.core.exceptions import ApplicationError, NotFoundError
from app.infrastructure.notifications.local_smtp import LocalSmtpEmailSender
from app.models.notification import Notification
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.notification import NotificationPreferencesUpdate


logger = logging.getLogger(__name__)
CATEGORY_PREFERENCE = {
    "security": "security_alerts",
    "qr": "qr_activity",
    "share": "share_activity",
    "bulk": "bulk_activity",
}


class NotificationService:
    def __init__(self, repository: NotificationRepository, users: UserRepository, email: LocalSmtpEmailSender) -> None:
        self._repository = repository
        self._users = users
        self._email = email

    async def notify(self, user_id: str, event_type: str, category: str, severity: str, title: str, message: str,
                     action_url: str | None = None, metadata: dict | None = None) -> Notification | None:
        preferences = await self._repository.preferences(user_id)
        preference = CATEGORY_PREFERENCE.get(category)
        if preference and not preferences.get(preference, True):
            return None
        notification = None
        if preferences["in_app_enabled"]:
            notification = await self._repository.create(user_id=user_id, event_type=event_type, category=category,
                severity=severity, title=title, message=message, action_url=action_url, metadata=metadata or {})
        if preferences["email_enabled"] and self._email.available:
            user = await self._users.find_by_id(user_id)
            if user is not None and user.status == "active":
                try:
                    await self._email.send(user.email, f"IntelliQR: {title}", f"{message}\n\nOpen IntelliQR to review this event.")
                except Exception:
                    logger.exception("Notification email failed", extra={"user_id": user_id, "event_type": event_type})
        return notification

    async def list_owned(self, user_id: str, limit: int, offset: int, unread_only: bool):
        items, total = await self._repository.list_owned(user_id, limit, offset, unread_only)
        return items, total, await self._repository.unread_count(user_id)

    async def unread_count(self, user_id: str) -> int:
        return await self._repository.unread_count(user_id)

    async def mark_read(self, notification_id: str, user_id: str) -> None:
        if not await self._repository.mark_read(notification_id, user_id):
            raise NotFoundError("Notification was not found")

    async def mark_all_read(self, user_id: str) -> None:
        await self._repository.mark_all_read(user_id)

    async def delete_owned(self, notification_id: str, user_id: str) -> None:
        if not await self._repository.delete_owned(notification_id, user_id):
            raise NotFoundError("Notification was not found")

    async def preferences(self, user_id: str) -> dict:
        return {**await self._repository.preferences(user_id), "local_smtp_available": self._email.available}

    async def update_preferences(self, user_id: str, request: NotificationPreferencesUpdate) -> dict:
        values = request.model_dump()
        if values["email_enabled"] and not self._email.available:
            raise ApplicationError("Configure an SMTP server before enabling email notifications")
        return {**await self._repository.update_preferences(user_id, values), "local_smtp_available": self._email.available}
