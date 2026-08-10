import asyncio
from datetime import datetime, timezone

import pytest

from app.api.dependencies import get_current_admin
from app.core.config import Settings
from app.core.exceptions import ApplicationError, AuthorizationError
from app.core.security import PasswordService, TokenService
from app.models.user import User
from app.schemas.admin import AdminUserUpdateRequest
from app.services.admin_service import AdminService
from app.services.auth_service import AuthService


def user(identifier: str, role: str = "user", status: str = "active") -> User:
    now = datetime.now(timezone.utc)
    return User(id=identifier, name="Test User", email=f"{identifier}@example.com", password_hash="hash",
                role=role, status=status, token_version=1, created_at=now, updated_at=now)


def test_admin_dependency_rejects_regular_users() -> None:
    with pytest.raises(AuthorizationError):
        asyncio.run(get_current_admin(user("member")))
    admin = user("admin", "admin")
    assert asyncio.run(get_current_admin(admin)) is admin


def test_admin_service_revokes_sessions_and_records_audit() -> None:
    class Repository:
        audited = None

        async def find_user(self, user_id): return user(user_id)
        async def count_active_admins(self): return 1
        async def update_user(self, user_id, changes): return user(user_id, changes.get("role", "user"), changes.get("status", "active"))
        async def record_audit(self, admin_id, action, target_id, details): self.audited = (admin_id, action, target_id, details)

    class Sessions:
        revoked = None
        async def revoke_user(self, user_id): self.revoked = user_id

    repository, sessions = Repository(), Sessions()
    service = AdminService(repository, sessions)
    result = asyncio.run(service.update_user(user("admin", "admin"), "member", AdminUserUpdateRequest(status="disabled")))

    assert result.status == "disabled"
    assert sessions.revoked == "member"
    assert repository.audited == ("admin", "user.access_updated", "member", {"status": "disabled"})


def test_admin_cannot_lock_self_or_remove_last_active_admin() -> None:
    class Repository:
        async def find_user(self, user_id): return user(user_id, "admin")
        async def count_active_admins(self): return 1

    service = AdminService(Repository(), None)
    admin = user("admin", "admin")
    with pytest.raises(ApplicationError, match="own role"):
        asyncio.run(service.update_user(admin, "admin", AdminUserUpdateRequest(status="disabled")))
    with pytest.raises(ApplicationError, match="last active"):
        asyncio.run(service.update_user(admin, "second-admin", AdminUserUpdateRequest(role="user")))


def test_configured_email_bootstraps_admin_at_registration() -> None:
    class Users:
        created_role = None
        async def find_by_email(self, _email): return None
        async def create(self, name, email, password_hash, role="user", locale="en"):
            self.created_role = role
            return user("new-admin", role)

    class Sessions:
        async def create(self, **_values): return None

    settings = Settings(_env_file=None, jwt_secret="x" * 32, admin_emails=["ADMIN@example.com"])
    users = Users()
    service = AuthService(users, Sessions(), PasswordService(), TokenService(settings), settings)
    result = asyncio.run(service.register("Administrator", "admin@example.com", "strong-password"))

    assert users.created_role == "admin"
    assert result.user.role == "admin"
