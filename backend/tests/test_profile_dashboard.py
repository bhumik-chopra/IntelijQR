import asyncio
from datetime import datetime, timezone

import pytest

from app.core.exceptions import AuthorizationError
from app.core.security import PasswordService
from app.models.user import User
from app.services.dashboard_service import DashboardService
from app.services.profile_service import ProfileService


def make_user(password_hash: str) -> User:
    now = datetime.now(timezone.utc)
    return User(id="user-id", name="Current Name", email="user@example.com", password_hash=password_hash,
                role="user", status="active", token_version=1, created_at=now, updated_at=now)


def test_profile_name_update_returns_updated_user() -> None:
    passwords = PasswordService(); user = make_user(passwords.hash("current-password"))
    class Users:
        async def update_name(self, _id, name):
            return User(**{**{field: getattr(user, field) for field in user.__dataclass_fields__}, "name": name})
    service = ProfileService(Users(), None, passwords)
    assert asyncio.run(service.update_name("user-id", "Updated Name")).name == "Updated Name"


def test_profile_locale_update_is_persisted() -> None:
    passwords = PasswordService(); user = make_user(passwords.hash("current-password"))
    class Users:
        async def update_locale(self, _id, locale):
            return User(**{**{field: getattr(user, field) for field in user.__dataclass_fields__}, "locale": locale})
    service = ProfileService(Users(), None, passwords)
    assert asyncio.run(service.update_locale("user-id", "gu")).locale == "gu"


def test_password_change_verifies_current_password_and_revokes_sessions() -> None:
    passwords = PasswordService(); user = make_user(passwords.hash("current-password")); state = {"revoked": False, "hash": None}
    class Users:
        async def change_password(self, _id, password_hash): state["hash"] = password_hash; return user
    class Sessions:
        async def revoke_user(self, _id): state["revoked"] = True
    service = ProfileService(Users(), Sessions(), passwords)
    asyncio.run(service.change_password(user, "current-password", "new-secure-password"))
    assert state["revoked"] is True
    assert passwords.verify("new-secure-password", state["hash"])
    with pytest.raises(AuthorizationError): asyncio.run(service.change_password(user, "wrong-password", "another-password"))


def test_dashboard_service_records_exports_without_changing_source_data() -> None:
    class Repository:
        recorded = None
        async def record_download(self, *values): self.recorded = values
        async def summary(self, _user_id): return {"qr_codes": 2}
    repository = Repository(); service = DashboardService(repository)
    asyncio.run(service.record_download("user", "qr", "qr-id", "code.png", "png"))
    assert repository.recorded == ("user", "qr", "qr-id", "code.png", "png")
    assert asyncio.run(service.summary("user"))["qr_codes"] == 2
