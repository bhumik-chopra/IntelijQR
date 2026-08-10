from app.core.exceptions import ApplicationError, AuthorizationError, NotFoundError
from app.core.security import PasswordService
from app.models.user import User
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository


class ProfileService:
    def __init__(self, users: UserRepository, sessions: SessionRepository, passwords: PasswordService) -> None:
        self._users = users; self._sessions = sessions; self._passwords = passwords

    async def update_name(self, user_id: str, name: str) -> User:
        user = await self._users.update_name(user_id, name)
        if user is None: raise NotFoundError("User account was not found")
        return user

    async def update_locale(self, user_id: str, locale: str) -> User:
        user = await self._users.update_locale(user_id, locale)
        if user is None: raise NotFoundError("User account was not found")
        return user

    async def change_password(self, current: User, current_password: str, new_password: str) -> None:
        if not self._passwords.verify(current_password, current.password_hash):
            raise AuthorizationError("Current password is incorrect")
        if self._passwords.verify(new_password, current.password_hash):
            raise ApplicationError("New password must be different from the current password")
        user = await self._users.change_password(current.id, self._passwords.hash(new_password))
        if user is None: raise NotFoundError("User account was not found")
        await self._sessions.revoke_user(current.id)
