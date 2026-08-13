import asyncio
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.core.exceptions import ApplicationError, NotFoundError
from app.schemas.notification import NotificationPreferencesUpdate
from app.services.notification_service import NotificationService


def test_remote_smtp_hosts_are_supported() -> None:
    settings = Settings(_env_file=None, jwt_secret="x" * 32, smtp_host="smtp.resend.com")
    assert settings.smtp_host == "smtp.resend.com"


def test_notification_persists_and_delivers_opted_in_local_email() -> None:
    class Repository:
        created = None
        async def preferences(self, _user_id): return {"in_app_enabled": True, "email_enabled": True, "security_alerts": True}
        async def create(self, **values): self.created = values; return SimpleNamespace(**values)

    class Users:
        async def find_by_id(self, _user_id): return SimpleNamespace(email="owner@example.com", status="active")

    class Email:
        available = True
        sent = None
        async def send(self, recipient, subject, body): self.sent = (recipient, subject, body)

    repository, email = Repository(), Email()
    service = NotificationService(repository, Users(), email)
    asyncio.run(service.notify("owner", "security.risky_qr_detected", "security", "critical", "Risky QR", "Review it"))

    assert repository.created["event_type"] == "security.risky_qr_detected"
    assert email.sent[0] == "owner@example.com"
    assert "Risky QR" in email.sent[1]


def test_preferences_require_local_smtp_and_missing_notifications_are_owner_safe() -> None:
    class Repository:
        async def update_preferences(self, _user_id, values): return values
        async def mark_read(self, _notification_id, _user_id): return False

    class Email:
        available = False

    service = NotificationService(Repository(), None, Email())
    request = NotificationPreferencesUpdate(in_app_enabled=True, email_enabled=True, security_alerts=True,
        qr_activity=True, share_activity=True, bulk_activity=True)
    with pytest.raises(ApplicationError, match="email provider"):
        asyncio.run(service.update_preferences("user", request))
    with pytest.raises(NotFoundError):
        asyncio.run(service.mark_read("another-users-notification", "user"))
