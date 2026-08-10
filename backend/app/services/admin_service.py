import logging

from app.core.exceptions import ApplicationError, NotFoundError
from app.models.user import User
from app.repositories.admin_repository import AdminRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.admin import AdminUserUpdateRequest


logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, repository: AdminRepository, sessions: SessionRepository) -> None:
        self._repository = repository
        self._sessions = sessions

    async def overview(self) -> dict:
        return {"stats": await self._repository.overview(), "recent_audit": await self._repository.list_audit()}

    async def list_users(self, limit: int, offset: int, search: str | None, role: str | None, status: str | None):
        return await self._repository.list_users(limit, offset, search, role, status)

    async def update_user(self, admin: User, user_id: str, request: AdminUserUpdateRequest) -> User:
        if admin.id == user_id:
            raise ApplicationError("Administrators cannot change their own role or status")
        changes = request.model_dump(exclude_unset=True)
        if not changes:
            raise ApplicationError("At least one field must be changed")
        current = await self._repository.find_user(user_id)
        if current is None:
            raise NotFoundError("User account was not found")
        removes_active_admin = current.role == "admin" and current.status == "active" and (
            changes.get("role") == "user" or changes.get("status") == "disabled"
        )
        if removes_active_admin:
            # Preserve a recoverable local administration path.
            if await self._repository.count_active_admins() <= 1:
                raise ApplicationError("The last active administrator cannot be removed")
        updated = await self._repository.update_user(user_id, changes)
        if updated is None:
            raise NotFoundError("User account was not found")
        await self._sessions.revoke_user(user_id)
        await self._repository.record_audit(admin.id, "user.access_updated", user_id, changes)
        logger.info("Administrator updated user access", extra={"admin_user_id": admin.id, "target_user_id": user_id})
        return updated
